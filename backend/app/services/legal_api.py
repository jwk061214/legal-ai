import requests
import os

def get_legal_definition(term: str) -> str:
    """
    법제처 오픈API에서 법률 용어 의미 조회
    현재는 데모용 Mock 데이터
    """
    mock = {
        "채무불이행": "채무자가 정당한 이유 없이 이행하지 않는 상태",
        "불가항력": "사람의 힘으로는 어쩔 수 없는 자연재해 또는 사고",
        "계약 해제": "계약을 소급하여 무효로 만드는 것"
    }
    return mock.get(term, "정의를 찾을 수 없습니다.")