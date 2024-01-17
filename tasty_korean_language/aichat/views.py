# aichat/views.py
import json
import logging
from threading import Thread
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.db import models
from django.conf import settings
from .models import ChatLog, ChatMessage, Feedback
from .STT import etri_eval, compare, hug_stt_acc
from .utils import ApiClientManager, FileHandler, AIChatProcessor

logger = logging.getLogger(__name__)

#region [Language & Translation Handlers] --------------------------------------
def translate(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            translated = AIChatProcessor.translate_message(
                data['message'], 
                data.get('target_lang', 'ko')
            )
            return JsonResponse({'translated_message': translated})
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return HttpResponseBadRequest("Translation failed")
    return JsonResponse({'error': 'Invalid request'}, status=400)

def update_language(request):
    if request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            request.user.language = data['language']
            request.user.save()
            return JsonResponse({'message': 'Language updated successfully!'})
        except KeyError:
            return JsonResponse({'error': 'Missing language parameter'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)
#endregion ---------------------------------------------------------------------

#region [Chat Session Management] ----------------------------------------------
@login_required
def chatsetting(request):
    chatlog_list = ChatLog.objects.filter(user=request.user).order_by("-created_at")
    return render(request, 'aichat/chat_setting.html', {'chatloglist': chatlog_list})

@login_required
def index(request):
    if request.method == 'POST':
        title = request.POST.get('title', '')[:100]
        chatlog = ChatLog.objects.create(user=request.user, title=title or '제목없음')
        
        # 비동기 초기 메시지 생성
        Thread(target=create_initial_chat_session, args=(chatlog, request.user)).start()
        
        return redirect('aichat:chatlog', chatlog.id)
    return render(request, 'aichat/chat_setting.html')

def create_initial_chat_session(chatlog, user):
    """비동기 초기 채팅 세션 생성"""
    try:
        initial_message = AIChatProcessor.generate_gpt_response("말하기 쉬운 주제로 얘기하자", 'ko')
        translated = AIChatProcessor.translate_message(initial_message, user.language)
        
        ChatMessage.objects.create(
            chatlog=chatlog,
            sender="system",
            message=initial_message,
            translated=translated
        )
    except Exception as e:
        logger.error(f"Initial message error: {str(e)}")
#endregion ---------------------------------------------------------------------

#region [Chat Interaction Handlers] --------------------------------------------
@login_required
def index2(request, id):
    try:
        chatlog = ChatLog.objects.prefetch_related('chatmessage_set').get(
            id=id, 
            user=request.user
        )
        messages = chatlog.chatmessage_set.select_related('feedback').all()
        feedback_list = [
            AIChatProcessor.process_feedback(msg.feedback) 
            if hasattr(msg, 'feedback') else [] 
            for msg in messages
        ]
        return render(request, 'aichat/chat.html', {
            'messages': zip(messages, feedback_list), 
            'id': id
        })
    except ChatLog.DoesNotExist:
        return HttpResponseBadRequest("Invalid chat log")

@login_required
def send(request, id):
    try:
        chatlog = ChatLog.objects.get(id=id, user=request.user)
        audio_file = request.FILES['audio_file']
        correct_message = request.POST.get('message', '')
        
        # 비동기 메시지 처리
        Thread(target=process_user_message, args=(
            chatlog, 
            audio_file, 
            correct_message, 
            request.user
        )).start()
        
        return redirect('aichat:chatlog', id)
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        return HttpResponseBadRequest("Message processing failed")

def process_user_message(chatlog, audio_file, correct_message, user):
    """사용자 메시지 처리 파이프라인"""
    try:
        # 1. 파일 처리
        webm_path = FileHandler.save_audio_file(user, audio_file)
        wav_path = FileHandler.convert_audio_format(webm_path)
        
        # 2. 음성 인식 처리
        stt_result, hug_acc = hug_stt_acc(correct_message, str(wav_path))
        
        # 3. 사용자 메시지 저장
        user_msg = ChatMessage.objects.create(
            chatlog=chatlog,
            sender=user.username,
            message=stt_result,
            audio_path=f"/media/{wav_path.relative_to(settings.MEDIA_ROOT)}"
        )
        
        # 4. 발음 평가
        etri_score = etri_eval(correct_message, str(wav_path), settings.ETRI_API_KEY)
        compare_result = ", ".join(sum(compare(correct_message, stt_result), []))
        Feedback.objects.create(
            chatmessage=user_msg,
            accuracy_detail=hug_acc,
            accuracy=etri_score,
            feedback=compare_result,
            answer=correct_message
        )
        
        # 5. AI 응답 생성
        gpt_response = AIChatProcessor.generate_gpt_response(correct_message, user.language)
        translated = AIChatProcessor.translate_message(gpt_response, user.language)
        
        ChatMessage.objects.create(
            chatlog=chatlog,
            sender="system",
            message=gpt_response,
            translated=translated
        )
        
    except Exception as e:
        logger.error(f"Message processing error: {str(e)}")
#endregion ---------------------------------------------------------------------

#region [Chat History Views] ---------------------------------------------------
class ChatLogListView(ListView):
    model = ChatLog
    template_name = 'aichat/chatlog_list.html'
    context_object_name = 'chatlog_list'
    paginate_by = 10

    def get_queryset(self):
        return ChatLog.objects.filter(user=self.request.user).prefetch_related(
            'chatmessage_set'
        ).annotate(
            first_message=models.Min('chatmessage__created_at')
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_chats'] = self.get_queryset().count()
        return context
#endregion ---------------------------------------------------------------------