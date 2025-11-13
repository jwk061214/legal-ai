from langchain_core.prompts import PromptTemplate
from langchain_community.llms import Ollama             # <-- HuggingFace가 아닌 Ollama 임포트
from langchain_core.output_parsers import StrOutputParser

def create_easy_legal_interpretation(original_text, term_definitions):
    """
    LLM을 이용해 법률 텍스트를 쉽게 해석합니다.
    """
    
    # Ollama를 사용해 M4 맥북의 로컬 모델을 지정합니다.
    # (Ollama 앱이 백그라운드에서 실행 중이어야 합니다)
    llm = Ollama(
        model="gemma2:9b",  # 'ollama list'로 확인된 설치된 모델 이름
        temperature=0.7
    )

    # 'Chat'이 아닌 기본 PromptTemplate (text-generation)
    template = """
    당신은 법률 문서를 일반인이 이해하기 쉽게 설명해주는 전문가입니다.
    아래의 원문 텍스트와 법률 용어의 뜻을 참고하여, 원문을 쉽고 명확하게 해석해주세요.

    **원문 텍스트:**
    {original_text}

    **참고 법률 용어:**
    {term_definitions}

    **쉬운 해석:**
    """
    prompt = PromptTemplate.from_template(template)

    # Langchain 체인 구성
    chain = prompt | llm | StrOutputParser()

    # 체인 실행
    response = chain.invoke({
        "original_text": original_text,
        "term_definitions": "\n".join([f"- {term}: {definition}" for term, definition in term_definitions.items()])
    })

    return response