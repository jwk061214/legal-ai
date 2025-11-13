from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .schemas import InterpretationRequest, InterpretationResponse
from .services.extract_terms import extract_terms
from .services.legal_api import get_legal_definition
from .services.llm_service import generate_interpretation


app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 나중에 React 도메인으로 제한 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Legal AI backend is running!"}

@app.post("/interpret", response_model=InterpretationResponse)
def interpret_text(req: InterpretationRequest):
    text = req.text

    # 1) 용어 추출
    found_terms = extract_terms(text)

    # 2) 용어 정의 조회
    term_definitions = {
        t: get_legal_definition(t)
        for t in found_terms
    }

    # 3) LLM 해석 생성
    result = generate_interpretation(text, term_definitions)

    return InterpretationResponse(
        result=result,
        terms=term_definitions
    )
