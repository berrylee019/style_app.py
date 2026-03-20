import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from datetime import datetime
import os
import re
import openai

# 1. API 키 및 페이지 설정
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("API 키 설정이 필요합니다! .streamlit/secrets.toml을 확인해 주셔요.")

st.set_page_config(page_title="AI 스타일 가이드", page_icon="👗", layout="centered")

# --- 커스텀 CSS (기존 디자인 유지) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .main-title { font-size: 2.5rem; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 0.5rem; }
    .sub-title { font-size: 1.1rem; color: #64748B; text-align: center; margin-bottom: 2rem; }
    .tip-card { 
        background-color: #f8fafc; border-radius: 10px; padding: 20px; 
        border-left: 5px solid #3B82F6; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
        height: 100%; margin-bottom: 10px;
    }
    .tip-header { font-weight: 700; color: #1E40AF; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3rem; 
        background-color: #2563EB; color: white; font-weight: 700; border: none; transition: all 0.3s; 
    }
    .stButton>button:hover { background-color: #1E40AF; transform: translateY(-2px); }
    </style>
    """, unsafe_allow_html=True)

# --- [함수] PDF 생성 엔진 ---
def create_pdf_file(text_content):
    def clean_text(text):
        text = text.replace('**', '')
        text = text.replace('* ', ' • ')
        text = re.sub(r'\.{2,}', '.', text)
        text = text.replace('___', '')
        return text.strip()

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()
    epw = pdf.w - 20
    
    font_path = "NanumGothic.ttf"
    if os.path.exists(font_path):
        pdf.add_font('Nanum', '', font_path)
        pdf.set_font('Nanum', '', 12)
    else:
        pdf.set_font("Arial", size=12)

    pdf.set_fill_color(28, 35, 49)
    pdf.rect(0, 0, 210, 45, 'F')
    if os.path.exists("styley.png"):
        pdf.image("styley.png", 15, 12, 22)
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(45, 18)
    pdf.set_font('Nanum', '', 24)
    pdf.cell(0, 10, "STYLE ANALYSIS REPORT", ln=True)
    pdf.set_font('Nanum', '', 10)
    pdf.set_xy(45, 28)
    pdf.cell(0, 10, f"Issued by Microhard AI Lab | {datetime.now().strftime('%Y.%m.%d')}", ln=True)

    pdf.set_y(55)
    pdf.set_text_color(44, 62, 80)
    lines = text_content.split('\n')
    for line in lines:
        raw_line = line.strip()
        if not raw_line:
            pdf.ln(4); continue
        if raw_line.startswith('#'):
            pdf.ln(6)
            title_text = clean_text(raw_line.replace('#', ''))
            pdf.set_font('Nanum', '', 15)
            pdf.set_text_color(30, 58, 138)
            pdf.cell(epw, 10, title_text, ln=True)
            pdf.line(10, pdf.get_y(), 60, pdf.get_y())
            pdf.ln(4)
        else:
            pdf.set_font('Nanum', '', 11)
            pdf.set_text_color(44, 62, 80)
            pdf.multi_cell(epw, 7, txt=clean_text(raw_line))
            pdf.ln(1)
    return pdf.output()

# --- [함수] 업그레이드된 비주얼 생성 엔진 (성별 반영) ---
def generate_style_visual(style_description, selected_gender):
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        st.info(f"👗 {selected_gender} 모델을 위한 맞춤형 화보를 AI가 제작 중입니다...")
        
        # 성별 영어 변환
        gender_en = "female" if selected_gender == "여성" else "male"
        
        # 성별이 반영된 정교한 프롬프트
        full_prompt = (f"A professional {gender_en} fashion model wearing {style_description}, "
                       f"high-end fashion editorial photography, magazine style, "
                       f"luxury lighting, 4k resolution, stylish background")
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        st.error(f"비주얼 생성 중 오류: {e}")
        return None

# --- UI 레이아웃 시작 ---
col_img, col_txt = st.columns([1, 4])
with col_img:
    if os.path.exists("styley.png"): st.image("styley.png", width=110)
    else: st.write("🖼️")

with col_txt:
    st.markdown("""
        <div style="position: relative; background: #E1F5FE; border-radius: 15px; padding: 15px; margin-top: 10px; border: 1px solid #B3E5FC;">
            <strong style="color: #0288D1; font-size: 1.1rem;">Styley:</strong><br>
            <span style="color: #333;">"반가워요 형님! 오늘 형님의 성별과 스타일을 딱 맞춰서 베스트 룩을 시각화해드릴게유! ✨"</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">👗 AI 스타일 가이드</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">실시간 비디오 분석으로 완성하는 당신만의 퍼스널 룩</p>', unsafe_allow_html=True)

# --- 업로드 및 성별 선택 섹션 ---
st.markdown("#### 📹 촬영 가이드 및 정보 입력")
c_v, c_u = st.columns([1.2, 1])

with c_v:
    if os.path.exists("sample_guide.mp4"): st.video("sample_guide.mp4")
    else: st.info("가이드 영상을 준비해 주셔요!")

with c_u:
    uploaded_file = st.file_uploader("영상을 업로드하세요", type=["mp4", "mov", "avi"])
    # [업그레이드 1] 성별 선택 UI 추가
    gender = st.radio("시각화할 모델 성별 선택", ["여성", "남성"], horizontal=True)
    
    if uploaded_file:
        st.success("영상 준비 완료!")

# --- 꿀팁 섹션 ---
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="tip-card"><div class="tip-header">👤 1. 전신 샷 필수</div>머리부터 발끝까지 화면에 들어와야 해요.</div><br><div class="tip-card"><div class="tip-header">🔄 2. 360도 회전</div>천천히 한 바퀴 돌아주세요.</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="tip-card"><div class="tip-header">💡 3. 밝은 조명</div>조명이 밝아야 컬러를 정확히 잡아요.</div><br><div class="tip-card"><div class="tip-header">⏱️ 4. 5~15초 권장</div>너무 길면 업로드가 느려질 수 있어요.</div>', unsafe_allow_html=True)

# --- 분석 및 시각화 로직 ---
if uploaded_file is not None:
    st.divider()
    
    # 1. 스타일 분석 버튼
    if 'analysis_result' not in st.session_state:
        if st.button("✨ AI 스타일 분석 시작"):
            with st.status("🔍 AI가 스타일을 정밀 분석 중입니다...", expanded=True) as status:
                try:
                    model = genai.GenerativeModel('gemini-2.0-flash') # 최신 모델명으로 수정
                    video_part = {"mime_type": uploaded_file.type, "data": uploaded_file.read()}
                    prompt = "패션 컨설턴트로서 영상을 분석해 1.스타일 페르소나, 2.체형 강점, 3.컬러 제안, 4.팁 순으로 리포트해줘. 마크다운 기호 없이 깔끔하게."
                    response = model.generate_content([prompt, video_part])
                    st.session_state.analysis_result = response.text
                    status.update(label="✅ 분석 완료!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"분석 오류: {e}")

    # 2. 결과 출력 및 시각화 버튼
    if 'analysis_result' in st.session_state:
        st.subheader("📊 AI 프리미엄 스타일 리포트")
        st.markdown(st.session_state.analysis_result)
        
        st.divider()
        # [업그레이드 3] 버튼 로직 수정 (성별 전달)
        if st.button("🎨 내 추천 스타일 화보로 보기"):
            # 분석 결과에서 핵심 키워드 약 100자 추출하여 전달
            img_url = generate_style_visual(st.session_state.analysis_result[:150], gender)
            if img_url:
                st.image(img_url, caption=f"AI가 제안하는 {gender} 모델 코디 샘플입니다, 형님!")
                st.balloons()

        # 3. 수익화(PDF 다운로드) 섹션
        st.divider()
        st.markdown("### 🚀 스타일 업그레이드 본부")
        res_c1, res_c2 = st.columns([1.2, 1])
        with res_c1:
            st.info("💡 **카페 회원 혜택**\n- 리포트 PDF 저장 가능\n- 코디 가이드북 즉시 증정")
            st.link_button("☕ 카페에서 비번 확인하기", "https://cafe.naver.com/stylely")
        with res_c2:
            input_pw = st.text_input("카페 비밀번호를 입력하세요", type="password")
            if input_pw == "style77":
                pdf_data = create_pdf_file(st.session_state.analysis_result)
                st.download_button(
                    label="📄 PDF 리포트 다운로드",
                    data=bytes(pdf_data),
                    file_name=f"Style_Report_{datetime.now().strftime('%m%d')}.pdf",
                    mime="application/pdf"
                )

st.markdown("<br><br><p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>Copyright 2026. Microhard All rights reserved.</p>", unsafe_allow_html=True)
