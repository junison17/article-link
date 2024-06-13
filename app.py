import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO

# 네이버 검색 결과를 가져오는 함수
def get_naver_results(query, page=1):
    url = f"https://search.naver.com/search.naver?query={query}&start={page * 10 + 1}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for item in soup.select(".news_tit"):
        title = item.get_text()
        link = item["href"]
        results.append((title, link))

    for item in soup.select(".sh_blog_title"):
        title = item.get_text()
        link = item["href"]
        results.append((title, link))

    return results

# 모든 페이지의 결과를 수집하는 함수
def collect_all_results(query, max_pages=10):
    all_results = []
    for page in range(max_pages):
        results = get_naver_results(query, page)
        if not results:
            break
        all_results.extend(results)
    return all_results

# 엑셀 파일로 저장하는 함수
def save_to_excel(data):
    df = pd.DataFrame(data, columns=["Title", "Link"])
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()  # save() 대신 close() 사용
    processed_data = output.getvalue()
    return processed_data

# 기사 본문 텍스트를 가져오는 함수
def get_article_text(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 네이버 뉴스 기사의 본문을 추출하는 다양한 시도
    article_body = soup.find('div', {'id': 'articleBodyContents'})
    if not article_body:
        article_body = soup.find('div', {'class': 'news_end'})
    if not article_body:
        article_body = soup.find('div', {'class': 'content'})

    if article_body:
        return article_body.get_text(separator='\n').strip()
    return "본문을 추출할 수 없습니다."

# Streamlit 애플리케이션 인터페이스
st.title("Naver Article and Blog Title Collector")
query = st.text_input("Enter your query:")
max_pages = st.number_input("Enter the number of pages to scrape:", min_value=1, max_value=100, value=10)

if st.button("Search"):
    if query:
        results = collect_all_results(query, max_pages)
        if results:
            st.write(f"Found {len(results)} results")
            
            # 스크롤이 있는 리스트 뷰 생성
            with st.expander("Show Results"):
                for idx, (title, link) in enumerate(results):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"[{title}]({link})")
                    with col2:
                        article_text = get_article_text(link)
                        st.download_button(
                            label="Download Text",
                            data=article_text,
                            file_name=f"{title}.txt",
                            mime="text/plain",
                            key=f"download_button_{idx}"
                        )
            
            # 파일 저장 버튼
            excel_data = save_to_excel(results)
            st.download_button(label="Download Excel file", data=excel_data, file_name="results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="excel_download_button")
        else:
            st.write("No results found.")
    else:
        st.write("Please enter a query.")

