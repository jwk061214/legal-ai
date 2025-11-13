from langchain_community.llms import Ollama

def generate_interpretation(text: str, terms: dict) -> str:
    llm = Ollama(model="gemma2:9b")

    prompt = f"""
당신은 전문 법률 문서를 일반인이 이해하기 쉽게 해석해주는 전문가입니다.

원문:
{text}

법률 용어와 정의:
{terms}

위의 내용을 참고해서 원문의 의미를 유지하되 쉽게 설명해주세요.
"""
    response = llm.invoke(prompt)
    return response
