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

# 세션 상태 초기화 (단계 제어용)
if 'stage' not in st.session_state:
    st.session_state.stage = 'ready' # ready -> analyzed -> shopping
if 'analysis_text' not in st.session_state:
    st.session_state.analysis_text = ""
if 'products' not in st.session_state:
    st.session_state.products = []

# 2. 비주얼 커스텀 스타일링
st.markdown("""
<style>
    .main-title { color: #1E3A8A; font-weight: 800; text-align: center; font-size: 2.2rem; }
    .point-text { color: #2563EB; font-weight: 600; text-align: center; }
    .guide-card { background-color: white; padding: 15px; border-radius: 12px; border-left: 5px solid #2563EB; margin-bottom: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .stButton>button { border-radius: 10px; font-weight: bold; height: 3rem; }
    .analysis-result { background-color: #F0F7FF; padding: 25px; border-radius: 15px; border: 1px solid #BFDBFE; line-height: 1.8; font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)

# --- [함수] 네이버 쇼핑 API (성별 정밀 필터) ---
def get_gender_item(gender, keyword):
    exclude = "남성" if gender == "여성" else "여성"
    refined_query = f"{gender}용 {keyword} -{exclude} -공용"
    encoded_query = urllib.parse.quote(refined_query)
    url = f"https://openapi.naver.com/v1/search/shop.json?query={encoded_query}&display=1&sort=sim"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    try:
        res = requests.get(url, headers=headers)
        return res.json().get('items', [None])[0] if res.status_code == 200 else None
    except: return None

# --- UI 레이아웃 ---
st.markdown("<h1 class='main-title'>👗 AI 스타일 가이드 PRO</h1>", unsafe_allow_html=True)
st.markdown("<p class='point-text'>실시간 비디오 분석으로 완성하는 당신만의 퍼스널 룩</p>", unsafe_allow_html=True)

# [상단 섹션] 촬영 가이드 및 업로드
st.divider()
col_guide, col_upload = st.columns([1.3, 1])

with col_guide:
    st.markdown("### 📽️ 촬영 가이드 및 업로드")
    st.video("https://www.youtube.com/watch?v=1vE5QSvW_Vg") # 형님의 유튜브 가이드 영상
    
    # 4가지 수칙 레이아웃
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='guide-card'>👤 <b>1. 전신 샷 필수</b><br>머리부터 발끝까지 다 들어와야 해요.</div>", unsafe_allow_html=True)
        st.markdown("<div class='guide-card'>🔄 <b>2. 360도 회전</b><br>천천히 한 바퀴 돌면 입체 분석이 가능합니다.</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='guide-card'>💡 <b>3. 밝은 조명</b><br>조명이 밝아야 컬러를 정확히 잡아내요.</div>", unsafe_allow_html=True)
        st.markdown("<div class='guide-card'>⏱️ <b>4. 5~15초 권장</b><br>너무 길면 업로드가 느려질 수 있어요.</div>", unsafe_allow_html=True)

with col_upload:
    st.markdown("### 🎬 영상을 업로드하세요")
    gender = st.radio("분석 성별", ["여성", "남성"], horizontal=True)
    uploaded_file = st.file_uploader("", type=["mp4", "mov"])
    
    if uploaded_file:
        if st.button("🚀 스타일 분석 시작", use_container_width=True, type="primary"):
            with st.spinner("잠시만 기다려주십시요! AI가 분석 중입니다..."):
                try:
                    video_data = uploaded_file.read()
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    prompt = f"영상 속 인물의 스타일을 '{gender}' 기준으로 정밀 분석하고 패션 리포트를 작성해줘. 마지막엔 반드시 # 쇼핑 키워드: [{gender} 상의, {gender} 하의, {gender} 신발, {gender} 잡화] 형식을 포함해줘."
                    response = model.generate_content([prompt, {"mime_type": "video/mp4", "data": video_data}])
                    
                    # 데이터 저장 및 단계 변경
                    st.session_state.analysis_text = response.text
                    keywords = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[(.*?)\]', response.text)
                    if keywords:
                        k_list = [k.strip() for k in keywords.group(1).split(',')]
                        st.session_state.products = [get_gender_item(gender, k) for k in k_list[:4]]
                    
                    st.session_state.stage = 'analyzed'
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")

# --- [단계별 출력 제어] ---

# 1단계: 분석 결과 리포트 보여주기
if st.session_state.stage in ['analyzed', 'shopping']:
    st.divider()
    st.subheader("📊 AI 스타일 정밀 분석 리포트")
    st.markdown(f"<div class='analysis-result'>{st.session_state.analysis_text}</div>", unsafe_allow_html=True)
    
    # 분석 내용을 다 읽은 후에만 버튼이 나타남
    if st.session_state.stage == 'analyzed':
        st.write("")
        if st.button("✨ 내 체형에 맞는 추천 상품 확인하기", use_container_width=True):
            st.session_state.stage = 'shopping'
            st.rerun()

# 2단계: 추천 상품 리스트 보여주기
if st.session_state.stage == 'shopping':
    st.divider()
    st.subheader(f"🛒 추천 {gender} 아이템 4선")
    cols = st.columns(4)
    for i, item in enumerate(st.session_state.products):
        if item:
            with cols[i]:
                with st.container(border=True):
                    title = item['title'].replace('<b>', '').replace('</b>', '')
                    st.image(item['image'], use_container_width=True)
                    st.markdown(f"**{title[:15]}...**")
                    st.markdown(f"**{int(item['lprice']):,}원**")
                    
                    # 모든 버튼은 형님의 인포크링크로 고정
                    st.link_button("🔥 최저가 혜택받기", MY_REVENUE_LINK, use_container_width=True, type="primary")
    
    st.success("분석과 추천이 모두 완료되었습니다! 의뢰인의 체형을 보완해줄 핵심 아이템 입니다.  추가 분석을 원하시면 영상을 다시 올려주세요.")


import streamlit as st

def add_business_section():
    st.markdown("---")
    st.header("💼 Business Edition (Enterprise Only)")
    
    # 상단 긴박감 조성 배너
    st.error("🔥 **현재 도입 가능한 슬롯이 단 1개 남았습니다.** (상위 브랜드 4곳 도입 확정)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Early Bird PoC")
        st.write("2주간의 기술 검증 및 반품률 감소 리포트 제공")
        # 버튼 클릭 시 구글 폼으로 연결
        st.link_button("마지막 슬롯 선점하기 (₩99,000)", 
                       "https://docs.google.com/spreadsheets/d/1beDxNIxoDtj7d151FSrDETLn-uOtA8CNHd5tMi2sglo/edit?gid=0#gid=0")

    with col2:
        st.subheader("Standard SaaS")
        st.write("월 구독형 엔진 이용 및 API 무제한 호출")
        st.button("슬롯 대기 신청", help="현재 슬롯 마감으로 대기 명단에 등록됩니다.")

    with col3:
        st.subheader("Custom Engine")
        st.write("독립 서버 구축 및 전용 모델 파인튜닝")
        st.link_button("담당자 직통 문의", "bslee@yahoo.com")

    st.info("💡 PoC 신청 시 담당자가 24시간 이내에 연동 가이드를 발송해 드립니다.")

add_business_section()
