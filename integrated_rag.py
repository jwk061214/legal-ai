import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 우리가 만든 모듈들
from legal_search import search_law_articles_semantically
from precedent_rag import search_precedents
from llm_service import extract_search_law_name
from deepeval_wrapper import GeminiDeepEvalLLM

# DeepEval 관련 임포트 (평가용)
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_genai_client():
    if not GEMINI_API_KEY: return None
    return genai.Client(api_key=GEMINI_API_KEY)

# --- 1. 통합 검색 및 답변 생성 ---
def generate_integrated_answer(user_question):
    """
    1. 질문 분석 -> 법령명 추출
    2. 법령 API 검색 -> 실시간 벡터 검색 -> 가장 관련 있는 조항 1개 추출
    3. 판례 DB 검색 -> 가장 관련 있는 판례 1개 추출
    4. 종합 답변 생성
    """
    client = get_genai_client()
    if not client: return "API 키 오류", [], []

    logs = []
    
    # 1-1. 법령명 추출
    logs.append("🔍 질문 분석 중...")
    search_params = extract_search_law_name(user_question)
    target_law = search_params.get("law_name", "근로기준법")
    
    # 1-2. [Source 1] 법령 검색 (API + 실시간 벡터)
    logs.append(f"📜 법령 검색: '{target_law}'에서 관련 조항 찾는 중...")
    real_law_name, articles = search_law_articles_semantically(target_law, user_question, k=1)
    
    statute_text = articles[0] if articles else "(관련 법 조항을 찾지 못했습니다.)"
    
    # 1-3. [Source 2] 판례 검색 (미리 구축된 벡터 DB)
    logs.append("⚖️ 유사 판례 검색 중...")
    precedents = search_precedents(user_question, k=1)
    
    precedent_text = precedents[0].page_content if precedents else "(관련 판례를 찾지 못했습니다.)"

    # 1-4. 통합 답변 생성
    logs.append("🤖 법령과 판례를 종합하여 답변 작성 중...")
    
    prompt = f"""
    당신은 유능한 법률 상담 AI입니다.
    사용자의 질문에 대해 [참고 법령]과 [유사 판례]를 모두 고려하여 답변해주세요.

    [사용자 질문]: {user_question}

    [참고 1: 법령 ({real_law_name})]:
    {statute_text}

    [참고 2: 판례]:
    {precedent_text}

    [작성 가이드]:
    1. 먼저 [참고 1] 법령에 근거하여 원칙적인 답변을 하세요.
    2. 그 다음 [참고 2] 판례를 인용하여 실제 적용 사례나 예외를 설명하세요.
    3. 두 정보가 부족하면 일반적인 법 상식을 덧붙여 친절하게 설명하세요.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        answer = response.text
        
        # 평가를 위해 검색된 문맥(Context)을 리스트로 반환
        retrieved_context = [statute_text, precedent_text]
        
        return answer, retrieved_context, logs
        
    except Exception as e:
        return f"답변 생성 중 오류 발생: {e}", [], logs

# --- 2. DeepEval 평가 (복구됨) ---

def evaluate_rag_response(user_question, actual_output, retrieval_context):
    """
    생성된 답변을 DeepEval을 사용하여 평가합니다.
    - Faithfulness: 답변이 검색된 문서(법령/판례)에 근거하는가? (환각 체크)
    - Answer Relevancy: 답변이 질문에 적절한가?
    """
    
    print("📊 DeepEval 평가 시작 (Gemini 사용)...")

    # 1. 심판관(Evaluator) LLM 설정
    # deepeval_wrapper.py에서 정의한 Gemini 모델 사용
    gemini_evaluator = GeminiDeepEvalLLM()

    # 2. 평가 지표 설정
    faithfulness = FaithfulnessMetric(
        threshold=0.7,
        model=gemini_evaluator,
        include_reason=True
    )
    relevancy = AnswerRelevancyMetric(
        threshold=0.7,
        model=gemini_evaluator,
        include_reason=True
    )

    # 3. 테스트 케이스 생성
    test_case = LLMTestCase(
        input=user_question,
        actual_output=actual_output,
        retrieval_context=retrieval_context
    )

    # 4. 평가 실행
    faithfulness.measure(test_case)
    relevancy.measure(test_case)

    return {
        "faithfulness": {
            "score": faithfulness.score,
            "reason": faithfulness.reason,
            "pass": faithfulness.is_successful()
        },
        "relevancy": {
            "score": relevancy.score,
            "reason": relevancy.reason,
            "pass": relevancy.is_successful()
        }
    }

# ==========================================
# 🧪 테스트 코드
# ==========================================
if __name__ == "__main__":
    print("--- 하이브리드 RAG 및 평가 테스트 ---")
    q = "알바하다 다쳤는데 산재 처리 되나요?"
    print(f"질문: {q}\n")
    
    # 1. 답변 생성
    answer, context, logs = generate_integrated_answer(q)
    
    print("\n[진행 로그]")
    for log in logs:
        print(log)
        
    print("\n[최종 답변]")
    print(answer)
    
    print("\n[평가 시작]")
    # 2. 평가 실행
    try:
        eval_result = evaluate_rag_response(q, answer, context)
        print(f"Faithfulness Score: {eval_result['faithfulness']['score']}")
        print(f"Relevancy Score: {eval_result['relevancy']['score']}")
    except Exception as e:
        print(f"평가 중 오류: {e}")