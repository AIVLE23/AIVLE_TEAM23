from django.shortcuts import render, redirect, resolve_url
from django.views.generic import ListView
from django.http import JsonResponse

from django.contrib.auth.decorators import login_required

from .models import *

from openai import OpenAI

from django.conf import settings

from google.cloud import speech

from django.conf import settings
from django.core.files.storage import default_storage

import urllib3
import json
import base64
import librosa
import numpy as np


from pydub import AudioSegment

import os

from google.cloud import translate_v2
from .STT import etri_eval, compare, hug_stt_acc, etri_stt


##################Lanugae 설정 Update##################

def translate(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        message = request.POST.get('message')
        target_language = 'ko'  # 대상 언어 설정

        # 번역 수행
        translation_client = translate_v2.Client.from_service_account_json("C:\\Users\\user\\Desktop\\chat.json")
        translated_message = translation_client.translate(message, target_language=target_language)['translatedText']
        
        return JsonResponse({'translated_message': translated_message})
    else:
        return JsonResponse({'error': '잘못된 요청'}, status=400)

def update_language(request):
    if request.method == 'PATCH':
        data = json.loads(request.body)
        language = data.get('language')
        request.user.language = language
        request.user.save()
        return JsonResponse({'message': 'Language updated successfully!'})

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


@login_required
def chatsetting(request):
    chatloglist = ChatLog.objects.filter(user=request.user).order_by("-created_at")
    
    return render(request, 'aichat/chat_setting.html', {'chatloglist': chatloglist})


#####################aichat#####################

@login_required
def index(request):
    if request.method == 'POST':
        title = request.POST['title']
        if (title != ''):
            chatlog = ChatLog.objects.create(user=request.user, title=title)
        else:
            chatlog = ChatLog.objects.create(user=request.user)
        
        initial_gpt_message = get_chat_gpt_response("말하기 쉬운 주제로 얘기하자", 'ko')
    
        translation_client = translate_v2.Client.from_service_account_json("C:\\Users\\user\\Desktop\\chat.json")
        trans_initial_gpt_message = translation_client.translate(initial_gpt_message, target_language=request.user.language)['translatedText']
        # 초기 메시지를 GPT에 전달
        ChatMessage.objects.create(chatlog=chatlog, sender="system", message=initial_gpt_message, translated=trans_initial_gpt_message)
        
        return redirect('aichat:chatlog', chatlog.id)
    

@login_required
def index2(request, id):
    userchatlog = ChatLog.objects.get(id=id)
    
    messages_with_feedback = ChatMessage.objects.filter(chatlog=userchatlog).select_related('feedback').all()
    
    
    # Feedback 단어쌍 처리
    feedback_list = []
    for message in messages_with_feedback:
        if hasattr(message, 'feedback'):
            feedback_message = message.feedback.feedback
            if feedback_message:
                feedback = feedback_message.split(', ')
                feedback = list(zip(feedback[::2], feedback[1::2]))
            else:
                feedback = []
            feedback_list.append(feedback)
        else:
            feedback_list.append([])
        
    return render(request, 'aichat/chat.html', {'messages': zip(messages_with_feedback, feedback_list), 'id': id})

@login_required
def send(request, id):
    
    correct_message = request.POST.get('message')
    sender = request.user.username
    chatlog = ChatLog.objects.get(id=id)
    audio_file = request.FILES['audio_file']    # audio_file = request.FILES.get('audio_file')
    
    print(id)
    print(request.user)
    print(request.POST)
    print(request.FILES)
    print(correct_message)
    
    #POST로 받은 오디오 파일 webm으로 저장
    last_chatmessage_id = ChatMessage.objects.last().id
    last_chatmessage_id += 1
    default_storage.save(sender+'/' + str(last_chatmessage_id) + '.webm', audio_file)    # file_path = default_storage.save(sender+'/' + ' ' + '.mp3', audio_file)

    #webm 오디오 파일 받아서 wav로 변환 후 saveFilePath에 저장
    audioFilePath = ".\\media\\" + sender + "\\" + str(last_chatmessage_id) + ".webm"
    # make dir
    current_path = os.getcwd()
    if not os.path.exists(current_path + "\\media\\" + sender + "_transformed"):
        os.mkdir(current_path + "\\media\\" + sender + "_transformed")
    saveFilePath = ".\\media\\" + sender + "_transformed" + "\\" + str(last_chatmessage_id) + ".wav"
    webm = AudioSegment.from_file(audioFilePath, format="webm")
    webm.export(saveFilePath, format="wav")
    # DB에 추가될 오디오 파일 경로
    audio_path = "/media/" + sender + "_transformed" + "/" + str(last_chatmessage_id) + ".wav"
    
    #STT 적용
    STT_result, hug_acc = hug_stt_acc(correct_message, saveFilePath)    
    # stt_message = run_stt(audio_file)
    
    #ChatMessage objects 생성
    ChatMessage.objects.create(chatlog=chatlog, sender=sender, message=STT_result, audio_path=audio_path) # ChatMessage.objects.create(chatlog=chatlog, sender=sender, message=STT_result)    # userchatmessage = ChatMessage.objects.create(chatlog=chatlog, sender=sender, message=stt_message)
    
    #발음평가 모델 적용
    key = settings.ETRI_API_KEY
    etri_score = etri_eval(correct_message,saveFilePath,key)    # accurcy, feedback = get_pronunciation_feedback(correct_message, saveFilePath)
    
    #Feedback 틀린 단어 생성
    compare_lt = compare(correct_message, STT_result)
    to_compare_lt_str = ", ".join(sum(compare_lt, []))
    
    #Feedback objects 생성
    Feedback.objects.create(chatmessage=ChatMessage.objects.last(), accuracy_detail = hug_acc, accuracy=etri_score, feedback=to_compare_lt_str, answer=correct_message)      # detail_acc, accurcy, feedback = get_pronunciation_feedback(correct_message, audio_file, sender,last_chatmessage_id)
    
    #GPT 답변 생성
    # chat_gpt_response = get_chat_gpt_response(correct_message, request.user.language)
    chat_gpt_response = get_chat_gpt_response(correct_message, 'ko')
    
    #ChatMessage objects 생성
    
    ###################################################################################################################
    user_language = request.user.language if request.user.language else 'en'
    translation_client = translate_v2.Client.from_service_account_json("C:\\Users\\user\\Desktop\\chat.json")
    translated_message = translation_client.translate(chat_gpt_response, target_language=user_language)['translatedText']
    ChatMessage.objects.create(chatlog=chatlog, sender="system", message=chat_gpt_response, translated=translated_message)
    ###################################################################################################################
    
    return redirect('aichat:chatlog', id)
    
#####################함수#####################

def run_stt(audio_file):
    client = speech.SpeechClient()
    
    audio = speech.RecognitionAudio(content=audio_file.read())
    
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=36000,
        language_code="ko-KR",
    )
    
    response = client.recognize(config=config, audio=audio)
    
    for result in response.results:
        print("Transcript: {}".format(result.alternatives[0].transcript))
    
    return response.results[0].alternatives[0].transcript
     
     
