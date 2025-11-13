from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from poc_streamlit.legal_dict import extract_and_define_terms
from poc_streamlit.llm_service import create_easy_legal_interpretation

st.set_page_config(page_title="⚖️ 쉬운 법률 해석 생성기", page_icon="⚖️")

st.title("쉬운 법률 해석 생성기")
st.write("어려운 법률 텍스트(계약서, 판례 등)를 입력하면 AI가 알기 쉽게 풀어서 설명해 드립니다.")
st.markdown("---")


# 예시 텍스트
sample_text = "제7조 (계약의 해제)\n① 매도인 또는 매수인이 본 계약상의 채무불이행을 하였을 경우, 그 상대방은 서면으로 이행을 최고하고 계약을 해제할 수 있다.\n② 천재지변 기타 불가항력의 사유로 계약 이행이 불가능하게 된 때에는 본 계약은 자동 해제된 것으로 본다."

# 사용자 입력
original_text = st.text_area("여기에 법률 텍스트를 입력하세요:", value=sample_text, height=200)

if st.button("해석 생성하기", type="primary"):
    if not original_text:
        st.warning("해석할 법률 텍스트를 입력해주세요.")
    else:
        with st.spinner("AI가 법률 텍스트를 분석하고 있습니다... 잠시만 기다려주세요."):
            # 1. 법률 용어 추출 및 정의
            term_definitions = extract_and_define_terms(original_text)

            # 2. LLM을 통한 쉬운 해석 생성
            easy_interpretation = create_easy_legal_interpretation(original_text, term_definitions)

            st.markdown("---")
            st.subheader("🔍 AI 법률 해석 결과")

            # 결과 출력
            st.success("해석이 완료되었습니다!")
            st.write(easy_interpretation)

            # 참고한 법률 용어 출력 (선택 사항)
            if term_definitions:
                with st.expander("참고한 법률 용어 보기"):
                    for term, definition in term_definitions.items():
                        st.markdown(f"**{term}**: {definition}")