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
    </style>
    """, unsafe_allow_html=True)

# --- [함수] 쇼핑 키워드 추출 로직 ---
def extract_shop_keywords(text):
    try:
        match = re.search(r'# 쇼핑 키워드: \[(.*?)\]', text)
        if match:
            keywords = [k.strip() for k in match.group(1).split(',')]
            return keywords[:3]
    except:
        pass
    return ["여성 패션", "남성 패션", "인기 코디"]

# --- [함수] PDF 및 비주얼 생성 엔진 (성별 가이드 강화) ---
def create_pdf_file(text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=text_content.encode('latin-1', 'ignore').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

def generate_style_visual(style_description, selected_gender):
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        if selected_gender == "여성":
            base_desc = "An elegant Korean female model, sophisticated modest fashion, high-end editorial."
        else:
            base_desc = "A distinguished Korean male model, lean refined silhouette, classic tailored fashion."
        
        full_prompt = f"{base_desc} Style: {style_description[:120]}. 4k resolution, studio lighting."
        response = client.images.generate(model="dall-e-3", prompt=full_prompt, size="1024x1024", n=1)
        return response.data[0].url
    except Exception as e:
        st.error("이미지 생성 중 정책/기술적 이슈가 발생했습니다.")
        return None

# --- UI 상단 레이아웃 ---
col_img, col_txt = st.columns([1, 4])
with col_img:
    if os.path.exists("styley.png"): st.image("styley.png", width=110)
    else: st.write("🖼️")

with col_txt:
    st.markdown("""<div style="background: #E1F5FE; border-radius: 15px; padding: 15px; border: 1px solid #B3E5FC;">
        <strong style="color: #0288D1;">Styley:</strong> "반갑습니다 형님! 오늘 베스트 룩과 수익 링크까지 싹 다 잡아드릴게유! ✨"</div>""", unsafe_allow_html=True)

st.markdown('<p class="main-title">👗 AI 스타일 가이드</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">실시간 비디오 분석으로 완성하는 당신만의 퍼스널 룩</p>', unsafe_allow_html=True)

# --- 섹션 1: 업로드 영역 ---
c_v, c_u = st.columns([1.2, 1])
with c_v:
    embed_url = "https://www.youtube.com/embed/1vE5QSvW_Vg?rel=0&modestbranding=1"
    video_html = f'<iframe width="100%" height="500" src="{embed_url}" frameborder="0" allowfullscreen></iframe>'
    components.html(video_html, height=520)

with c_u:
    st.markdown("#### ⚙️ 설정 및 업로드")
    gender = st.radio("1️⃣ 모델 성별 선택", ["여성", "남성"], horizontal=True)
    uploaded_file = st.file_uploader("2️⃣ 영상 업로드", type=["mp4", "mov", "avi"])
    if uploaded_file:
        st.success("✅ 준비 완료!")

# --- 섹션 2: 분석 실행 ---
if uploaded_file:
    if st.button("🚀 AI 스타일 분석 시작", use_container_width=True, type="primary"):
        with st.status("🔍 분석 중...", expanded=True) as status:
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                video_part = {"mime_type": uploaded_file.type, "data": uploaded_file.read()}
                prompt = f"""
                Analyze {gender}'s style. Focus on Korean elegant fashion.
                Start with [성별: {gender}].
                # 1. 스타일 페르소나 # 2. 체형 강점 # 3. 퍼스널 컬러 # 4. 스타일링 팁
                [중요] 마지막에 다음 형식을 포함하세요: # 쇼핑 키워드: [키워드1, 키워드2, 키워드3]
                """
                response = model.generate_content([prompt, video_part])
                st.session_state.analysis_result = response.text
                status.update(label="✅ 분석 완료!", state="complete")
            except Exception as e:
                st.error(f"오류: {e}")

# --- 섹션 3: 결과 및 수익화 (에러 해결 구간) ---
if 'analysis_result' in st.session_state:
    st.divider()
    st.subheader("📊 AI 프리미엄 스타일 리포트")
    st.markdown(st.session_state.analysis_result)

    if st.button(f"🎨 {gender} 추천 스타일 화보 생성", use_container_width=True):
        with st.spinner("화보 제작 중..."):
            img_url = generate_style_visual(st.session_state.analysis_result, gender)
            st.session_state.pictorial_url = img_url

    if 'pictorial_url' in st.session_state and st.session_state.pictorial_url:
        st.image(st.session_state.pictorial_url, caption="AI 맞춤형 화보")
        
        # [동적 쇼핑 링크 & AF 아이디 연동]
        keywords = extract_shop_keywords(st.session_state.analysis_result)
        st.markdown("#### 🛍️ AI 추천 아이템 바로 구매하기")
        cols = st.columns(len(keywords))
        
        for i, keyword in enumerate(keywords):
            with cols[i]:
                # 1. target_url 정의
                target_url = f"https://www.coupang.com/np/search?q={keyword.replace(' ', '+')}"
                # 2. 형님의 AF 아이디 포함된 딥링크 생성 (AF5326630)
                shop_url = f"https://link.coupang.com/re/AFFSDP?lptag=AF5326630&subid=stylescan&pageKey={target_url}"
                st.link_button(f"🛒 {keyword}", shop_url, use_container_width=True)
        
        st.caption("※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.")

        # [고화질 결제 섹션]
        st.write("") # 187번 줄 들여쓰기 에러 수정됨
        with st.container(border=True):
            st.markdown("#### 🖼️ 고화질 화보 소장")
            d_col1, d_col2 = st.columns([2, 1])
            with d_col1: st.write("워터마크 없는 HD 이미지를 간직하세요.")
            with d_col2:
                if st.button("💰 구매 (990원)", use_container_width=True):
                    st.toast("결제 시스템 연동 중...")

    # [PDF 저장]
    st.divider()
    input_pw = st.text_input("리포트 비밀번호 (카페 확인)", type="password")
    if input_pw == "style77":
        st.download_button("📄 PDF 다운로드", data=create_pdf_file(st.session_state.analysis_result), file_name="Report.pdf")

st.markdown("<br><p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>Copyright 2026. Microhard All rights reserved.</p>", unsafe_allow_html=True)
