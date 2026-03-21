import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from datetime import datetime
import os
import re
import openai
import streamlit.components.v1 as components

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
    .tip-card { background-color: #f8fafc; border-radius: 10px; padding: 20px; border-left: 5px solid #3B82F6; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- [함수] 쇼핑 키워드 추출 로직 ---
def extract_shop_keywords(text):
    try:
        # 정규표현식으로 [# 쇼핑 키워드: [A, B, C]] 형태를 찾아냅니다.
        match = re.search(r'# 쇼핑 키워드: \[(.*?)\]', text)
        if match:
            keywords = [k.strip() for k in match.group(1).split(',')]
            return keywords[:3] 
    except:
        pass
    return ["여성 패션", "남성 패션", "인기 코디"] # 추출 실패 시 기본값

# --- [함수] PDF 및 비주얼 생성 엔진 ---
def create_pdf_file(text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=text_content.encode('latin-1', 'ignore').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

def generate_style_visual(style_description, selected_gender):
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        base_desc = "Elegant Korean model, sophisticated modest fashion, high-end editorial photography. "
        full_prompt = f"{base_desc} Style: {style_description[:100]}. {selected_gender} model, natural lighting, 4k."
        response = client.images.generate(model="dall-e-3", prompt=full_prompt, size="1024x1024", n=1)
        return response.data[0].url
    except Exception as e:
        st.error(f"이미지 생성 중 오류 발생: {e}")
        return None

# --- UI 상단 ---
col_img, col_txt = st.columns([1, 4])
with col_img:
    if os.path.exists("styley.png"): st.image("styley.png", width=110)
    else: st.write("🖼️")

with col_txt:
    st.markdown("""<div style="background: #E1F5FE; border-radius: 15px; padding: 15px; border: 1px solid #B3E5FC;">
        <strong style="color: #0288D1;">Styley:</strong> "반갑습니다 형님! 오늘 베스트 룩과 쇼핑 아이템까지 싹 다 뽑아드릴게유! ✨"</div>""", unsafe_allow_html=True)

st.markdown('<p class="main-title">👗 AI 스타일 가이드</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">실시간 비디오 분석으로 완성하는 당신만의 퍼스널 룩</p>', unsafe_allow_html=True)

# --- 섹션 1: 가이드 및 업로드 ---
c_v, c_u = st.columns([1.2, 1])
with c_v:
    st.markdown('<h4 style="color: #1a73e8; margin-top: 0;">📹 촬영 가이드</h4>', unsafe_allow_html=True)
    embed_url = "https://www.youtube.com/embed/1vE5QSvW_Vg?rel=0&modestbranding=1"
    video_html = f'<iframe width="100%" height="500" src="{embed_url}" frameborder="0" allowfullscreen></iframe>'
    components.html(video_html, height=520)

with c_u:
    st.markdown("#### ⚙️ 설정 및 업로드")
    gender = st.radio("1️⃣ 시각화할 모델 성별 선택", ["여성", "남성"], horizontal=True)
    with st.expander("⚠️ 촬영 전 체크!", expanded=True):
        st.markdown("* 단색 배경 / 전신 노출 / 2~3m 거리")
    uploaded_file = st.file_uploader("2️⃣ 영상을 업로드하세요", type=["mp4", "mov", "avi"])
    if uploaded_file:
        st.success("✅ 준비 완료! 아래 버튼을 누르셔요.")

# --- 섹션 2: 분석 실행 (강화된 프롬프트 탑재) ---
if uploaded_file:
    if st.button("🚀 AI 스타일 분석 시작", use_container_width=True, type="primary"):
        with st.status("🔍 AI가 스타일과 쇼핑 키워드를 분석 중...", expanded=True) as status:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                video_part = {"mime_type": uploaded_file.type, "data": uploaded_file.read()}
                
                # [수정됨] 쇼핑 키워드 추출을 위한 강화된 프롬프트
                prompt = f"""
                이 영상의 주인공은 {gender}이며, 한국인(Korean)입니다.
                반드시 {gender}의 관점에서, '한국인 모델' 특유의 우아함과 세련미를 중심으로 분석하세요.

                항목별 리포트 내용:
                # 1. 스타일 페르소나
                # 2. 체형 강점 분석
                # 3. 퍼스널 컬러 제안
                # 4. 오늘의 스타일링 팁

                [중요: 쇼핑 자동화를 위한 규칙]
                마지막 줄에 반드시 분석된 스타일과 가장 잘 어울리는 실제 구매 가능한 '쇼핑 검색어' 3개를 아래 형식으로만 적으세요.
                형식: # 쇼핑 키워드: [키워드1, 키워드2, 키워드3]
                (예: # 쇼핑 키워드: [린넨 셔츠, 와이드 슬랙스, 가죽 로퍼])
                """
                
                response = model.generate_content([prompt, video_part])
                st.session_state.analysis_result = response.text
                status.update(label="✅ 분석 완료!", state="complete")
            except Exception as e:
                st.error(f"오류: {e}")

# --- 섹션 3: 결과 출력 및 수익화 (동적 링크 연결) ---
if 'analysis_result' in st.session_state:
    st.divider()
    st.subheader("📊 AI 프리미엄 스타일 리포트")
    st.markdown(st.session_state.analysis_result)

    # 화보 생성 버튼
    if st.button(f"🎨 {gender} 추천 스타일 화보로 보기", use_container_width=True):
        with st.spinner("AI 화보 생성 중..."):
            img_url = generate_style_visual(st.session_state.analysis_result, gender)
            st.session_state.pictorial_url = img_url

    # 화보 및 동적 쇼핑 버튼 출력 영역
    if 'pictorial_url' in st.session_state and st.session_state.pictorial_url:
        st.image(st.session_state.pictorial_url, caption="AI 맞춤형 스타일 화보")
        
        # [동적 링크 로직 적용]
        keywords = extract_shop_keywords(st.session_state.analysis_result)
        
        st.markdown("#### 🛍️ AI 추천 아이템 바로 구매하기")
        cols = st.columns(len(keywords))
        for i, keyword in enumerate(keywords):
            with cols[i]:
                # 쿠팡 검색 동적 URL 생성
                shop_url = f"https://www.coupang.com/np/search?q={keyword.replace(' ', '+')}"
                st.link_button(f"🛒 {keyword}", shop_url, use_container_width=True)
        
        st.caption("※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.")

        # [Step 2] 고화질 소장 결제
        st.write("")
        with st.container(border=True):
            st.markdown("#### 🖼️ 워터마크 없는 고화질 화보 소장")
            d_col1, d_col2 = st.columns([2, 1])
            with d_col1: st.write("나만의 인생 스타일을 고화질(HD) 이미지로 간직하세요.")
            with d_col2:
                if st.button("💰 고화질 구매 (990원)", use_container_width=True):
                    st.toast("💳 결제 시스템 연동 중...", icon="⏳")

    # [PDF 소장 섹션]
    st.divider()
    st.markdown("### 🚀 리포트 소장하기")
    res_c1, res_c2 = st.columns([1.2, 1])
    with res_c1:
        st.info("카페에서 비밀번호 확인 후 PDF를 다운로드하세요.")
        st.link_button("☕ 카페 바로가기", "https://cafe.naver.com/stylely")
    with res_c2:
        input_pw = st.text_input("비밀번호", type="password")
        if input_pw == "style77":
            st.download_button("📄 PDF 다운로드", data=create_pdf_file(st.session_state.analysis_result), file_name="Style_Report.pdf")

st.markdown("<br><p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>Copyright 2026. Microhard All rights reserved.</p>", unsafe_allow_html=True)
