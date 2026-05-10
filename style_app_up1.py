import streamlit as st
import google.generativeai as genai
import requests
import re
import urllib.parse
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 고유 설정 및 API 키
NAVER_ID = "CS3M6p8wqe7L4t1W4pbW"
NAVER_SECRET = "uh542B_0BS"
MY_REVENUE_LINK = "https://link.inpock.co.kr/shopping1"

try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("⚠️ Streamlit Secrets에 'MY_API_KEY'를 설정해주세요.")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="wide")

# 세션 상태 초기화
if 'stage' not in st.session_state:
    st.session_state.stage = 'ready'
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

# --- [함수] 네이버 쇼핑 API ---
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

st.divider()
col_guide, col_upload = st.columns([1.3, 1])

with col_guide:
    st.markdown("### 📽️ 촬영 가이드 및 업로드")
    st.video("https://www.youtube.com/watch?v=1vE5QSvW_Vg")
    
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
                    
                    st.session_state.analysis_text = response.text
                    keywords = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[(.*?)\]', response.text)
                    if keywords:
                        k_list = [k.strip() for k in keywords.group(1).split(',')]
                        st.session_state.products = [get_gender_item(gender, k) for k in k_list[:4]]
                    
                    st.session_state.stage = 'analyzed'
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")

if st.session_state.stage in ['analyzed', 'shopping']:
    st.divider()
    st.subheader("📊 AI 스타일 정밀 분석 리포트")
    st.markdown(f"<div class='analysis-result'>{st.session_state.analysis_text}</div>", unsafe_allow_html=True)
    
    if st.session_state.stage == 'analyzed':
        st.write("")
        if st.button("✨ 내 체형에 맞는 추천 상품 확인하기", use_container_width=True):
            st.session_state.stage = 'shopping'
            st.rerun()

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
                    st.link_button("🔥 최저가 혜택받기", MY_REVENUE_LINK, use_container_width=True, type="primary")
    
    st.success("분석과 추천이 모두 완료되었습니다! 의뢰인의 체형을 보완해줄 핵심 아이템 입니다.")

# --- [비즈니스 섹션: 구글 시트 연동] ---
def add_poc_registration_form():
    st.markdown("---")
    st.header("💼 Business Edition (Enterprise Only)")
    st.error("🔥 **현재 도입 가능한 슬롯이 단 1개 남았습니다.** (상위 브랜드 4곳 도입 확정)")

    # 구글 시트 연결
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
    except:
        st.warning("⚠️ 구글 시트 연결 설정이 필요합니다.")
        return

    with st.container():
        st.subheader("Early Bird PoC 마지막 슬롯 신청")
        st.write("아래 정보를 입력해 주시면 담당자가 24시간 이내에 연동 가이드를 발송해 드립니다.")
        
        with st.form("poc_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                brand_name = st.text_input("브랜드명 / 회사명*", placeholder="예: 무신사, 스타일스캔")
                manager_name = st.text_input("담당자 성함 및 직함*", placeholder="예: 홍길동 팀장")
            with col2:
                platform = st.selectbox("현재 운영 중인 플랫폼*", ["카페24", "메이크샵", "자사 구축", "기타 플랫폼"])
                contact_info = st.text_input("연락처 / 이메일*", placeholder="example@brand.com")
            
            goal = st.multiselect("가장 고민되는 지표", ["반품률 감소", "구매 전환율 상승", "신규 AI 기술 도입", "퍼스널 컬러 데이터 확보"])
            message = st.text_area("기타 문의사항")
            
            submitted = st.form_submit_button("마지막 슬롯 선점 및 PoC 등록하기")
            
            # 수정된 데이터 처리 부분
            if submitted:
                if brand_name and manager_name and contact_info:
                    try:
                        # 1. 데이터 읽기 시도 (데이터가 없으면 에러가 날 수 있으므로 예외처리)
                        try:
                            existing_data = conn.read(worksheet="style_app")
                        except:
                            # 데이터가 아예 없는 초기 상태라면 헤더만 있는 데이터프레임 생성
                            existing_data = pd.DataFrame(columns=["Timestamp", "Brand", "Manager", "Platform", "Contact", "Goals", "Message"])
                        
                        # 2. 새 데이터 생성
                        new_entry = pd.DataFrame([{
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Brand": brand_name,
                            "Manager": manager_name,
                            "Platform": platform,
                            "Contact": contact_info,
                            "Goals": ", ".join(goal),
                            "Message": message
                        }])
                        
                        # 3. 병합 및 업데이트 (clear_cache=True 추가)
                        updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
                        conn.update(worksheet="style_app", data=updated_df)
                        
                        st.success(f"✅ 신청 완료! {brand_name} 담당자님, 등록되었습니다.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"시트 업데이트 중 오류 발생: {e}")
                else:
                    st.warning("⚠️ 필수 항목(*)을 모두 입력해 주세요.")

    st.info("💡 PoC 비용(₩99,000)은 담당자 확인 후 발송되는 연동 가이드 내 결제 링크를 통해 결제됩니다.")

add_poc_registration_form()
