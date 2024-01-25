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
        'From now on, you will write child\'s diary instead of child. The content of diary must be the summarize of the conversation you had, with the child and write it as a diary. And the conditions of the diary are 1.It must be at least 160 characters and no more than 180 characters. 2.The sentences in the diary should end with "~했다" or "~했어." 3.Write in the handwriting style of a child aged 7 to 10 years. 4.The child is of South Korean nationality. 5.Do not include a greeting in the summary. Please follow these conditions when making a diary.')
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
        prompt=f'{summary}. Please create an illustration based on the following summary: This summary summarizes the conversation between you and the baby.Additionally I would like to recreate an image I previously generated using seed number 3129831613. The image should maintain the same style and characteristics as the one produced with the given seed number. While satisfying these conditions  Generate a cute and lovely image that is suitable for a child\'s picture diary. And thier ages are 4 ~ 6. If there are people in the drawing, please depict them with a light apricot-colored skin tone (#fdece2) and draw black or dark brown hair. The most important thing is do not include any texts in image. ',
        size="1024x1024",
        quality="standard",
        n=1,
        style="natural",
    )
    image_url = response.data[0].url
    return image_url
