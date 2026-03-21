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

# --- [함수] 쇼핑 키워드 추출 로직 (정규식 강화) ---
def extract_shop_keywords(text):
    try:
        # 다양한 공백이나 대괄호 형식을 모두 잡을 수 있도록 개선
        match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[?(.*?)\]?$', text, re.MULTILINE)
        if match:
            raw_keywords = match.group(1).split(',')
            keywords = [k.strip().replace('[', '').replace(']', '') for k in raw_keywords]
            return [k for k in keywords if k][:3]
    except:
        pass
    return ["기능성 티셔츠", "린넨 팬츠", "데일리 룩"]

# --- [함수] PDF 생성 ---
def create_pdf_file(text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=text_content.encode('latin-1', 'ignore').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# --- [함수] 화보 생성 ---
def generate_style_visual(style_description, selected_gender):
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        base_desc = "Korean female model" if selected_gender == "여성" else "Korean male model"
        full_prompt = f"{base_desc}, sophisticated fashion, Style: {style_description[:120]}. 4k, studio lighting."
        response = client.images.generate(model="dall-e-3", prompt=full_prompt, size="1024x1024", n=1)
        return response.data[0].url
    except:
        return None

# --- UI 상단 레이아웃 ---
col_img, col_txt = st.columns([1, 4])
with col_img:
    if os.path.exists("styley.png"): st.image("styley.png", width=110)
    else: st.write("🖼️")
with col_txt:
    st.markdown('<div style="background: #E1F5FE; border-radius: 15px; padding: 15px; border: 1px solid #B3E5FC;">반갑습니다 형님! 오늘 베스트 룩과 수익 링크까지 싹 다 잡아드릴게유! ✨</div>', unsafe_allow_html=True)

st.markdown('<p class="main-title">👗 AI 스타일 가이드</p>', unsafe_allow_html=True)

# --- 섹션 1: 업로드 영역 ---
c_v, c_u = st.columns([1.2, 1])
with c_v:
    video_html = '<iframe width="100%" height="500" src="https://www.youtube.com/embed/1vE5QSvW_Vg" frameborder="0" allowfullscreen></iframe>'
    components.html(video_html, height=520)
with c_u:
    gender = st.radio("1️⃣ 모델 성별 선택", ["여성", "남성"], horizontal=True)
    uploaded_file = st.file_uploader("2️⃣ 영상 업로드", type=["mp4", "mov", "avi"])

# --- 섹션 2: 분석 실행 ---
if uploaded_file:
    if st.button("🚀 AI 스타일 분석 시작", use_container_width=True, type="primary"):
        with st.status("🔍 분석 중...") as status:
            try:
                # 모델명 gemini-1.5-flash로 수정완료
                model = genai.GenerativeModel('gemini-2.5-flash')
                video_part = {"mime_type": uploaded_file.type, "data": uploaded_file.read()}
                prompt = f"""
                당신은 최고의 AI 스타일리스트입니다. {gender} 사용자의 영상을 분석하여 다음 규격에 맞춰 상세 리포트를 작성하세요.
                1. 스타일 페르소나 / 2. 체형 강점 / 3. 퍼스널 컬러 / 4. 스타일링 팁
                마지막 줄 형식 엄수: # 쇼핑 키워드: [키워드1, 키워드2, 키워드3]
                """
                response = model.generate_content([prompt, video_part])
                st.session_state.analysis_result = response.text
                status.update(label="✅ 분석 완료!", state="complete")
            except Exception as e:
                st.error(f"오류: {e}")

# --- 섹션 3: 결과 출력 및 쿠팡 버튼 (무조건 출력 로직) ---
if 'analysis_result' in st.session_state:
    st.divider()
    st.markdown(st.session_state.analysis_result)

    # 1. 쇼핑 버튼 생성 (리포트 바로 아래 배치)
    keywords = extract_shop_keywords(st.session_state.analysis_result)
    st.markdown("#### 🛍️ AI 추천 아이템 바로 구매하기")
    cols = st.columns(len(keywords))
    
    for i, keyword in enumerate(keywords):
        with cols[i]:
            # 검색 정확도를 위해 성별 추가
            full_query = f"{gender} {keyword}".strip()
            # 이중 인코딩으로 유실 방지
            target_url = f"https://www.coupang.com/np/search?q={urllib.parse.quote(full_query)}"
            final_url = urllib.parse.quote(target_url, safe='')
            # 최종 수익 링크 (AF5326630)
            shop_url = f"https://link.coupang.com/re/PCSWSDP?lptag=AF5326630&subid=stylescan&pageKey={final_url}"
            st.link_button(f"🛒 {keyword}", shop_url, use_container_width=True)

    st.caption("※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.")

    # 2. 화보 생성 섹션
    if st.button(f"🎨 {gender} 추천 스타일 화보 생성", use_container_width=True):
        with st.spinner("화보 제작 중..."):
            st.session_state.pictorial_url = generate_style_visual(st.session_state.analysis_result, gender)
    
    if 'pictorial_url' in st.session_state and st.session_state.pictorial_url:
        st.image(st.session_state.pictorial_url, caption="AI 맞춤형 화보")

    # PDF 저장 등 기타 기능
    input_pw = st.text_input("리포트 비밀번호", type="password")
    if input_pw == "style77":
        st.download_button("📄 PDF 다운로드", data=create_pdf_file(st.session_state.analysis_result), file_name="Report.pdf")

st.markdown("<br><p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>Copyright 2026. Microhard All rights reserved.</p>", unsafe_allow_html=True)
