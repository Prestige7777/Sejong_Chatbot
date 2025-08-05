import os
import streamlit as st
import time
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

# ✅ API Key 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ 경로 설정
pdf_path = "C:/Users/USER/Desktop/WebDevelop/Real_Sejong/2026mojip.pdf"
persist_dir = "C:/Users/USER/Desktop/WebDevelop/Real_Sejong/faiss_db"

# ✅ 진학사 URL
jinhak_urls = {
    "2025학년도 수시 경쟁률": "https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10950551.html",
    "2024학년도 수시 경쟁률": "https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10950471.html",
    "2023학년도 수시 경쟁률": "https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10950401.html"
}

# ✅ 크롤링 함수 (셀레니움)
def crawl_jinhak_html_selenium(url: str) -> str:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service(executable_path="C:/chromedriver-win64/chromedriver.exe")  # 경로 맞게 수정
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    time.sleep(2)
    tables = driver.find_elements(By.TAG_NAME, "table")
    all_text = "\n\n".join([table.text for table in tables])
    driver.quit()
    return all_text

# ✅ 벡터스토어 생성 함수
def create_vectorstore():
    all_docs = []

    # 1. PDF 로딩
    pdf_loader = PyPDFLoader(pdf_path)
    pdf_docs = pdf_loader.load()
    for doc in pdf_docs:
        doc.metadata["source"] = "2026모집요강 PDF"
    all_docs.extend(pdf_docs)

    # 2. 진학사 크롤링
    for label, url in jinhak_urls.items():
        try:
            crawled_text = crawl_jinhak_html_selenium(url)
            all_docs.append(Document(page_content=crawled_text, metadata={"source": label}))
            print(f"📄 크롤링된 {label} 텍스트 일부:\n{crawled_text[:300]}")
        except Exception as e:
            print(f"[ERROR] {label} 크롤링 실패: {e}")

    # 3. 텍스트 분할
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = splitter.split_documents(all_docs)

    # 4. 디버깅 로그
    print("✅ 저장된 전체 청크 수:", len(chunks))
    for i, chunk in enumerate(chunks):
        if "2025학년도 수시 경쟁률" in chunk.metadata.get("source", ""):
            print(f"\n🔍 [진학사 청크 예시] {i+1}번 청크\n", chunk.page_content[:300])

    # 5. FAISS 벡터스토어 저장
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embedding=embeddings)
    vectorstore.save_local(persist_dir)
    return vectorstore

# ✅ Streamlit 페이지 설정
st.set_page_config(page_title="세종대학교 입시 상담 챗봇", layout="centered")
st.title("🎓 세종대학교 수시 입시 상담 챗봇")

# ✅ 배경 이미지 설정 함수
import base64

def set_background_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_string}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ✅ 배경 이미지 적용
background_img_path = "C:/Users/USER/Desktop/WebDevelop/Real_Sejong/RealBack.jpg"
set_background_image(background_img_path)

# ✅ 벡터스토어 로드 또는 생성
embeddings = OpenAIEmbeddings()
if not os.path.exists(persist_dir) or not os.listdir(persist_dir):
    st.info("🔄 FAISS 벡터스토어를 새로 생성합니다.")
    db = create_vectorstore()
else:
    db = FAISS.load_local(persist_dir, embeddings, allow_dangerous_deserialization=True)

retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 8})

# ✅ 프롬프트 템플릿
system_prompt = """
너는 세종대학교 입시 전문 상담 챗봇이야.
경쟁률과 관련된 질문은 진학사 데이터에 기반해 답변하고,
그 외 질문은 2026학년도 모집요강 PDF를 참고해서 답변해.
표, 리스트, 구체적 예시를 사용해서 사용자에게 친절하게 알려줘.
불확실하거나 데이터가 부족하면 '입학처로 문의'하라고 안내해.
"""

prompt = PromptTemplate(
    template="{system_prompt}\n질문: {question}\n참고자료: {context}\n답변:",
    input_variables=["system_prompt", "question", "context"]
)

llm = ChatOpenAI(model_name="gpt-4o", temperature=0.2)

rag_chain = (
    RunnableParallel({
        "context": retriever,
        "question": RunnablePassthrough()
    }) | prompt.partial(system_prompt=system_prompt)
      | llm
)

# ✅ 메뉴
menu = st.sidebar.radio(
    "🔹 원하는 정보를 선택하세요",
    [
        "전형 정보 안내",
        "모집 요강 확인",
        "경쟁률 조회",
        "학과 소개"
    ]
)

# ✅ 사이드바 하단 안내
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    ℹ️ **세종대학교 입학처**  
    - 주소: 서울특별시 광진구 능동로 209(군자동)  
    - 전화: (02)3408-3456, (02)3408-4455  
    - [입학처 홈페이지 바로가기](https://ipsi.sejong.ac.kr/)
    """
)

# ✅ 로고 이미지를 base64로 인코딩하는 함수
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# ✅ 로고 경로
logo_path = "C:/Users/USER/Desktop/WebDevelop/Real_Sejong/logo.png"
encoded_image = get_base64_image(logo_path)

# ✅ 중앙 정렬된 로고 + 텍스트 출력
st.sidebar.markdown(
    f"""
    <div style='text-align: center; margin-top: 15px;'>
        <img src='data:image/png;base64,{encoded_image}' width='150'/>
        <p style='margin-top: 5px; font-weight: bold; font-size: 16px;'>세종대학교</p>
    </div>
    """,
    unsafe_allow_html=True
)


preset_questions = {
    "전형 정보 안내": "학생부 종합전형에 대해 설명해줘.",
    "모집 요강 확인": "세종대 수시 제출서류 알려줘.",
    "경쟁률 조회": "2024학년도 경제학과 경쟁률 알려줘.",
    "학과 소개": "나노신소재공학과에 대해서 소개해줘"
}

# ✅ 질문 입력
with st.form("question_form"):
    user_query = st.text_area(
        "궁금한 점을 직접 입력하거나, 메뉴를 선택해 주세요!",
        value=preset_questions[menu],
        height=80
    )
    submitted = st.form_submit_button("질문하기")

if submitted:
    with st.spinner("답변 생성 중..."):
        #docs = retriever.get_relevant_documents(user_query)
        #for i, d in enumerate(docs):
            #st.write(f"🔹 검색된 청크 {i+1}: 출처 → {d.metadata.get('source', '알 수 없음')}")
            #st.code(d.page_content[:300])

        answer = rag_chain.invoke(user_query)
        st.markdown(f"#### 답변\n{answer.content}" if hasattr(answer, 'content') else answer)
