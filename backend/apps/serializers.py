<<<<<<< HEAD
# serializers.py

from rest_framework import serializers
from .models import ChatRoom

class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ['user_id']
=======
from rest_framework import serializers
from .models import GPTQuestion, UserAnswer

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPTQuestion
        fields = ['id', 'content']

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ['id', 'question', 'content']
>>>>>>> develop
