from dotenv import load_dotenv
import streamlit as st

# 📚 1. 법률 용어 사전 모듈
from legal_dict import extract_and_define_terms

# 📜 2. 법령 검색 모듈
from legal_search import search_law_articles_semantically

# 🤖 3. AI 서비스 모듈 (Gemini)
from llm_service import (
    create_easy_legal_interpretation, 
    extract_search_law_name, 
    generate_legal_answer
)

# ⚖️ 4. 판례 RAG 모듈
from precedent_rag import generate_precedent_answer 

# 🔍 5. 통합 하이브리드 & 평가 모듈
from integrated_rag import generate_integrated_answer, evaluate_rag_response

# 환경 변수 로드
load_dotenv()

# --- Streamlit 페이지 설정 ---
st.set_page_config(
    page_title="⚖️ Legal AI Helper", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚖️ Legal AI Helper")
st.markdown("---")

# 탭 구성 (4개 기능)
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 쉬운 법률 해석", 
    "🤖 법령 상담", 
    "⚖️ 판례 상담", 
    "🔍 하이브리드 상담 (평가)"
])

# ============================================================
# [탭 1] 쉬운 법률 해석 (Terminology & Interpretation)
# ============================================================
with tab1:
    st.header("어려운 법률 텍스트 해석기")
    st.write("계약서나 판례 텍스트를 붙여넣으면, 법률 용어를 분석하고 쉽게 풀어드립니다.")
    
    sample_text = "제7조 (계약의 해제)\n① 매도인 또는 매수인이 본 계약상의 채무불이행을 하였을 경우, 그 상대방은 서면으로 이행을 최고하고 계약을 해제할 수 있다."
    original_text = st.text_area("법률 텍스트 입력:", value=sample_text, height=200, key="tab1_area")

    if st.button("해석하기", type="primary", key="tab1_btn"):
        if not original_text:
            st.warning("텍스트를 입력해주세요.")
        else:
            with st.spinner("1단계: 법률 용어 분석... (법제처 API 호출 중)"):
                term_definitions = extract_and_define_terms(original_text)

            with st.spinner("2단계: AI가 용어 정의를 쉽게 풀고, 본문을 해석 중입니다... (Gemini 호출 중)"):
                llm_result = create_easy_legal_interpretation(original_text, term_definitions)
                
                # 결과 파싱
                easy_interpretation = llm_result.get("main_interpretation", "해석을 생성하지 못했습니다.")
                simplified_terms = llm_result.get("simplified_terms", {})

                # 결과 출력
                st.success("해석이 완료되었습니다!")
                st.text_area("상세 해석 내용", value=easy_interpretation, height=300)

                if term_definitions:
                    st.subheader(" ")
                    with st.expander("💡 AI가 참고한 법률 용어 보기"):
                        for term, data in term_definitions.items():
                            st.markdown(f"#### {term}")
                            easy_def = simplified_terms.get(term, "쉬운 해석 없음")
                            st.info(f"**쉬운 정의:** {easy_def}")
                            if data['english'] != "N/A":
                                st.caption(f"English: {data['english']}")
                            st.divider()

# ============================================================
# [탭 2] 법령 기반 상담 (Rule-based Agent)
# ============================================================
with tab2:
    st.header("AI 법률 상담 (근거 법령 검색)")
    st.write("질문을 입력하면 **가장 관련 있는 법령(법제처)**을 찾아 답변해 드립니다.")
    
    user_question_law = st.text_input("질문을 입력하세요", placeholder="예: 알바하다 다쳤는데 산재 처리 가능한가요?", key="tab2_input")
    
    if st.button("상담 받기", type="primary", key="tab2_btn"):
        if not user_question_law:
            st.warning("질문을 입력해주세요.")
        else:
             # 1. 검색어 추출 및 법령 검색
             with st.status("1. 질문 분석 및 법령 검색 중...") as status:
                search_params = extract_search_law_name(user_question_law)
                target_law = search_params.get("law_name", "근로기준법")
                st.write(f"🔍 감지된 법령: **{target_law}**")
                
                status.update(label="2. 법령 본문 가져오는 중...", state="running")
                real_law_name, articles = search_law_articles_semantically(target_law)
                
                if not articles:
                    st.error(f"'{target_law}' 정보를 가져오지 못했습니다.")
                    status.update(label="검색 실패", state="error")
                else:
                    st.write(f"📚 **{real_law_name}**에서 조항 정보를 가져왔습니다.")
                    with st.expander("참고한 법 조항 보기"):
                        for art in articles:
                            st.text(art)
                            st.markdown("---")
                    status.update(label="검색 완료!", state="complete")
            
             # 2. 답변 생성
             if articles:
                with st.spinner("3. 최종 답변 작성 중..."):
                    answer = generate_legal_answer(user_question_law, real_law_name, articles)
                
                st.divider()
                st.subheader("🤖 AI 상담 결과")
                st.markdown(answer)

