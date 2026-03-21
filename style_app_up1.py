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

# --- [함수] PDF 및 비주얼 생성 엔진 ---
def create_pdf_file(text_content):
    # (기존 PDF 생성 로직 유지)
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
        
        response = client.images.generate(
            model="dall-e-3", prompt=full_prompt, size="1024x1024", n=1
        )
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
        <strong style="color: #0288D1;">Styley:</strong> "반갑습니다 형님! 오늘 베스트 룩을 뽑아드릴게유! ✨"</div>""", unsafe_allow_html=True)

st.markdown('<p class="main-title">👗 AI 스타일 가이드</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">실시간 비디오 분석으로 완성하는 당신만의 퍼스널 룩</p>', unsafe_allow_html=True)

# --- 섹션 1: 가이드 및 업로드 ---
c_v, c_u = st.columns([1.2, 1])

with c_v:
    st.markdown('<h4 style="color: #1a73e8; margin-top: 0;">📹 촬영 가이드 및 정보 입력</h4>', unsafe_allow_html=True)
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

# --- 섹션 2: 분석 실행 ---
if uploaded_file:
    if st.button("🚀 AI 스타일 분석 시작", use_container_width=True, type="primary"):
        with st.status("🔍 분석 중...", expanded=True) as status:
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                video_part = {"mime_type": uploaded_file.type, "data": uploaded_file.read()}
                prompt = f"Analyze {gender}'s style. Focus on Korean elegant fashion. Start with [성별: {gender}]."
                response = model.generate_content([prompt, video_part])
                st.session_state.analysis_result = response.text
                status.update(label="✅ 분석 완료!", state="complete")
            except Exception as e:
                st.error(f"오류: {e}")

# --- 섹션 3: 결과 출력 및 수익화 ---
if 'analysis_result' in st.session_state:
    st.divider()
    st.subheader("📊 AI 프리미엄 스타일 리포트")
    st.markdown(st.session_state.analysis_result)

    # [수익화 버튼 섹션]
    st.divider()
    curr_gender = gender # 혹은 분석 결과에서 추출

    if st.button(f"🎨 {curr_gender} 추천 스타일 화보로 보기", use_container_width=True):
        with st.spinner("AI 화보 생성 중..."):
            img_url = generate_style_visual(st.session_state.analysis_result, curr_gender)
            st.session_state.pictorial_url = img_url

    # 화보가 생성된 후 보여줄 수익화 영역
    if 'pictorial_url' in st.session_state and st.session_state.pictorial_url:
        st.image(st.session_state.pictorial_url, caption="AI 맞춤형 스타일 화보")
        
        # --- [Step 1] 제휴 마케팅 ---
        st.markdown("#### 🛍️ 화보 속 아이템 쇼핑하기")
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            st.link_button("👕 비슷한 상의 구매하기", "https://link.coupang.com/a/d8BH1i", use_container_width=True)
        with s_col2:
            st.link_button("👖 비슷한 하의 구매하기", "https://link.coupang.com/a/d8BJks", use_container_width=True)

        # --- [Step 2] 고화질 소장 결제 ---
        st.write("")
        with st.container(border=True):
            st.markdown("#### 🖼️ 워터마크 없는 고화질 화보 소장")
            d_col1, d_col2 = st.columns([2, 1])
            with d_col1:
                st.write("나만의 인생 스타일을 고화질(HD) 이미지로 간직하세요.")
            with d_col2:
                if st.button("💰 고화질 구매 (990원)", use_container_width=True):
                    st.toast("💳 결제 창으로 이동합니다...", icon="⏳")

    # [기존 카페 비번/PDF 섹션]
    st.divider()
    st.markdown("### 🚀 리포트 소장하기")
    res_c1, res_c2 = st.columns([1.2, 1])
    with res_c1:
        st.info("카페에서 비밀번호를 확인 후 PDF를 다운로드하세요.")
        st.link_button("☕ 카페 바로가기", "https://cafe.naver.com/stylely")
    with res_c2:
        input_pw = st.text_input("비밀번호", type="password")
        if input_pw == "style77":
            st.download_button("📄 PDF 다운로드", data=create_pdf_file(st.session_state.analysis_result), file_name="Report.pdf")

st.markdown("<br><p style='text-align: center; color: #94a3b8;'>Copyright 2026. Microhard All rights reserved.</p>", unsafe_allow_html=True)
