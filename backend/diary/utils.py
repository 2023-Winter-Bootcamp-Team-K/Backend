import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# gpt한테 요약 요청
def generate_summary(content):
    content_str = "\n".join(content)
    summary_request = (
        'From now on, you will write child\'s diary instead of child. The content of diary must be the summarize of the conversation you had, with the child and write it as a diary. And the conditions of the diary are '
        '1.It must be at least 160 characters and no more than 180 characters. '
        '2. Each sentence in the diary should end with "~했다" or "~했어." '
        '4.The child is of South Korean nationality. '
        '5.Do not include a greeting in the summary. '
        '6.The last sentence of the diary is "오늘의 일기 끝!".'
        'Please follow these conditions when making a diary.'
        )
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
        max_tokens=220,
    )
    return response.choices[0].message.content
# 달리 이미지 생성 로직보
# def generate_image(summary):
#
#     response = client.images.generate(
#         model="dall-e-3",
#         prompt=f'{summary}'
#                f'From now on, you will be drawing illustrations to be included in a child\'s picture diary.'
#                f'You should follow the following instructions :'
#                f'I would like to recreate an image I previously generated using seed number "3129831613". '
#                f'The image should maintain the same style and characteristics as the one produced with the given seed number.'
#                f'1.Draw the illustration based on the summary provided. '
#                f'2.Create an illustration that suits a child\'s picture diary.'
#                f'3.If there are human illustrations, color the skin in #fdece2.'
#                f'4.You never include any text in the illustration.'
#                f'Remember, you should follow these instructions',
#         size="1024x1024",
#         quality="standard",
#         n=1,
#         style="natural",
#     )
#     image_url = response.data[0].url
#     return image_url
