# -*- coding: utf-8 -*-
"""
이 모듈은 Google Gemini API를 사용하기 위한 클라이언트 클래스를 제공합니다.
Gemini 모델을 호출하여 텍스트, 이미지 생성 및 멀티모달 입력을 처리하는 기능을 포함합니다.
"""
import os
import time
import mimetypes
import base64

from google import genai
from google.genai import types
from dotenv import load_dotenv

import vertexai


def encode_image_to_base64(file_path: str) -> str:
    """로컬 이미지 파일을 Base64로 인코딩하는 함수"""
    try:
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        print(f"오류: 파일 '{file_path}'을(를) 찾을 수 없습니다.")
        return None


def load_image_bytes(file_path: str) -> bytes:
    """로컬 이미지 파일을 읽어 원본 바이트를 반환하는 함수"""
    try:
        with open(file_path, "rb") as image_file:
            return image_file.read()
    except FileNotFoundError:
        print(f"오류: 파일 '{file_path}'을(를) 찾을 수 없습니다.")
        return None


class Gemini:
    """
    Google Gemini API를 사용하기 위한 래퍼 클래스입니다.
    API 호출 시 재시도 로직을 포함하여 안정적인 통신을 지원합니다.
    """

    def __init__(self):
        """
        Gemini 클래스의 인스턴스를 초기화합니다.
        .env 파일에서 환경 변수를 로드하고 Vertex AI와 Gemini 클라이언트를 설정합니다.
        """
        # .env 파일로부터 환경 변수 로드
        load_dotenv()
        # Vertex AI 초기화
        vertexai.init(project=os.getenv('PROJECT_ID'), location=os.getenv('LOCATION'))
        self.api_key = os.getenv('API_KEY')

        # Gemini 클라이언트 초기화
        self.client = genai.Client(api_key=self.api_key)

        # 사용할 Gemini 모델 설정
        self.model_text = "gemini-2.0-flash"  # 텍스트 기반 모델                                                                                                                                    │
        self.model_image = "gemini-2.5-flash-image-preview"  # 이미지 및 멀티모달 모델

        # API 호출 실패 시 재시도 설정
        self.max_retries = 3  # 최대 재시도 횟수
        self.initial_delay = 1  # 초기 대기 시간 (초)


    def retry_with_delay(func):
        """
        API 호출 실패 시 지수 백오프를 사용하여 재시도하는 데코레이터입니다.
        """
        def wrapper(self, *args, **kwargs):
            delay = self.initial_delay
            for attempt in range(self.max_retries):
                try:
                    # 함수 실행
                    return func(self, *args, **kwargs)
                except Exception as e:
                    # 마지막 시도인 경우 예외 발생
                    if attempt == self.max_retries - 1:
                        raise e
                    # 재시도 전 에러 메시지 출력 및 대기
                    print(f"gemini 호출 {attempt + 1}번째 실패: {e}")
                    time.sleep(delay)
                    # 대기 시간을 2배로 증가
                    delay *= 2
        return wrapper

    @retry_with_delay
    def call_gemini_image_text(self, prompt, image, response_type="application/json", model=None):
        """
        이미지와 텍스트를 입력으로 받아 Gemini 멀티모달 모델을 호출합니다.

        Args:
            prompt (str): 모델에 전달할 기본 프롬프트
            image (bytes): 입력 이미지 데이터
            response_type (str, optional): 응답 MIME 타입. Defaults to "application/json".
            model (str, optional): 사용할 모델 이름. Defaults to self.model_image.

        Returns:
            str: 모델이 생성한 텍스트 응답
        """
        # 이미지 파일을 Gemini 서버에 업로드
        target_image = self.client.files.upload(file=image)
        # Gemini 모델에 콘텐츠 생성 요청
        response = self.client.models.generate_content(
            model=model if model else self.model_text,
            contents=[
                prompt,
                target_image,
            ],
            config={
                "response_mime_type": response_type,
                "temperature": 0,
                "top_p": 1,
                "top_k": 1,
            }
        )
        return response.candidates[0].content.parts[0].text

    @retry_with_delay
    def call_gemini_text(self, prompt, response_type="application/json", model=None):
        """
        텍스트를 입력으로 받아 Gemini 텍스트 모델을 호출합니다.

        Args:
            prompt (str): 모델에 전달할 프롬프트
            response_type (str, optional): 응답 MIME 타입. Defaults to "application/json".
            model (str, optional): 사용할 모델 이름. Defaults to self.model_text.

        Returns:
            str: 모델이 생성한 텍스트 응답
        """
        response = self.client.models.generate_content(
            model=model if model else self.model_text,
            contents=[prompt],
            config={
                "response_mime_type": response_type,
            }
        )
        return response.candidates[0].content.parts[0].text


    def generate_creative_prompt(self, user_prompt):
        """
        사용자 입력을 기반으로 창의적인 프롬프트를 생성합니다.

        Args:
            user_prompt (str): 사용자가 입력한 프롬프트

        Returns:
            str: 모델이 생성한 창의적인 프롬프트
        """
        prompt = f"""다음은 사용자가 입력한 이미지 생성 프롬프트입니다: '{user_prompt}'. 이 프롬프트를 더 창의적이고 상세하게 만들어주세요. 이미지 생성에 가장 적합한 형태로, 영어로 작성해주세요."""
        return self.call_gemini_text(prompt)

    @retry_with_delay
    def call_image_generator(self, prompt, image_files):
        """
        프롬프트와 여러 이미지 파일을 기반으로 새로운 이미지와 텍스트를 생성합니다.

        Args:
            prompt (str): 이미지 생성을 위한 텍스트 프롬프트
            image_files (list): 입력으로 사용할 이미지 파일 경로 리스트

        Returns:
            tuple: (생성된 이미지 데이터 리스트, 생성된 텍스트 응답)
        """
        # 프롬프트와 이미지 파트들을 준비
        parts = [types.Part.from_text(text=prompt)]

        if image_files:
            for image_file in image_files:
                if not os.path.exists(image_file):
                    print(f"오류: 입력 이미지 파일을 찾을 수 없습니다. 경로를 확인해주세요: {image_file}")
                    continue

                # 입력 이미지 로드
                try:
                    with open(image_file, "rb") as f:
                        image_data = f.read()
                    mime_type, _ = mimetypes.guess_type(image_file)
                    if not mime_type:
                        mime_type = 'application/octet-stream'  # 기본값 설정
                    parts.append(types.Part.from_bytes(data=image_data, mime_type=mime_type))
                except Exception as e:
                    print(f"이미지 파일 로딩 중 오류 발생: {e}")
                    return [], ""

        # 모델에게 전달할 콘텐츠 프롬프트 구성
        contents = [
            types.Content(
                role="user",
                parts=parts,
            ),
        ]

        # 이미지 및 텍스트 생성을 위한 설정
        generate_config = types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            temperature=0,
            top_p=1,
            top_k=1,
            # 안전 설정: 모든 카테고리에 대해 차단 안함
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
            ]
        )

        image_parts = []
        full_text_response = ""

        # 스트리밍 방식으로 콘텐츠 생성 요청
        response_stream = self.client.models.generate_content_stream(
            model=self.model_image,
            contents=contents,
            config=generate_config,
        )
        # 스트림 응답 처리
        for chunk in response_stream:
            if not (chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts):
                continue

            for part in chunk.candidates[0].content.parts:
                if part.inline_data:
                    # 이미지 데이터 추가
                    image_parts.append(part.inline_data)
                elif part.text:
                    # 텍스트 데이터 추가
                    full_text_response += part.text

        return image_parts, full_text_response