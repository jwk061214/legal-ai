import os
from datasets import load_dataset
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import time

# --- 설정 ---
EMBEDDING_MODEL = "jhgan/ko-sbert-nli"
DB_PATH = "precedent_faiss_db"
DATASET_ID = "joonhok-exo-ai/korean_law_open_data_precedents"
SAMPLE_SIZE = 1000 

def build_vector_db():
    print(f"📥 1. 데이터셋 다운로드 중... ({DATASET_ID})")
    try:
        dataset = load_dataset(DATASET_ID, split="train")
        
        print(f"   - 전체 데이터 개수: {len(dataset)}개")
        # (참고용) 실제 컬럼 확인
        print(f"   - 데이터셋 컬럼: {dataset.column_names}") 
        
        # 샘플링
        if SAMPLE_SIZE and len(dataset) > SAMPLE_SIZE:
            dataset = dataset.select(range(SAMPLE_SIZE))
            print(f"   - (테스트용) 상위 {SAMPLE_SIZE}개만 사용합니다.")
            
    except Exception as e:
        print(f"❌ 데이터셋 로드 실패: {e}")
        return

    print("\n🔄 2. 데이터 전처리 및 문서 변환 중...")
    documents = []
    
    for item in dataset:
        # ⭐️ [핵심 수정] 컬럼명 하드코딩 ⭐️
        # 이미지에서 확인된 컬럼: '전문', '판결요지', '판시사항'
        
        content = item.get('전문', '')   # 본문
        summary = item.get('판결요지', '') # 요약
        note = item.get('판시사항', '')    # 판시사항 (제목 대용으로 쓸 수 있음)
        
        # 사건명/번호는 데이터셋에 있다면 가져오고, 없으면 '정보 없음' 처리
        case_name = item.get('사건명', '사건명 정보 없음')
        case_number = item.get('사건번호', '번호 정보 없음')

        # 본문 내용이 없거나 너무 짧으면 스킵 (데이터 품질 관리)
        if not content or len(str(content)) < 10: 
            continue

        # 검색에 사용될 텍스트 구성 (LLM이 읽을 내용)
        page_content = f"""
[사건명] {case_name}
[사건번호] {case_number}

[판시사항]
{note}

[판결요지]
{summary}

[전문 내용]
{content[:2000]}... (이하 생략)
"""
        # 메타데이터 저장 (출처 및 필터링용)
        metadata = {
            "case_name": case_name,
            "case_number": case_number,
            "source": "판례 데이터셋"
        }
        
        documents.append(Document(page_content=page_content, metadata=metadata))

    if not documents:
        print("❌ 생성된 문서가 0개입니다! '전문' 컬럼이 비어있는지 확인해주세요.")
        return

    print(f"   - 변환된 문서 개수: {len(documents)}개")

    print(f"\n🧮 3. 임베딩 및 벡터 DB 생성 중... (모델: {EMBEDDING_MODEL})")
    try:
        start_time = time.time()
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        
        # FAISS 인덱스 생성
        vectorstore = FAISS.from_documents(documents, embeddings)
        
        # 로컬에 저장
        vectorstore.save_local(DB_PATH)
        
        end_time = time.time()
        print(f"✅ 4. DB 저장 완료! (소요 시간: {end_time - start_time:.2f}초)")
        print(f"   - 저장 경로: ./{DB_PATH}")
        
    except Exception as e:
        print(f"❌ 벡터 DB 생성 실패: {e}")

if __name__ == "__main__":
    build_vector_db()