import json
import os
import random
import time
import base64


from django.core.files.base import ContentFile
from django.http import JsonResponse
from openai import OpenAI
from channels.generic.websocket import WebsocketConsumer
from dotenv import load_dotenv
import asyncio

from tts import text_to_speach
from .models import *
from .tasks import speech_to_text_task,upload_audio_to_s3_task
import logging
from users.models import User
from django.utils import timezone



load_dotenv()

OPENAI_API_KEY=os.getenv('OPENAI_API_KEY')
client=OpenAI(api_key=OPENAI_API_KEY)
logger = logging.getLogger(__name__)

class ChatConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_room_id = None
        self.chatroom = None
        self.present_question = None
        self.user = None
        self.endTime = 10
        # 대화 기록을 저장할 리스트
        self.conversation = []
        self.default_audio_file_urls = []
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 클라이언트와 연결
    def connect(self, text_data=None):
        # JSON 문자열을 파이썬 객체로 변환
        if text_data is not None:
            json.loads(text_data)
        self.chat_room_id = self.scope["url_route"]["kwargs"]["roomid"]
        self.accept()

        # chatroom를 찾아서 chatroom 오브젝트 생성
        self.chatroom = ChatRoom.objects.get(id=self.chat_room_id)
        # user 찾기
        self.user = User.objects.get(id=self.chatroom.user_id)
        self.username = self.user.username

        # 연결 완료 전송 (프론트에 기분 화면 활성화)
        self.send(
            text_data=json.dumps(
                {
                    "event": "connected",
                    "data": {
                        "message": "연결 됐습니다.",
                        "roomId": self.chat_room_id,
                    }
                }
            )
        )

        # 첫 질문 선택
        question_content = self.pick_random_question(self.user.username)  # username을 매개변수로 전달합니다.


        # 종료 메세지 보내기
        # loop = asyncio.get_event_loop()
        # asyncio.create_task(self.send_end_message())
    def receive(self, text_data):
        if text_data:
            res = json.loads(text_data)
            event = res.get("event")
            data = res.get("data")
            logger.info(res)
            # 1. 첫 대화 시작
            if event == "conversation_start":
                # 기분 room에 추가
                mood = data.get("mood")
                if mood == None:
                    self.send(
                        text_data=json.dumps(
                            {
                                "event": "error",
                                "data": "기분이 정상적으로 넘어오지 않았습니다.",
                            }
                        )
                    )
                # 기분 저장
                self.chatroom.add_mood(mood)
                self.situation_tuning(self.user, mood=mood)
                # 첫 질문 선택
                question_content = self.pick_random_question(self.username)
                # 질문 text 전송
                self.default_conversation(self.chatroom, question_content)
                # 질문 음성 파일 전송(mp3)
                self.audio_send(question_content)

                self.add_answer(answer=None)
                self.add_question(question=question_content)

            # 2. 음성 대답
            elif event == "user_answer":
                print(self.present_question.id)
                # base64 디코딩
                audio_blob = data["audioBlob"]
                audio_data = base64.b64decode(audio_blob)


                # 오디오 파일로 변환
                audio_file = ContentFile(audio_data)

                # 오디오 파일을 바이너리 데이터로 변환
                binary_audio_data = audio_file.read()

                # 비동기 태스크 실행
                upload_task = upload_audio_to_s3_task.delay(binary_audio_data)

                # 비동기 작업 실행
                task = speech_to_text_task.delay(audio_data)
                # 작업 완료 후 콜백 함수 연결
                task.then(self.on_task_completion(task,upload_task))

            elif event == "conversation_end":
                self.send(json.dumps({"message": "", "finish_reason": ""}))
                self.close()

    def disconnect(self, closed_code):
        # self.chatroom.delete_at = timezone.now()
        # self.chatroom.save()
        pass

    def save_gpt_question(self, content):
        # GPT 질문 저장
        question = GPTQuestion.objects.create(chatroom_id=self.chatroom, content=content)
        question.save()
        # 현재 질문 설정
        self.present_question = question

    def save_user_answer(self, question, content, url):
        # 사용자 답변 저장
        answer = UserAnswer.objects.create(question_id=question, content=content, audio_url=url)
        answer.save()

    def add_question(self, question):
        self.conversation.append(
            {
                "role": "assistant",
                "content": question
            }
        )

    def add_answer(self, answer=None):
        if answer is not None:
            self.conversation.append(
                {
                    "role": "user",
                    "content": "'" + answer + "'" + " is my answer, and you give me a one question."
                                "You will talk to the 10 to 13 years of child. "
                                "The purpose of our conversation is to find out how the child spent their day and what emotions they experienced."
                                "You should offer a follow-up question that aligns with the context of the child's response. "
                                "Additionally, you should express ample empathy in response to the child's answers. "
                                "Remember, you can only ask one question at a time."
                }
            )
        else:
            self.conversation.append(
                {
                    "role": "user",
                    "content": "Another question, give me only one."
                }
            )

    def continue_conversation(self, chatroom):
        messages = ""

        for chunk in self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.conversation,
                temperature=0.9,
                stream=True,
        ):
            finish_reason = chunk.choices[0].finish_reason
            response_message = chunk.choices[0].delta.content
            # 메시지 조각를 클라이언트로 바로 전송
            #self.send(json.dumps({"event": "conversation",
            #                      "data": {"message": response_message, "finish_reason": finish_reason}}))
            self.gpt_text_send(response_message, finish_reason)
            if finish_reason == "stop":
                break

            # 메시지 조각 합침
            messages += response_message

        self.save_gpt_question(content=messages)
        return messages

    def child_conversation(self, content):
        messages = ""
        for index, chunk in enumerate(content):
            is_last_char = "incomplete"
            # 현재 글자가 마지막 글자인지 확인
            if index == len(content) - 1:
                is_last_char = "stop"

            # 메시지를 클라이언트로 바로 전송
            self.user_text_send(chunk, is_last_char)
            # 마지막 글자에 도달하면 루프 종료
            if is_last_char == "stop":
                break

            messages += chunk
            time.sleep(0.05)

    def default_conversation(self, chatroom, question_content):
        messages = ""
        # question_content의 index와 원소를 순차적으로 반환하여 스트리밍 형식으로 출력
        for index, chunk in enumerate(question_content):
            is_last_char = "incomplete"
            # 현재 글자가 마지막 글자인지 확인
            if index == len(question_content) - 1:
                is_last_char = "stop"

            # 메시지를 클라이언트로 바로 전송
            self.gpt_text_send(chunk, is_last_char)
            # 마지막 글자에 도달하면 루프 종료
            if is_last_char == "stop":
                break

            messages += chunk
            time.sleep(0.05)
        # GPTQuestion 객체를 생성하고 데이터베이스에 저장
        question = GPTQuestion.objects.create(content=messages, chatroom_id=chatroom)
        question.save()
        self.present_question = question


    def child_conversation(self, content):
        messages = ""
        for index, chunk in enumerate(content):
            is_last_char = "incomplete"
            # 현재 글자가 마지막 글자인지 확인
            if index == len(content) - 1:
                is_last_char = "stop"

            # 메시지를 클라이언트로 바로 전송
            self.user_text_send(chunk, is_last_char)
            # 마지막 글자에 도달하면 루프 종료
            if is_last_char == "stop":
                break

            messages += chunk
            time.sleep(0.05)


    def pick_random_question(self, username):
        pick_question = []
        user_name = username[1:]
        while True:
            basic_questions_list = [
                "오늘 뭐했어?",
                "오늘 기분은 어때?",
                "오늘 가장 재미있었던 일은 뭐야?",
                "오늘 하루 잘 지냈어?",
                "안녕, 반가워 또 보네?",
                f"안녕 , {user_name}아 오늘 날씨 어땠어?",
                f"안녕 {user_name}아 뭐하다가 이제왔어? 기다렸잖아!!",
                f"안녕, {user_name}아 보고싶었어. 너는 어땠어?",
                "안녕, 오늘도 재밌게 놀 준비됐어? 목소리 크게!!!!",
                "오늘 힘든 일은 없었어?",
                "오늘 뭐하고 놀았어?",
                "오늘 친구들이랑 뭐하고 놀았어?",
                "오늘 하루 어땠어?",
                "Hi? 영어로 안녕이라는 뜻이야!",
                f"{user_name}이 오늘 입은 옷 예쁘다! 좋은일 있었어?",
            ]

            question = random.choice(basic_questions_list)

            if question in pick_question:
                continue
            pick_question.append(question)
            break

        return question

    def situation_tuning(self, user, mood):
        self.conversation = [
            {
                "role": "system",
                "content": 'My name is ' + user.username + ' and My age is ' + str(user.age) + ' and My gender is ' + user.gender + 'and My mood is ' + mood + '.'
                           'With these conditions, from now on, you will have a conversation with a child. '
                            'The child is Korean and age is between  10 to 13. '
                            'The purpose of your conversation with a child is to find out how child spent child\'s day and how child\'s felt. '
                            'You should ask him simple, clear questions, and use a soft, friendly tone.'
                             "You should offer a follow-up question that aligns with the context of the child's response."
                             "Additionally, you should express ample empathy in response to the child's answers."
                             "Remember, you can only ask one question at a time."
            },
        ]

    def audio_send(self, text):
        # TTS blob 객체 생성
        tts_audio_data = text_to_speach(text)
        tts_audio_string = base64.b64encode(tts_audio_data).decode('utf-8')
        # TTS blob 전송
        self.send(json.dumps({
            "event": "question_tts",
            "data": {
                "audioBlob": tts_audio_string
            }
        }
        ))


    def text_send(self, message, finish_reason):
        if finish_reason is None:
            finish_reason = "incomplete"
        self.send(json.dumps({"event": "conversation",
                              "data": {"message": message, "finish_reason": finish_reason}}))

    def gpt_text_send(self, message,finish_reason):
        if finish_reason is None:
            finish_reason = "incomplete"
        self.send(json.dumps({"event": "conversation",
                              "data": {"character": "quokka", "message": message, "finish_reason": finish_reason}}))

    def user_text_send(self, message,finish_reason):
        if finish_reason is None:
            finish_reason = "incomplete"
        self.send(json.dumps({"event": "conversation",
                              "data": {"character": "child", "message": message, "finish_reason": finish_reason}}))

    def end_conversation(self):
        # 대화 요약 생성
        summary = self.generate_summary(self.conversation)

        # DALL-E 이미지 생성
        image_url = self.generate_image(summary)

        # 클라이언트에 결과 전송
        self.send(json.dumps({
            "event": "chat_end",
            "summary": summary,
            "image_url": image_url
        }))

    # # gpt한테 요약 요청
    # def generate_summary(self, content):
    #     content_str = "\n".join(content)
    #     summary_request = ('You have to write a picture diary based on the conversation. It\'s going to be in your child\'s picture diary. Please write 180 characters or less. And you only speak in Korean')
    #     response = client.chat.completions.create(
    #         model="gpt-3.5-turbo",
    #         messages=[
    #             {
    #                 "role": "system",
    #                 "content": summary_request
    #             },
    #             {
    #                 "role": "user",
    #                 "content": content_str
    #             },
    #         ],
    #     )
    #     return response.choices[0].message.content
    # # 달리 이미지 생성 로직보
    # def generate_image(self, summary):
    #
    #     response = client.images.generate(
    #         model="dall-e-3",
    #         prompt=summary,
    #         size="1024x1024",
    #         quality="standard",
    #         n=1,
    #         style="natural",
    #     )
    #     image_url = response.data[0].url
    #     return image_url

    def on_task_completion(self, result, audio_file_url):
        text_result = result.get(timeout=10)  # 결과를 기다림
        self.child_conversation(text_result)
        self.add_answer(text_result)
        self.save_user_answer(question=self.present_question, content=text_result, url=audio_file_url)
        # STT 결과를 기반으로 후속 처리 진행
        question = self.continue_conversation(self.chatroom)  # 실패지점 !

        self.audio_send(question)
        self.add_question(question=question)

