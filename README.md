
# 🧭 세종대학교 입시 상담 챗봇

## 1. 프로젝트 개요

### 1.1. 프로젝트명  
세종대학교 입시 상담 챗봇

### 1.2. 목표  
입시 정보에 접근하기 어려운 수험생들을 위해, **세종대학교 수시 입시 정보**를 AI 챗봇을 통해 직관적으로 제공하는 것을 목표로 합니다. 진학사 경쟁률 데이터와 2026학년도 모집요강 PDF를 기반으로, 실시간 검색 기반 추천형 답변을 제공합니다.

### 1.3. 주요 기능
- 📌 **경쟁률 자동 크롤링**: 진학사 사이트의 경쟁률 정보를 셀레니움으로 자동 수집
- 📌 **PDF 분석**: 모집요강 PDF에서 필요한 정보를 분할 분석
- 📌 **RAG 기반 답변 생성**: LangChain을 통한 검색 기반 답변 제공
- 📌 **Streamlit UI 제공**: 사용자가 메뉴를 선택하거나 직접 질문 가능
- 📌 **지속 가능한 DB 관리**: FAISS 벡터스토어를 활용해 정보 재활용

---

## 2. 프로젝트 설명

### 2.1. 주요 기능과 사용법

1. **앱 실행 및 페이지 접속**  
   `streamlit run app.py` 명령어로 챗봇 실행

2. **사이드바에서 원하는 메뉴 선택**
   - 전형 정보 안내
   - 모집 요강 확인
   - 경쟁률 조회
   - 학과 소개

3. **기본 질문 자동 입력 + 사용자 질문 입력 가능**
   - 메뉴에 따라 기본 질문이 자동 입력되고, 사용자가 직접 수정할 수 있음

4. **AI가 RAG 기반 답변 생성 후 출력**
   - 사용자 질문과 관련된 PDF/크롤링 내용을 검색 후 요약 응답

5. **세종대 입학처 정보 및 로고 표시**
   - 사이드바에 위치 정보와 로고를 함께 출력

---

### 2.2. 코드 설명

- `app.py`: 전체 Streamlit UI, 사용자 입력, 상태 관리, 챗봇 로직 통합 실행

#### 📁 주요 구성

##### 🔹 벡터스토어 생성 및 로드
- `create_vectorstore()` 함수
  - 모집요강 PDF 로딩 (`PyPDFLoader`)
  - 진학사 2023~2025 경쟁률 크롤링 (`Selenium + BeautifulSoup`)
  - `RecursiveCharacterTextSplitter`로 문서 분할
  - `OpenAIEmbeddings` → `FAISS` 저장

##### 🔹 검색 및 답변 생성
- `retriever`: `db.as_retriever(search_type="similarity", k=8)`
- `rag_chain`: `RunnableParallel` + `PromptTemplate` + `ChatOpenAI`
- 검색된 청크 기반으로 프롬프트를 구성하고 GPT-4o가 최종 답변 생성

##### 🔹 사용자 입력 처리
- 메뉴 선택 시 자동 질문 세팅 (`preset_questions`)
- 제출된 질문에 대해 답변 생성
- 답변은 Markdown 형식으로 출력

##### 🔹 디자인 요소
- 배경 이미지 설정 (`set_background_image`)
- 로고 이미지 Base64 인코딩 → 사이드바 중앙 정렬 출력
- 입학처 정보 고정 표시

---

## 3. 기술 스택

| 항목 | 기술 |
|------|------|
| 🧠 LLM | OpenAI `gpt-4o` |
| 📚 RAG | LangChain + FAISS |
| 💬 UI | Streamlit |
| 📄 데이터 | PDF (모집요강), HTML (진학사) |
| 🌐 크롤링 | Selenium, BeautifulSoup |
| 🧠 임베딩 | `OpenAIEmbeddings` |

---

## 4. 향후 개선 방향

- 🔄 데이터 자동 업데이트 스케줄링 (예: cron + 셀레니움)
- 🗃️ 학과별 FAQ 학습 데이터 구축
- 🔍 키워드 기반 필터링 추가 (예: '논술', '면접' 키워드 강조)
- 📈 사용자 질문 통계 분석 후 피드백 루프 적용

---

## 5. 참고 정보

- [세종대학교 입학처 바로가기](https://ipsi.sejong.ac.kr/)
- 진학사 경쟁률 페이지:
  - [2025학년도](https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10950551.html)
  - [2024학년도](https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10950471.html)
  - [2023학년도](https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10950401.html)
