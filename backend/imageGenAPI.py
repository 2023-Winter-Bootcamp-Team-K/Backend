
import re
import time
import httpx
import random
import asyncio
import requests

from enum import Enum
import os

BING_URL = "https://www.bing.com"

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "max-age=0",
    "content-type": "application/x-www-form-urlencoded",
    "referrer": f"{BING_URL}/images/create/",
    "origin": BING_URL,
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.63",
    "x-forwarded-for": f"13.{random.randint(104, 107)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
}
# BING_URL 및 HEADERS 변수가 선언되어, Bing의 이미지 생성 API에 접근하는데 사용되는 코드.

class Error(Enum):
    ERROR_TIMEOUT = "Your request has timed out."
    ERROR_BLOCKED_PROMPT = (
        "Your prompt has been blocked. Try to change any bad words and try again."
    )
    ERROR_BEING_REVIEWED_PROMPT = "Your prompt is being reviewed. Try to change any sensitive words and try again."
    ERROR_NO_RESULTS = "Could not get results"
    ERROR_UNSUPPORTED_LANG = "This language is currently not supported"
    ERROR_NO_IMAGES = "No images"
    ERROR_MANY_REQUESTS = "Can't submit any more prompts. Please wait until your other ongoing creations are complete."
    EERROR_PROBLEM_CREATING_IMAGES = "There was a problem creating your images."
    ERROR_UNKNOWN = "Unknown error"


class ImageGenAPI:
    TIMEOUT = 128

    def __init__(self,auth_cookie: str):
        self.session = httpx.AsyncClient(headers=HEADERS, cookies={"_U": auth_cookie}) #session ID가져오는듯?

    async def get_images(self, prompt):
        start_time = time.time()

        url_encoded_prompt = requests.utils.quote(prompt) #요약내용이 들어가는 곳

        response = await self.session.post(
            f"{BING_URL}/images/create?q={url_encoded_prompt}&rt=3&FORM=GENCRE",  # &rt=4
            follow_redirects=False,
            data=f"q={url_encoded_prompt}&qs=ds",
        )

        if response.status_code == 302:
            redirect_url = response.headers.get("Location", None)

            if redirect_url is not None:
                redirect_url = redirect_url.replace("&nfy=1", "")
                await self.session.get(f"{BING_URL}{redirect_url}")
                polling_url = f"{BING_URL}/images/create/async/results/{redirect_url.split('id=')[-1]}?q={url_encoded_prompt}"
            else:
                raise Exception("redirect_url not found")

            timeout_start = time.time()

            while True:
                response = await self.session.get(polling_url)

                if response.status_code != 200:
                    raise Exception(Error.ERROR_NO_RESULTS.value)
                elif time.time() - timeout_start > self.TIMEOUT:
                    raise Exception(Error.ERROR_TIMEOUT.value)
                elif not response.text or "errorMessage" in response.text:
                    if "errorMessage" in response.text:
                        print("has errorMessage")
                    await asyncio.sleep(1)
                else:
                    break

            image_links = re.findall(r'src="([^"]+)"', response.text)

            if len(image_links) == 0:
                raise Exception(Error.ERROR_NO_IMAGES.value)

            normal_image_links = [link.split("?w=")[0] for link in image_links]

            processing_time = time.time() - start_time

            return normal_image_links, processing_time
        else:
            res_message = response.text.lower()

            if "can't submit any more prompts" in res_message:
                raise Exception(Error.ERROR_MANY_REQUESTS.value)
            elif "this prompt has been blocked" in res_message:
                raise Exception(Error.ERROR_BLOCKED_PROMPT.value)
            elif "this prompt is being reviewed" in res_message:
                raise Exception(Error.ERROR_BEING_REVIEWED_PROMPT.value)
            elif "problem creating your images" in res_message:
                raise Exception(Error.EERROR_PROBLEM_CREATING_IMAGES.value)
            else:
                raise Exception(Error.ERROR_UNKNOWN.value)


async def test(prompt):
    result = await image_generator.get_images(prompt)
    print(result)


if __name__ == "__main__":
    prompt = "여우 분홍색 지브리 개 기타 도서관"

    image_generator = ImageGenAPI(
        os.getenv("BING_SESSION_ID")
    )  # .env 에 추가, BING_SESSION_ID

    asyncio.run(test(prompt))

    # 웹 쿠키 얻기 cookieStore.get("_U").then(result => console.log(result.value))