# ⚖️ 쉬운 법률 해석 생성기 (Easy Legal Interpretation Generator)

이 프로젝트는 어려운 법률 텍스트(계약서, 판례 등)를 입력받아, LLM(거대 언어 모델)을 활용해 일반인이 이해하기 쉬운 언어로 해석해주는 데모 애플리케이션입니다.

## 🌟 프로젝트 목표

법률 용어는 전문적이고 복잡하여 일반인이 접근하기 어렵습니다. 이 프로젝트의 목표는 법률 텍스트에서 주요 용어를 식별하고 그 의미를 찾아낸 뒤, 이 정보를 AI에게 제공하여 원문의 의미를 해치지 않으면서도 **쉽고 명확하게** 풀어서 설명하는 것입니다.

**작동 흐름:**

1.  **Input:** 사용자가 어려운 법률 텍스트를 입력합니다.
2.  **Processing:**
    * 텍스트에서 법률 용어를 추출합니다.
    * 법률 용어 API([법제처 오픈 API](https://open.law.go.kr/LSO/openApi/guideList.do))를 통해 용어의 정의를 가져옵니다.
    * 원본 텍스트와 용어 정의를 LLM 프롬프트로 구성합니다.
3.  **Output:** LLM이 생성한 쉬운 법률 해석을 사용자에게 보여줍니다.

## 🛠️ 사용된 기술 스택

* **Frontend:** Streamlit
* **LLM:** Gemini API (`gemini-2.0-flash`)
* **API (External):** 대한민국 법제처 법률 용어 API


### 1. 사전 준비

* **Python 3.9+** 환경

### 2. 프로젝트 설정

1.  **저장소 클론:**
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```

2.  **가상 환경 생성 및 활성화 (권장):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate   # Windows
    ```

3.  **필요한 라이브러리 설치:**

4.  **.env 파일 생성:**
    프로젝트 루트에 `.env` 파일을 만듭니다.

    ```
    # .env 파일
    MOLEG_API_KEY="your-api"
    GEMINI_API_KEY="your-api"
    ```

### 3. 데모 실행
**Streamlit 앱 실행:** 터미널에서 다음 명령어를 입력합니다.
    ```bash
    streamlit run app.py
    ```

브라우저에서 `http://localhost:8501` 주소로 접속하여 데모를 사용할 수 있습니다.

## 📂 프로젝트 구조
쉬운-법률-해석기/ <br>
├── 📄 app.py              # Streamlit 메인 애플리케이션 <br>
├── 🤖 llm_service.py      # Gemini API 연동 (AI 해석 생성) <br>
├── 📚 legal_dict.py       # 법률 용어 API 연동 (용어 정의 추출) <br>
├── 📦 requirements.txt    # 필요한 파이썬 라이브러리 목록 <br>
├── 🔒 .env                # API 키 및 환경 변수 (Git에 포함되지 않음) <br>
└── 📖 README.md           # 프로젝트 설명
