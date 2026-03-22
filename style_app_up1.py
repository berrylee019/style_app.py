import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import re
import openai
import streamlit.components.v1 as components
import urllib.parse

# 1. API 키 및 페이지 설정
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("API 키 설정이 필요합니다! .streamlit/secrets.toml을 확인해 주셔요.")

st.set_page_config(page_title="AI 스타일 가이드", page_icon="👗", layout="centered")

# --- 커스텀 CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .main-title { font-size: 2.5rem; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 0.5rem; }
    .sub-title { font-size: 1.1rem; color: #64748B; text-align: center; margin-bottom: 2rem; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 700; transition: all 0.3s; }
    </style>
    """, unsafe_allow_html=True)

# --- [함수] 쇼핑 키워드 추출 (강력한 정규식) ---
def extract_shop_keywords(text):
    try:
        match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[?(.*?)\]?$', text, re.MULTILINE)
        if match:
            raw_keywords = match.group(1).split(',')
            keywords = [k.strip().replace('[', '').replace(']', '') for k in raw_keywords]
            return [k for k in keywords if k][:3]
    except:
        pass
    return ["기능성 티셔츠", "린넨 팬츠", "데일리 룩"] # 추출 실패 시 기본값

# --- UI 상단 레이아웃 ---
col_img, col_txt = st.columns([1, 4])
with col_img:
    if os.path.exists("styley.png"): st.image("styley.png", width=110)
    else: st.write("🖼️")
with col_txt:
    st.markdown('<div style="background: #E1F5FE; border-radius: 15px; padding: 15px; border: 1px solid #B3E5FC;">반갑습니다 형님! 오늘 베스트 룩과 수익 링크까지 싹 다 잡아드릴게유! ✨</div>', unsafe_allow_html=True)

st.markdown('<p class="main-title">👗 AI 스타일 가이드</p>', unsafe_allow_html=True)

# --- 섹션 1: 설정 및 업로드 ---
c_v, c_u = st.columns([1.2, 1])
with c_v:
    video_html = '<iframe width="100%" height="500" src="https://www.youtube.com/embed/1vE5QSvW_Vg" frameborder="0" allowfullscreen></iframe>'
    components.html(video_html, height=520)
with c_u:
    gender = st.radio("1️⃣ 모델 성별 선택", ["여성", "남성"], horizontal=True)
    uploaded_file = st.file_uploader("2️⃣ 영상 업로드", type=["mp4", "mov", "avi"])

# --- 섹션 2: 분석 실행 (할당량 에러 방지용 모델 변경) ---
if uploaded_file:
    if st.button("🚀 AI 스타일 분석 시작", use_container_width=True, type="primary"):
        with st.status("🔍 분석 중...") as status:
            try:
                # 2.0-flash가 할당량이 찼다면 1.5-flash로 우회 시도
                model = genai.GenerativeModel('gemini-1.5-flash') 
                video_part = {"mime_type": uploaded_file.type, "data": uploaded_file.read()}
                prompt = f"""
                당신은 최고의 AI 스타일리스트입니다. {gender} 사용자의 영상을 분석하여 다음 규격에 맞춰 상세 리포트를 작성하세요.
                1. 스타일 페르소나 / 2. 체형 강점 / 3. 퍼스널 컬러 / 4. 스타일링 팁
                마지막 줄 형식 엄수: # 쇼핑 키워드: [키워드1, 키워드2, 키워드3]
                """
                response = model.generate_content([prompt, video_part], request_options={"timeout": 600})
                st.session_state.analysis_result = response.text
                status.update(label="✅ 분석 완료!", state="complete")
            except Exception as e:
                st.error(f"오류: {e}")

# --- 섹션 3: 결과 및 [수익화 버튼] 무조건 출력 ---
if 'analysis_result' in st.session_state:
    st.divider()
    st.markdown(st.session_state.analysis_result)

    # 🛍️ 쿠팡 쇼핑 버튼 생성 섹션
    keywords = extract_shop_keywords(st.session_state.analysis_result)
    st.markdown("#### 🛍️ AI 추천 아이템 바로 구매하기")
    cols = st.columns(len(keywords))
    
    for i, keyword in enumerate(keywords):
        with cols[i]:
            # [최종 솔루션] 숏링크 + 다이렉트 쿼리 조합
            search_query = f"{gender} {keyword}".strip()
            encoded_query = urllib.parse.quote(search_query)
            
            # AF5326630 형님 아이디가 박힌 가장 단순하고 강력한 검색 주소
            shop_url = f"https://link.coupang.com/a/AF5326630?q={encoded_query}"
            
            st.link_button(f"🛒 {keyword}", shop_url, use_container_width=True)
            
    st.caption("※ 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다. (ID: AF5326630)")
    st.divider()

    # 🎨 추천 스타일 화보 생성 (이후 로직은 그대로)
    if st.button(f"🎨 {gender} 추천 스타일 화보 생성", use_container_width=True):
        # ... (화보 생성 로직) ...
        pass

st.markdown("<br><p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>Copyright 2026. Microhard All rights reserved.</p>", unsafe_allow_html=True)
