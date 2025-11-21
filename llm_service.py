import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_genai_client():
    if not GEMINI_API_KEY: return None
    return genai.Client(api_key=GEMINI_API_KEY)

def call_gemini_api(prompt, temperature=0.3):
    # (기존 코드 동일)
    client = get_genai_client()
    if not client: return "API 키 오류"
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=temperature)
        )
        return response.text.strip() if response.text else "응답 없음"
    except Exception as e:
        return f"오류: {str(e)}"

# --- 🆕 1. 검색어 추출 함수 (법령명만 추출) ---
def extract_search_law_name(user_question: str) -> dict:
    """
    사용자 질문을 분석하여 검색할 '법령 이름' 1개만 추출합니다.
    """
    client = get_genai_client()
    
    prompt = f"""
    당신은 법률 검색 에이전트입니다. 
    사용자의 질문에 답하기 위해 찾아야 할 가장 적절한 한국의 '법령 이름' 1개를 추출해주세요.
    
    [사용자 질문]: {user_question}

    [응답 형식 (JSON)]:
    {{
        "law_name": "법령명 (예: 근로기준법, 형법, 민법, 자동차관리법)"
    }}
    
    주의: 약어가 아닌 정식 명칭을 추론하세요. (예: 알바 -> 근로기준법)
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"법령명 추출 실패: {e}")
        return {"law_name": "근로기준법"} # 기본값

# --- 🆕 2. 법률 상담 답변 생성 함수 ---
def generate_legal_answer(user_question, law_name, articles):
    """
    찾아낸 법 조항들을 바탕으로 사용자 질문에 답변합니다.
    """
    client = get_genai_client()
    
    # 조항이 너무 많을 경우를 대비해 텍스트 길이 제한
    articles_text = "\n\n".join(articles)
    
    prompt = f"""
    당신은 유능한 법률 상담 AI입니다.
    아래 [관련 법 조항]을 근거로 [사용자 질문]에 대해 친절하고 명확하게 답변해주세요.

    [참고 법령: {law_name}]
    {articles_text}

    [사용자 질문]:
    {user_question}

    [답변 가이드]:
    1. 결론부터 명확하게 말해주세요.
    2. 근거가 되는 법 조항을 인용하여 설명해주세요.
    3. 법률 용어가 있다면 쉽게 풀어서 설명해주세요.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"답변 생성 실패: {e}"

# ============================================================
#  기능 B: 쉬운 법률 해석 (계약서/판례 풀이)
# ============================================================

def create_easy_legal_interpretation(original_text: str, term_definitions: dict) -> dict:
    """
    복잡한 법률 텍스트와 용어 정의를 입력받아,
    1. 용어 정의를 쉽게 요약하고
    2. 본문을 쉽게 해석하여 JSON으로 반환합니다.
    """
    client = get_genai_client()
    if not client:
        return {
            "main_interpretation": "API 키가 설정되지 않았습니다.",
            "simplified_terms": {}
        }

    print("Gemini API (Single Call) 서비스 호출 시작...")
    
    # 1. 프롬프트에 넣을 용어 정의 목록 생성
    terms_context = ""
    if term_definitions:
        for term, data in term_definitions.items():
            terms_context += f"- {term}: {data['korean_original']}\n"
    else:
        terms_context = "(참고할 용어 정의 없음)"

    # 2. 통합 프롬프트 작성 (JSON 출력을 강제함)
    prompt = f"""
    당신은 법률 문서를 초등학생도 이해할 수 있게 설명해주는 친절한 변호사입니다.
    아래 제공된 [원본 텍스트]와 [법률 용어 목록]을 바탕으로 다음 두 가지 작업을 수행해주세요.

    [작업 1] '쉬운 용어 사전' 만들기:
    제공된 [법률 용어 목록]에 있는 각 용어의 뜻을 초등학생도 알 수 있게 '한 문장'으로 아주 쉽게 요약하세요.

    [작업 2] '본문 해석' 하기:
    [원본 텍스트]의 내용을 문단별로 나누어, 위에서 만든 쉬운 용어들을 활용해 아주 쉽고 명확하게 풀어서 설명해주세요.

    🚨 [중요 제약 사항] 🚨
    - **(굵게), ##(제목) 등의 마크다운 문법을 절대 사용하지 마세요.**
    - 오직 순수한 텍스트(Plain Text)로만 작성하세요.
    - 문단 사이에는 줄바꿈(\\n)만 사용하세요.
    - 친절하고 부드러운 말투(~해요, ~입니다)를 사용하세요.

    --------------------------------------------------------
    [법률 용어 목록 (원본 정의)]:
    {terms_context}

    [원본 텍스트]:
    {original_text}
    --------------------------------------------------------

    [응답 형식 (JSON)]:
    {{
        "simplified_terms": {{
            "용어1": "쉬운 요약 1",
            "용어2": "쉬운 요약 2"
        }},
        "main_interpretation": "여기에 마크다운 없는 순수 텍스트로 해석을 적어주세요."
    }}
    """

    try:
        # 3. Gemini API 호출 (JSON 모드 사용)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json" # JSON 응답 강제
            )
        )
        
        if response.text:
            result_data = json.loads(response.text)
            print("Gemini 응답 및 파싱 완료.")
            
            return {
                "main_interpretation": result_data.get("main_interpretation", "해석 생성 실패"),
                "simplified_terms": result_data.get("simplified_terms", {})
            }
        else:
            return {
                "main_interpretation": "AI가 빈 응답을 반환했습니다.",
                "simplified_terms": {}
            }
            
    except Exception as e:
        print(f"Gemini API 호출 오류: {e}")
        return {
            "main_interpretation": f"오류가 발생했습니다: {str(e)}",
            "simplified_terms": {}
        }