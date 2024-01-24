import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# gpt한테 요약 요청
def generate_summary(content):
    content_str = "\n".join(content)
    summary_request = ('You have to write a picture diary based on the conversation. It\'s going to be in your child\'s picture diary. Please write 180 characters or less. And you only speak in Korean')
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": summary_request
            },
            {
                "role": "user",
                "content": content_str
            },
        ],
    )
    return response.choices[0].message.content
# 달리 이미지 생성 로직보
def generate_image(summary):

    response = client.images.generate(
        model="dall-e-3",
        prompt="너무 즐거운 날이었다! 아침에 아빠와 산책을 하고 나무 위에서 동물들을 봤어요. 점심에는 공원에서 친구들과 피크닉도 했어요! 행복한 하루였어요! 🌳🌻🐿️🌳🍎 #즐거운하루 #피크닉 #동물들 #산책 #행복한아이 #사진일기. 이 내용을 바탕으로 아이가 그린 것 처럼 이미지 만들어줘 글을 넣지 말아줘.",
        # prompt=f"{summary}. 이거를 아이가 그린 그림일기 처럼 만들어줘",
        size="1024x1024",
        quality="standard",
        n=1,
        style="natural",
    )
    image_url = response.data[0].url
    return image_url
