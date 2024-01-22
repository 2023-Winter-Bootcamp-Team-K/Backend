import os
import sys
import urllib.request
from dotenv import load_dotenv

def text_to_speach(text):
    load_dotenv()
    client_id = os.getenv("CLOVA_TTS_ID")
    client_secret = os.getenv("CLOVA_TTS_SECRET")
    encText = urllib.parse.quote(text)
    # 음성으로 변환할 텍스트와 음색, 속도, 감정 등 변경
    data = "speaker=vdain&volume=0&speed=0&emotion=1&pitch=0&format=mp3&text=" + encText;
    url = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
    request = urllib.request.Request(url)
    request.add_header("X-NCP-APIGW-API-KEY-ID", client_id)
    request.add_header("X-NCP-APIGW-API-KEY", client_secret)
    response = urllib.request.urlopen(request, data=data.encode('utf-8'))
    rescode = response.getcode()
    if (rescode == 200):
        print("TTS mp3 저장")
        response_body = response.read()
        return response_body
    else:
        print("Error Code:" + rescode)