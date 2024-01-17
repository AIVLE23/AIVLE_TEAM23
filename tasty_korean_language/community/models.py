from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.conf import settings

# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=40, default = '')
    contents = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True)
    like_count = models.PositiveIntegerField(default=0) # 양수입력 필드
    # writer은 다른 모델을 참조하겠다.(User) 외래키 추가
    writer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default = '') # on_delete : User가 delete 될 때 게시글을 어떻게 설정한 것인지에 대해 설정 1. 게시글 같이 지우기(CASCADE) 2. 없는 값으로 해서 게시글은 남겨두기

    def get_absolute_url(self):
        return reverse('community:detail', args=[self.id])
    
    

class Reply(models.Model):
    """
        reply: Reply -> Board 연결관계
        comment: 댓글내용
        rep_date: 작성일
    """
    reply = models.ForeignKey(Post, on_delete=models.CASCADE)
    comment = models.CharField(max_length=200)
    rep_date = models.DateTimeField()

    def __str__(self):
        return self.comment
    
