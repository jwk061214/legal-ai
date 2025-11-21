import requests
import os
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
# --- 설정 ---
load_dotenv()
MOLEG_API_KEY = os.getenv("MOLEG_API_KEY")
EMBEDDING_MODEL = "jhgan/ko-sbert-nli" # 한국어 임베딩 모델

def search_law_id(law_name):
    """
    법령 이름으로 검색하여 '법령ID'를 반환합니다. (예: 001747 -> 1747)
    """
    SEARCH_URL = f"http://www.law.go.kr/DRF/lawSearch.do?OC={MOLEG_API_KEY}&target=eflaw&query={law_name}&type=xml"
    print(SEARCH_URL)
    try:
        response = requests.get(SEARCH_URL, timeout=5)
        if response.status_code == 200:
            try:
                root = ET.fromstring(response.content)
            except ET.ParseError:
                return None, None
            
            laws = root.findall("law")
            if not laws:
                return None, None

            target_law = None
            query_clean = law_name.replace(" ", "").strip()
            
            # 1단계: 완전 일치
            for law in laws:
                name_node = law.find("법령명한글")
                if name_node is not None and name_node.text:
                    if name_node.text.replace(" ", "").strip() == query_clean:
                        target_law = law
                        break
            
            # 2단계: 부분 일치 (가장 짧은 이름)
            if not target_law:
                candidates = []
                for law in laws:
                    name_node = law.find("법령명한글")
                    if name_node is not None and name_node.text and query_clean in name_node.text.replace(" ", ""):
                        candidates.append(law)
                if candidates:
                    candidates.sort(key=lambda x: len(x.find("법령명한글").text))
                    target_law = candidates[0]

            if not target_law:
                target_law = laws[0]

            raw_id = target_law.find("법령ID").text
            law_name_res = target_law.find("법령명한글").text
            
            # ID 포맷팅 (앞의 0 제거)
            if raw_id.isdigit():
                processed_id = str(int(raw_id))
            else:
                processed_id = raw_id
            
            print(f"DEBUG: 법령 ID 추출 - {law_name_res} ({processed_id})")
            return processed_id, law_name_res
            
    except Exception as e:
        print(f"법령 검색 오류: {e}")
    
    return None, None

def get_law_content_xml(law_id):
    """법령ID로 XML 본문을 조회합니다."""
    DETAIL_URL = f"http://www.law.go.kr/DRF/lawService.do?OC={MOLEG_API_KEY}&target=eflaw&ID={law_id}&type=xml"
    print(DETAIL_URL)

    try:
        response = requests.get(DETAIL_URL, timeout=10)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        print(f"법령 본문 조회 오류: {e}")
    return None

def parse_articles_from_xml(xml_content):
    """
    [Robust Parsing]
    구조를 엄격하게 따지는 대신, '조문단위' 내의 모든 텍스트를 순서대로 긁어옵니다.
    태그 이름을 보고 적절한 들여쓰기만 추가합니다.
    """
    if not xml_content: return []

    try:
        root = ET.fromstring(xml_content)
        articles_text_list = []

        # <조문> 섹션 찾기
        jomon_section = root.find("조문")
        if jomon_section is None:
            return []
        
        # 각 <조문단위> 순회
        for unit in jomon_section.findall("조문단위"):
            # 조문여부가 '조문'인 것만 처리 (부칙 등 제외)
            type_node = unit.find("조문여부")
            if type_node is not None and type_node.text != "조문":
                continue

            text_buffer = []
            
            # ⭐️ 핵심: .iter()를 사용하여 깊이에 상관없이 모든 하위 태그를 순서대로 방문
            for elem in unit.iter():
                # 텍스트가 없으면 스킵
                if not elem.text or not elem.text.strip():
                    continue
                
                tag = elem.tag
                text = elem.text.strip()
                
                # 태그에 따른 포맷팅 (들여쓰기 및 줄바꿈)
                if tag == "조문내용":
                    # 조문 제목은 맨 앞에 (줄바꿈 없음)
                    text_buffer.append(text)
                
                elif tag == "항번호":
                    # 항 번호 (①) : 줄바꿈 후 들여쓰기 2칸
                    text_buffer.append(f"\n  {text}")
                elif tag == "항내용":
                    # 항 내용 : 번호 뒤에 붙임 (공백 1칸)
                    text_buffer.append(f" {text}")
                
                elif tag == "호번호":
                    # 호 번호 (1.) : 줄바꿈 후 들여쓰기 4칸
                    text_buffer.append(f"\n    {text}")
                elif tag == "호내용":
                    text_buffer.append(f" {text}")
                
                elif tag == "목번호":
                    # 목 번호 (가.) : 줄바꿈 후 들여쓰기 6칸
                    text_buffer.append(f"\n      {text}")
                elif tag == "목내용":
                    text_buffer.append(f" {text}")
            
            # 버퍼를 하나의 문자열로 합치기
            full_article = "".join(text_buffer).strip()
            
            if full_article:
                articles_text_list.append(full_article)

        print(f"DEBUG: 총 {len(articles_text_list)}개의 조문을 추출했습니다.")
        return articles_text_list[:100] # 상위 100개

    except Exception as e:
        print(f"XML 파싱 오류: {e}")
        return []

# 🆕 --- 실시간 벡터 검색 함수 ---
def search_law_articles_semantically(law_name, user_question, k=2):
    """
    1. API로 법령 전문을 가져옵니다.
    2. 메모리에 임시 Vector DB를 만듭니다.
    3. 사용자 질문과 의미적으로 가장 유사한 조항 k개를 찾습니다.
    """
    # 1. 법령 검색 및 본문 파싱
    law_id, real_name = search_law_id(law_name)
    if not law_id:
        return None, []
    
    xml_content = get_law_content_xml(law_id)
    articles = parse_articles_from_xml(xml_content)
    
    if not articles:
        return real_name, []

    print(f"DEBUG: '{real_name}' 조항 {len(articles)}개 실시간 벡터화 시작...")

    # 2. 실시간 벡터 DB 생성 (In-Memory)
    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        # 문자열 리스트를 Document 객체 리스트로 변환
        docs = [Document(page_content=art, metadata={"source": real_name}) for art in articles]
        
        # FAISS 인덱스 생성 (매우 빠름)
        vectorstore = FAISS.from_documents(docs, embeddings)
        
        # 3. 의미 검색 수행
        results = vectorstore.similarity_search(user_question, k=k)
        
        # 결과 텍스트만 추출
        final_articles = [doc.page_content for doc in results]
        print(f"DEBUG: 벡터 검색 완료. 상위 {k}개 조항 추출.")
        
        return real_name, final_articles

    except Exception as e:
        print(f"❌ 벡터화 중 오류 발생: {e}")
        # 오류 시 그냥 앞부분 반환
        return real_name, articles[:k]

# ==========================================
# 🧪 테스트 코드
# ==========================================
if __name__ == "__main__":
    print("--- [실시간 벡터 RAG] 법령 검색 테스트 ---")
    question = "자동차 튜닝 승인 절차가 어떻게 돼?"
    target_law = "자동차관리법"
    
    print(f"질문: {question}")
    print(f"대상 법령: {target_law}")
    
    name, arts = search_law_articles_semantically(target_law, question, k=1)
    
    if name:
        print(f"\n✅ 검색된 법령: {name}")
        if arts:
            print(f"\n✅ AI가 선택한 가장 관련 있는 조항:\n{'-'*30}\n{arts[0]}\n{'-'*30}")
        else:
            print("⚠️ 조항을 찾지 못했습니다.")
    else:
        print("❌ 법령 검색 실패")