def get_chat_gpt_response(message, lang):
    
    client = OpenAI(api_key=settings.CHATGPT_API_KEY)
    
    message = f"{message} (Language: {lang})"

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": """당신은 다정하고 친절하며 조용한 사람입니다.
                                             먼저, 구체적인 주제를 선정하여 이야기를 나누어 보세요.
                                             상대방이 어떤 주제에 관해 이야기하든 친절하게 대답해야 합니다.
                                             가능하다면 이어지는 주제에 대해 계속 이야기를 나누되, 상대방의 대답으로 대화가 이어지지 않는다면 먼저 새로운 주제를 제안해보세요.
                                             무조건 2문장 안으로 말하고 간결하게 20단어 이내로 말하세요.
                                             짧고 간결하게 작성하세요.
                                             무조건 질문 하나만 하세요.
                                             항상 한국어로 대답하세요."""},
            {"role": "user", "content": message}
        ]
    )
    
    response = completion.choices[0].message.content
    
    return response




#####################chatlog list#####################

class ChatLogListView(ListView):
    model = ChatLog
    template_name = 'aichat/chatlog_list.html'
    context_object_name = 'chatlog_list'

    def get_queryset(self):
        # Fetch all ChatLogs with their first ChatMessage
        return ChatLog.objects.prefetch_related('chatmessage_set').annotate(first_message=models.Min('chatmessage__created_at'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data if needed
        return context

