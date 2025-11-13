def extract_terms(text: str):
    """
    데모 버전: 텍스트에서 법률 용어를 단순 탐색하여 추출.
    실제로는 형태소 분석 + 법률 용어 사전 기반 확장 예정.
    """
    legal_terms = ["채무불이행", "불가항력", "계약 해제"]
    
    found = []
    for term in legal_terms:
        if term in text:
            found.append(term)

    return found
