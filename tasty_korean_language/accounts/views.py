from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from .forms import SignupForm
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth.decorators import login_required

# from aichat.models import ChatLog, ChatMessage
from aichat.models import *
from community.models import Post


def signupConsent(request):
    return render(request, 'registration/signup_consent.html')

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(settings.LOGIN_URL)            
    else:
        form = SignupForm()

    return render(request, 'registration/signup.html',{'form':form})


def findID(request):
    if request.method == 'POST':
        User = get_user_model()
        email = request.POST.get('email', None)
        if email:
            try:
                user = User.objects.get(email=email)
                return JsonResponse({'result': user.username})
            except User.DoesNotExist:
                return JsonResponse({'result': 'User not found'})
    return JsonResponse({}, status=400)


# Cookie Test 
def cookie_test(request, code):
    response = render(request, 'registration/cookieTest.html')
    if code == 'add':
        response.set_cookie('model', 'A001')
        response.set_cookie('prod', 'EV9')
    elif code == 'get' :
        model = request.COOKIES.get('model')
        prod = request.COOKIES.get('prod')
        print(model, prod)
    elif code == 'del' :
        response.delete_cookie('model')
        response.delete_cookie('prod')
    return response
        

from django.contrib.sessions.backends.db import SessionStore

# Session Test
def session_test(request, code):
    response = render(request, 'registration/sessionTest.html')
    session = request.session
    if code == 1:
        user = request.user        
        print(user,':', session)
    elif code == 2 :        
        session['model'] = 'A001'
        session['prod'] = 'EV9'
        print('session 데이터 등록')
    elif code == 3:
        model = session.get('model')
        prod = session.get('prod')
        print('session 데이터 추출')
        print(model, prod)
    elif code == 4:
        session.pop('model')
        print('session 데이터 삭제')
        session.pop('prod')
    return response    


###################### mypage ######################
@login_required
def mypage(request):
    user = request.user
    chatlog_list = ChatLog.objects.filter(user=user).select_related('user').prefetch_related('chatmessage_set')[:10]
    post_list = Post.objects.filter(writer=user).select_related('writer').only('title', 'create_date')[:5]
    
    context = {
        'chatlog_list': chatlog_list,
        'post_list': post_list,
        'total_chats': ChatLog.objects.filter(user=user).count()
    }
    return render(request, 'registration/mypage.html', context)