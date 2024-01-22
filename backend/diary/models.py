import uuid

from django.db import models
from users.models import User

from apps.models import ChatRoom


class Diary(models.Model):
    JOY = 'joy'
    SAD = 'sad'
    ANGRY = 'angry'

    MOOD_CHOICES = [
        (JOY, 'Joy'),
        (SAD, 'Sad'),
        (ANGRY, 'Angry'),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, null=True)
    content = models.TextField() # 일기 내용 = 요약 내용
    img_url = models.CharField(max_length=500, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(null=True)
    mood = models.CharField(max_length=10, choices=MOOD_CHOICES)
    capture_url = models.CharField(max_length=500, null=True, blank=True)
