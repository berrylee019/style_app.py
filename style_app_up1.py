import streamlit as st
import google.generativeai as genai
import requests
import re
import urllib.parse

# 1. 고유 설정 및 API 키
NAVER_ID = "CS3M6p8wqe7L4t1W4pbW"
NAVER_SECRET = "uh542B_0BS"
MY_REVENUE_LINK = "https://link.inpock.co.kr/shopping1"

try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("⚠️ Streamlit Secrets에 'MY_API_KEY'를 설정해주세요.")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="wide")

# 2. 비주얼 커스텀 스타일링
st.markdown("""
<style>
    .main-title { color: #1E3A8A; font-weight: 800; text-align: center; font-size: 2.5rem; }
    .sub-title { color: #6B7280; text-align: center; margin-bottom: 30px; }
    .guide-box { background-color: #EFF6FF; border-radius: 15px; padding: 20px; border: 1px solid #BFDBFE; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; height: 3rem; background-color: #2563EB !important; }
</style>
""", unsafe_allow_html=True)

# --- [함수] 네이버 쇼핑 API (성별 정밀 필터) ---
def get_gender_item(gender, keyword):
    exclude = "남성" if gender == "여성" else "여성"
    refined_query = f"{gender} {keyword} -{exclude} -공용"
    encoded_query = urllib.parse.quote(refined_query)
    url = f"https://openapi.naver.com/v1/search/shop.json?query={encoded_query}&display=1&sort=sim"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    try:
        res = requests.get(url, headers=headers)
        return res.json().get('items', [None])[0] if res.status_code == 200 else None
    except: return None

# --- UI 레이아웃 ---
st.markdown("<h1 class='main-title'>👗 AI 스타일 가이드 PRO</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>당신의 영상 10초로 완성하는 완벽한 퍼스널 스타일링</p>", unsafe_allow_html=True)

# [상단 섹션] 가이드 영상 및 업로드
col1, col2 = st.columns([1.2, 1])

with col1:
    st.markdown("### 📽️ 촬영 가이드 (필독!)")
    # 형님이 주신 유튜브 쇼츠 링크를 임베드합니다.
    st.video("https://www.youtube.com/watch?v=1vE5QSvW_Vg")
    st.markdown("""
    <div class='guide-box'>
    ✅ <b>전신 샷 필수:</b> 머리부터 발끝까지 화면에 꽉 차게!<br>
    ✅ <b>360도 회전:</b> 천천히 한 바퀴 돌아주시면 분석이 정확해요.<br>
    ✅ <b>밝은 조명:</b> 조명이 밝아야 실제 컬러를 잘 잡습니다.
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("### 🎬 영상 업로드 및 분석")
    gender = st.radio("분석할 성별을 선택하세요", ["여성", "남성"], horizontal=True)
    uploaded_file = st.file_uploader("분석할 영상을 올려주세요 (MP4, MOV)", type=["mp4", "mov"])
    
    if uploaded_file and st.button("🚀 스타일 분석 시작"):
        with st.spinner("AI가 영상을 분석하고 최적의 아이템을 매칭 중입니다..."):
            # Gemini 영상 분석 로직 (중략 - 이전 코드와 동일)
            # ... 분석 후 키워드 4개 추출 ...
            keywords = ["자켓", "팬츠", "슈즈", "액세서리"] # 예시 키워드
            
            st.session_state['analysis_done'] = True
            st.session_state['items'] = [get_gender_item(gender, k) for k in keywords]

# [하단 섹션] 분석 결과 및 수익 아이템 전시
if st.session_state.get('analysis_done'):
    st.divider()
    st.subheader(f"🛒 AI 추천 {gender} 스타일링 아이템")
    cols = st.columns(4)
    
    for i, item in enumerate(st.session_state['items']):
        if item:
            with cols[i]:
                with st.container(border=True):
                    title = item['title'].replace('<b>', '').replace('</b>', '')
                    st.image(item['image'], use_container_width=True)
                    st.markdown(f"**{title[:15]}...**")
                    st.markdown(f"**{int(item['lprice']):,}원**")
                    
                    # [핵심] 모든 클릭은 형님의 인포크링크로!
                    st.link_button("🔥 최저가 혜택받기", MY_REVENUE_LINK, type="primary")

st.success(f"가이드 영상을 보시고 오른쪽 버튼을 통해 본인의 10초 영상을 올리시면 AI가 분석을 시작합니!")
