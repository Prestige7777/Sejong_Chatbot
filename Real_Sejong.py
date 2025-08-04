import os
from dotenv import load_dotenv
import streamlit as st
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

# .env에서 OPENAI_API_KEY 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 벡터스토어 및 데이터 경로
persist_dir = "C:/Users/USER/Desktop/WebDevelop/Real_Sejong/chroma_db"
data_path = "C:/Users/USER/Desktop/WebDevelop/Real_Sejong/data.txt"

st.set_page_config(page_title="세종대학교 입시 상담 챗봇", layout="centered")
st.title("🎓 세종대학교 수시 입시 상담 챗봇")

embeddings = OpenAIEmbeddings()

def create_vectorstore():
    with open(data_path, 'r', encoding='utf-8') as f:
        data = f.read()
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=80)
    docs = splitter.create_documents([data])
    vectorstore = Chroma.from_documents(
        docs,
        persist_directory=persist_dir
    )
    vectorstore.persist()
    return vectorstore

# 벡터스토어 로드/생성
if not os.path.exists(persist_dir) or len(os.listdir(persist_dir)) == 0:
    st.info("🔄 벡터스토어를 새로 생성합니다.")
    db = create_vectorstore()
else:
    db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)   # ★★★ 추가!!

retriever = db.as_retriever(search_kwargs={"k": 5})

# 프롬프트 정의
system_prompt = """
너는 세종대학교 입시 전문 상담 챗봇이야.
아래 정보에 기반해 사용자 질문에 성실하고 정확하게, 표나 리스트로 깔끔하게 안내해줘.
불확실한 경우 '입학처로 문의하시기 바랍니다'라고 안내해.
"""

prompt = PromptTemplate(
    template="{system_prompt}\n질문: {question}\n참고자료: {context}\n답변:",
    input_variables=["system_prompt", "question", "context"]
)

llm = ChatOpenAI(model_name="gpt-4o", temperature=0.2)

# LCEL 체인 구성
rag_chain = (
    RunnableParallel({
        "context": retriever,
        "question": RunnablePassthrough()
    })
    | prompt.partial(system_prompt=system_prompt)
    | llm
)

# 메뉴 버튼
menu = st.sidebar.radio(
    "🔹 원하는 정보를 선택하세요",
    [
        "전형 정보 안내",
        "모집 요강 확인",
        "경쟁률/컷트라인 조회",
        "학과 소개",
        "과거 마지막 합격/예비번호"
    ]
)

preset_questions = {
    "전형 정보 안내": "세종대학교 학생부 종합전형, 교과전형, 논술전형에 대해 설명해줘.",
    "모집 요강 확인": "세종대 학과별 모집인원, 지원자격, 제출서류 알려줘.",
    "경쟁률/컷트라인 조회": "최근 3년간 세종대 경쟁률과 컷트라인 알려줘.",
    "학과 소개": "세종대학교 각 학과를 간략히 소개해줘.",
    "과거 마지막 합격/예비번호": "2023~2024학년도 마지막합격자 예비번호 알려줘"
}

with st.form("question_form"):
    user_query = st.text_area(
        "궁금한 점을 직접 입력하거나, 메뉴를 선택해 주세요!",
        value=preset_questions[menu],
        height=80
    )
    submitted = st.form_submit_button("질문하기")

if submitted:
    with st.spinner("답변 생성 중..."):
        answer = rag_chain.invoke(user_query)
        st.markdown(f"#### 답변\n{answer.content}" if hasattr(answer, 'content') else answer)

st.markdown("---")
st.markdown(
    """
    ℹ️ **세종대학교 입학처**  
    - 주소: 서울특별시 광진구 능동로 209(군자동), 세종대학교 입학처  
    - 우편번호: 02006  
    - 전화: (02)3408-3456, (02)3408-4455  
    - 팩스: (02)3408-3556  
    - [입학처 홈페이지 바로가기](https://ipsi.sejong.ac.kr/)
    """
)
