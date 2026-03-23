import streamlit as st
import google.generativeai as genai
import requests
import re
import urllib.parse

# 1. 형님의 API 설정 (직접 입력 혹은 Secrets 활용)
NAVER_ID = "CS3M6p8wqe7L4t1W4pbW"
NAVER_SECRET = "uh542B_0BS"

try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("⚠️ Gemini API 키(MY_API_KEY)를 Streamlit Secrets에 설정해주세요.")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="wide")

# --- [함수] 네이버 쇼핑 API (성별 격리 강화형) ---
def get_strictly_gender_item(gender, keyword):
    # 성별 섞임을 막기 위한 강력한 제외어(-) 전략
    exclude = "남성" if gender == "여성" else "여성"
    # 검색어 예: "여성 오버핏 코트 -남성 -공용 -남녀공용"
    refined_query = f"{gender} {keyword} -{exclude} -공용 -남녀공용"
    
    encoded_keyword = urllib.parse.quote(refined_query)
    url = f"https://openapi.naver.com/v1/search/shop.json?query={encoded_keyword}&display=1&sort=sim"
    
    headers = {
        "X-Naver-Client-Id": NAVER_ID,
        "X-Naver-Client-Secret": NAVER_SECRET
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            items = response.json().get('items', [])
            return items[0] if items else None
        return None
    except:
        return None

# --- [함수] 4개 키워드 추출 ---
def extract_4_keywords(text):
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[(.*?)\]', text, re.MULTILINE)
    if match:
        k_list = [k.strip().replace('[', '').replace(']', '') for k in match.group(1).split(',')]
        return k_list[:4]
    return ["자켓", "팬츠", "스니커즈", "백"]

# --- UI 레이아웃 ---
st.title("👗 AI 스타일 가이드 PRO")
st.markdown("##### 형님, 네이버 API로 성별은 '칼'같이, 수익은 블로그 원고로 '확실'하게!")

gender = st.radio("분석 성별", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("패션 영상 업로드", type=["mp4", "mov"])

if uploaded_file:
    if st.button("🚀 스타일 분석 및 수익 아이템 매칭 시작"):
        with st.spinner("AI가 영상을 분석하고 성별에 맞는 아이템을 매칭 중입니다..."):
            try:
                # 1. Gemini 영상 분석
                video_data = uploaded_file.read()
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"""
                영상 속 스타일을 분석해서 패션 리포트를 작성해줘. 성별: {gender}.
                마지막 줄에 반드시 이 형식을 지켜서 4개 아이템을 뽑아줘:
                # 쇼핑 키워드: [{gender} 상의, {gender} 하의, {gender} 신발, {gender} 잡화]
                """
                response = model.generate_content([prompt, {"mime_type": "video/mp4", "data": video_data}])
                
                # 2. 결과 저장 및 키워드 추출
                analysis_text = response.text
                keywords = extract_4_keywords(analysis_text)
                
                # 3. 네이버 API 개별 호출 (4회)
                final_products = []
                for kw in keywords:
                    prod = get_strictly_gender_item(gender, kw)
                    if prod: final_products.append(prod)
                
                # --- 결과 화면 출력 ---
                st.divider()
                st.subheader("📊 AI 분석 리포트")
                st.info(analysis_text)
                
                st.subheader(f"🛒 추천 {gender} 아이템 4선")
                cols = st.columns(4)
                
                # 블로그 원고용 텍스트 빌더
                blog_script = f"## 오늘의 {gender} 스타일링 추천 리포트\n\n{analysis_text}\n\n---\n### ✨ 추천 아이템 리스트\n"

                for i, item in enumerate(final_products):
                    with cols[i]:
                        title = item['title'].replace('<b>', '').replace('</b>', '')
                        st.image(item['image'], use_container_width=True)
                        st.markdown(f"**{title[:15]}...**")
                        st.markdown(f"**{int(item['lprice']):,}원**")
                        # 현재는 네이버 쇼핑 링크 (수익화를 위해 블로그 활용 권장)
                        st.link_button("최저가 확인", item['link'], use_container_width=True)
                        
                        blog_script += f"{i+1}. {title}\n- 가격: {int(item['lprice']):,}원\n"

                # --- 수익화 핵심: 블로그 자동 원고 ---
                st.divider()
                st.subheader("✍️ 수익 창출용 블로그 원고 (복사해서 쓰세요!)")
                blog_script += f"\n---\n[형님의 수익 링크 넣는 곳]\n{gender} 패션 더보기 👉 https://naver.me/FdoTycFY\n"
                st.text_area("네이버 블로그/포스트에 바로 붙여넣기", blog_script, height=300)
                st.success("위 원고를 복사해서 블로그에 올리고 형님의 naver.me 링크를 달면 애드포스트 수익이 발생합니다!")

            except Exception as e:
                st.error(f"오류 발생: {e}")
