from django.db import models
from django.conf import settings
from django.core.files.storage import default_storage  # default_storage는 settings.py의 DEFAULT_FILE_STORAGE 사용


class ChatLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.TextField(default = '제목없음', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
class ChatMessage(models.Model):
    chatlog = models.ForeignKey(ChatLog, on_delete=models.CASCADE)
    sender = models.CharField(max_length=100)
    message = models.TextField()
    translated = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # audio_path = models.FilePathField(path='/media/', recursive=True, null=True)
    audio_path = models.FileField(
        upload_to='chat_audio/%Y/%m/%d/',
        blank=True,
        null=True,
        storage=default_storage  # S3 저장소 사용
    )
    
    def __str__(self):
        return self.message
    
    
class Feedback(models.Model):
    chatmessage = models.OneToOneField(ChatMessage, on_delete=models.CASCADE)
    accuracy = models.FloatField()
    accuracy_detail = models.FloatField()
    feedback = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    