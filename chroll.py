import requests
from bs4 import BeautifulSoup

urls = [
    "https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10950551.html",
    "https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10950471.html",
    "https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10950401.html"
]

all_text = ""

for url in urls:
    res = requests.get(url)
    res.encoding = 'utf-8'  # 혹시모를 한글 깨짐 방지
    soup = BeautifulSoup(res.text, "html.parser")

    # 텍스트만 추출
    text = soup.get_text(separator="\n", strip=True)
    all_text += f"\n=== URL: {url} ===\n" + text + "\n\n"

# 저장
with open("C:/Users/USER/Desktop/WebDevelop/Real_Sejong/data.txt", "w", encoding="utf-8") as f:
    f.write(all_text)
