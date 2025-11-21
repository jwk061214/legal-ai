import os
import json
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from google import genai
from google.genai import types

# --- 설정 ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DB_PATH = "precedent_faiss_db"
EMBEDDING_MODEL = "jhgan/ko-sbert-nli"

# --- 전역 변수 (DB 캐싱) ---
_vectorstore = None
_embeddings = None

def load_vector_db():
    """로컬에 저장된 FAISS DB를 로드합니다."""
    global _vectorstore, _embeddings
    
    if _vectorstore is not None:
        return _vectorstore

    print("DEBUG: FAISS DB 로딩 중...")
    try:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        _vectorstore = FAISS.load_local(
            DB_PATH, 
            _embeddings, 
            allow_dangerous_deserialization=True # 로컬 파일 신뢰
        )
        print("DEBUG: FAISS DB 로딩 완료")
        return _vectorstore
    except Exception as e:
        print(f"❌ DB 로딩 실패: {e}")
        return None

def get_genai_client():
    if not GEMINI_API_KEY: return None
    return genai.Client(api_key=GEMINI_API_KEY)

def search_precedents(query, k=3):
    """질문과 관련된 판례 k개를 검색합니다."""
    db = load_vector_db()
    if not db:
        return []
    
    # 유사도 검색
    docs = db.similarity_search(query, k=k)
    return docs

def generate_precedent_answer(user_question):
    """
    1. 관련 판례 검색
    2. Gemini에게 판례 기반 답변 요청
    """
    # 1. 판례 검색
    relevant_docs = search_precedents(user_question)
    
    if not relevant_docs:
        return "죄송합니다. 관련 판례 데이터를 찾을 수 없거나 DB가 구축되지 않았습니다."

    # 2. 프롬프트 구성
    context_text = ""
    for i, doc in enumerate(relevant_docs):
        context_text += f"""
--- [판례 {i+1}] ---
{doc.page_content}
-------------------
"""

    prompt = f"""
    당신은 대한민국 최고의 법률 전문가 AI입니다.
    아래 제공된 [관련 판례]를 근거로 [사용자 질문]에 대해 전문적이고 명확하게 답변해주세요.

    [관련 판례]:
    {context_text}

    [사용자 질문]:
    {user_question}

    [답변 가이드]:
    1. 결론부터 명확하게(가능/불가능/위법/적법 등) 말해주세요.
    2. 답변의 근거가 되는 '판례의 사건명'이나 '판결 요지'를 구체적으로 인용하세요.
    3. 법률 용어는 일반인이 이해하기 쉽게 풀어서 설명해주세요.
    4. 제공된 판례 내용만으로 판단하기 어렵다면, "제공된 판례 정보가 부족하지만..."이라고 전제하고 일반적인 법리를 설명하세요.
    """

    # 3. Gemini 호출
    client = get_genai_client()
    if not client: return "API 키 오류"

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        return response.text, relevant_docs
    except Exception as e:
        return f"답변 생성 오류: {e}", []