# ============================================================
# [탭 3] 판례 기반 상담 (Precedent RAG)
# ============================================================
with tab3:
    st.header("실전 판례 검색 상담")
    st.write("유사한 **과거 판례(Precedents)**를 검색하여 법적 판단을 예측해 봅니다.")
    
    if st.button("DB 상태 확인", key="check_db"):
        try:
            import os
            if os.path.exists("precedent_faiss_db"):
                st.success("✅ 판례 DB가 준비되어 있습니다.")
            else:
                st.error("❌ 판례 DB가 없습니다. 터미널에서 `python build_precedent_db.py`를 실행해주세요.")
        except:
            pass

    user_question_case = st.text_input("상황을 구체적으로 설명해주세요", placeholder="예: 술을 마시고 전동 킥보드를 타다가 걸렸는데 면허 취소가 되나요?", key="tab3_input")

    if st.button("판례 검색 및 상담", type="primary", key="tab3_btn"):
        if not user_question_case:
            st.warning("질문을 입력해주세요.")
        else:
            with st.spinner("관련된 판례를 찾아 분석 중입니다... (Vector DB 검색)"):
                # RAG 함수 호출
                answer, docs = generate_precedent_answer(user_question_case)
                
                st.subheader("⚖️ 판례 기반 분석 결과")
                st.markdown(answer)
                
                if docs:
                    st.divider()
                    with st.expander("🔍 AI가 참고한 유사 판례 보기"):
                        for i, doc in enumerate(docs):
                            st.markdown(f"**[판례 {i+1}] {doc.metadata.get('case_name', '제목 없음')}**")
                            st.caption(f"사건번호: {doc.metadata.get('case_number', '-')}")
                            st.info(f"판결요지: {doc.page_content[:200]}...") 
                            st.text(doc.page_content)
                            st.markdown("---")

# ============================================================
# [탭 4] 하이브리드 상담 (Hybrid RAG + Evaluation)
# ============================================================
with tab4:
    st.header("통합 법률 상담 & 신뢰도 평가")
    st.markdown("""
    **법령(API)**과 **판례(Vector DB)**를 동시에 분석하여 답변하고, 
    **DeepEval**을 통해 답변의 신뢰도(환각 여부, 관련성)를 점수로 보여줍니다.
    """)
    
    user_question_hybrid = st.text_input("통합 질문을 입력하세요", placeholder="예: 직장에서 괴롭힘을 당했는데 신고하면 불이익이 있을까요?", key="tab4_input")
    
    if st.button("통합 분석 시작", type="primary", key="tab4_btn"):
        if not user_question_hybrid:
            st.warning("질문을 입력해주세요.")
        else:
            # 1. 통합 검색 및 답변 생성
            with st.status("🚀 통합 RAG 시스템 가동 중...", expanded=True) as status:
                # integrated_rag.py의 함수 호출
                answer, context, logs = generate_integrated_answer(user_question_hybrid)
                
                for log in logs:
                    st.write(log)
                
                status.update(label="답변 생성 완료! 평가를 시작합니다.", state="complete")
            
            # 2. 답변 출력
            st.subheader("🤖 통합 분석 결과")
            st.markdown(answer)
            
            st.divider()
            
            # 3. DeepEval 평가 (시간이 좀 걸릴 수 있음)
            with st.spinner("📊 AI 심판관이 답변을 채점하고 있습니다... (DeepEval 실행 중)"):
                try:
                    eval_result = evaluate_rag_response(user_question_hybrid, answer, context)
                    
                    st.subheader("💯 답변 신뢰도 리포트")
                    col1, col2 = st.columns(2)
                    
                    # 신실성(Faithfulness)
                    with col1:
                        score = eval_result['faithfulness']['score']
                        st.metric("사실 충실도 (Faithfulness)", f"{score:.2f}", help="답변이 법령/판례에 근거했는지 판단합니다.")
                        if score < 0.7:
                            st.error("⚠️ 경고: 환각(Hallucination) 가능성 있음")
                        else:
                            st.success("✅ 근거 자료에 충실함")
                        with st.expander("채점 사유"):
                            st.write(eval_result['faithfulness']['reason'])
                    
                    # 관련성(Relevancy)
                    with col2:
                        score = eval_result['relevancy']['score']
                        st.metric("질문 관련성 (Relevancy)", f"{score:.2f}", help="질문의 의도에 맞는 답변인지 판단합니다.")
                        if score < 0.7:
                            st.warning("⚠️ 핵심을 놓쳤을 수 있음")
                        else:
                            st.success("✅ 질문 의도에 부합함")
                        with st.expander("채점 사유"):
                            st.write(eval_result['relevancy']['reason'])
                            
                except Exception as e:
                    st.error(f"평가 중 오류가 발생했습니다: {e}")
                    st.info("API 키 설정이나 네트워크 상태를 확인해주세요.")

            # 4. 참고 자료 표시
            with st.expander("📚 AI가 참고한 통합 자료 (법령 + 판례)"):
                st.markdown("#### [참고 1: 법령]")
                st.text(context[0] if context else "없음")
                st.markdown("---")
                st.markdown("#### [참고 2: 판례]")
                st.text(context[1] if len(context) > 1 else "없음")