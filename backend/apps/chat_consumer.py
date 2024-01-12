import json
import os
import random
import time

import openai
from channels.generic.websocket import WebsocketConsumer
from dotenv import load_dotenv
from .models import *
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


class ChatConsumer(WebsocketConsumer):
    # 클라이언트와 연결
    def connect(self):
        self.accept()
        # 대화 기록을 저장할 리스트
        self.conversation = []

    def disconnect(self, closed_code):
        # ChatRoom 모델에서 현재 사용자의 ID에 해당하는 데이터를 가져옴
        try:
            chatroom = ChatRoom.objects.get(chatroom_id=closed_code)
        except ChatRoom.DoesNotExist:
            # 해당 ChatRoom이 존재하지 않는 경우, 함수를 종료합니다.
            return

        # 연결된 ChatRoom과 관련된 GPTQuestion과 UserAnswer를 모두 삭제
        GPTQuestion.objects.filter(chatroom=chatroom).delete()
        UserAnswer.objects.filter(question__chatroom=chatroom).delete()

        # 마지막으로 ChatRoom 자체를 삭제합니다.
        chatroom.delete()

    # 질문과 대화 저장
    def add_question_answer(self, question, answer=None):
        self.conversation.append(
            {
                "role": "assistant",
                "content": question
            }
        )
        if answer is not None:
            self.conversation.append(
                {
                    "role": "user",
                    "content": "'" + answer + "'" + " is my answer, and you give me a one question.You will talk to the child. Your purpose is to find out what the child is thinking."
                }
            )
        else:
            self.conversation.append(
                {
                    "role": "user",
                    "content": "Another question, give me only one."
                }
            )

    def continue_conversation(self, form_object):
        messages = ""
        for chunk in openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=self.conversation,
                temperature=0.9,
                stream=True,
        ):
            finish_reason = chunk.choices[0].finish_reason
            if chunk.choices[0].finish_reason == "stop":
                self.send(json.dumps({"message": "", "finish_reason": finish_reason}))
                break

            message = chunk.choices[0].delta["content"]

            messages += message
            # 메시지를 클라이언트로 바로 전송
            self.send(json.dumps({"message": message, "finish_reason": finish_reason}))
        print(self.conversation)
        GPTQuestion.objects.create(content=messages, form_id=form_object)


    def default_conversation(self, chatroom, question_content):
        messages = ""
        # question_content의 index와 원소를 순차적으로 반환하여 스트리밍 형식으로 출력
        for index, chunk in enumerate(question_content):
            is_last_char = "incomplete"
            # 현재 글자가 마지막 글자인지 확인
            if index == len(question_content) - 1:
                is_last_char = "stop"

            # 메시지를 클라이언트로 바로 전송
            self.send(json.dumps({"message": chunk, "finish_reason": is_last_char}))

            # 마지막 글자에 도달하면 루프 종료
            if is_last_char == "stop":
                break

            messages += chunk
            time.sleep(0.05)

        # GPTQuestion 객체를 생성하고 데이터베이스에 저장
        GPTQuestion.objects.create(content=messages, chatroom=chatroom)

    def pick_random_question(self, username):
        pick_question = []
        while True:
            basic_questions_list = [
                "오늘 뭐했어?",
                "오늘 기분은 어때?",
                "오늘 가장 재미있었던 일은 뭐야?",
                "오늘 하루 잘 지냈어?",
                "안녕, 반가워 또 보네?",
                "본인의 직업관은 무엇인가요?",
                "안녕 , {username}아 오늘 날씨 어땠어?",
                "안녕 {username}아 뭐하다가 이제왔어? 기다렸잖아!!",
                "안녕, 00아 보고싶었어. 너는 어땠어?",
                "안녕, 오늘도 재밌게 놀 준비됐어? 목소리 크게!!!!",
                "오늘 힘든 일은 없었어?",
                "오늘 뭐하고 놀았어?",
                "오늘 친구들이랑 뭐하고 놀았어?",
                "오늘 하루 어땠어?",
                "Hi? 영어로 안녕이라는 뜻이야!",
                "오늘 입은 옷 예쁘네~ 좋은일 있었어?",
            ]

            question = random.choice(basic_questions_list)

            if question in pick_question:
                continue
            pick_question.append(question)
            break

        return question

    def situation_tuning(self, username, age, gender):
        self.conversation = [
            {
                "role": "system",
                "content": 'My name is '+username+' and My age is '+age+' and My gender is ' + gender + 'and you will talk to the child. Your purpose is to find out what the child is thinking. Continue the conversation with only soft and easy words like talking to the child. Please ask questions by referring to age, name, and gender. Just ask me one question unconditionally. And we will talk in Korean.'
            },
        ]