import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from datetime import datetime
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
                # [프롬프트 수정] 쇼핑몰 검색 정확도를 높이는 로직 추가
                prompt = f"""
                당신은 최고의 AI 패션 스타일리스트입니다. {gender} 사용자의 영상을 분석하여 다음 규격에 맞춰 리포트를 작성하세요.
                반드시 모든 항목을 상세히 작성해야 합니다.

                1. 스타일 페르소나: 사용자의 현재 스타일을 정의하세요.
                2. 체형 강점 분석: 영상에서 보이는 체형의 장점을 서술하세요.
                3. 퍼스널 컬러 제안: 가장 잘 어울리는 색상군을 추천하세요.
                4. 스타일링 팁: 더 멋져 보일 수 있는 구체적인 코디법을 제시하세요.

                [데이터 추출 규칙]
                리포트 맨 마지막 줄에 반드시 아래 형식을 한 줄로 추가하세요. 
                (검색어는 '소재+아이템' 형태의 구체적 명사여야 함)
                # 쇼핑 키워드: [키워드1, 키워드2, 키워드3]
                """
                response = model.generate_content([prompt, video_part])
                st.session_state.analysis_result = response.text
                status.update(label="✅ 분석 완료!", state="complete")
            except Exception as e:
                st.error(f"오류: {e}")

# --- 섹션 3: 결과 및 수익화 (링크 유실 방지 로직) ---
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
        
        import urllib.parse
        keywords = extract_shop_keywords(st.session_state.analysis_result)
        
        st.markdown("#### 🛍️ AI 추천 아이템 바로 구매하기")
        cols = st.columns(len(keywords))
        

        for i, keyword in enumerate(keywords):
            with cols[i]:
                # 1. 검색어 생성 (예: 남성 카키 기능성 반팔티)
                search_query = f"{gender} {keyword}".strip()
                
                # 2. [핵심] 쿠팡 파트너스 '검색 전용' 다이렉트 주소 구조
                # 이 주소는 중간 리다이렉트 없이 쿠팡 검색 엔진으로 키워드를 바로 쏩니다.
                # lptag(형님 아이디)와 q(검색어)를 나란히 배치하는 것이 포인트입니다.
                
                encoded_keyword = urllib.parse.quote(search_query)
                
                # [수정된 주소 구조] 
                # link.coupang.com 대신 'a.coupang.com' 또는 아래의 직접 호출 방식을 사용합니다.
                shop_url = (
                    f"https://link.coupang.com/re/PCSWSDP?"
                    f"lptag=AF5326630"
                    f"&subid=stylescan"
                    f"&pageKey=https%3A%2F%2Fwww.coupang.com%2Fnp%2Fsearch%3Fq%3D{encoded_keyword}"
                )
                
                # 3. 버튼 생성
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
