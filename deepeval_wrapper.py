import os
from deepeval.models import GeminiModel
from dotenv import load_dotenv

load_dotenv()

class GeminiDeepEvalLLM(GeminiModel):
    """
    DeepEval의 공식 GeminiModel을 사용하여 평가를 수행하는 클래스입니다.
    환경 변수에서 API 키를 자동으로 로드하도록 설정합니다.
    """
    def __init__(self, model_name="gemini-2.5-flash", **kwargs):
        # .env에서 API 키 로드
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")
        
        # 부모 클래스(GeminiModel) 초기화
        # 공식 모델은 내부적으로 google-generativeai 라이브러리를 사용하여 통신합니다.
        super().__init__(model_name=model_name, api_key=api_key, **kwargs)

    def load_model(self):
        """
        DeepEval 내부 로직과의 호환성을 위해 필요한 메서드입니다.
        공식 모델은 이미 self.model 등을 가지고 있으므로, 
        필요한 경우 부모의 load_model을 호출하거나 그대로 둡니다.
        """
        return super().load_model()