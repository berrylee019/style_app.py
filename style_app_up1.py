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
        st.info(f"👗 {selected_gender} 고객님을 위한 단아하고 품격 있는 화보를 제작 중입니다...")
        
        # 1. 성별 및 분위기별 맞춤 베이스 묘사 (핵심 단어: Conservative, Slender, Graceful)
        if selected_gender == "여성":
            # 'Modest'와 'Conservative'는 노출을 원천 봉쇄하는 마법의 단어입니다.
            base_desc = (
                "An elegant and graceful female model with a slender and natural build. "
                "She has a sophisticated and modest demeanor, wearing conservative and high-end fashion. "
            )
        else:
            # 'Refined silhouette'와 'Lean'은 과한 근육 대신 슬림한 멋을 줍니다.
            base_desc = (
                "A distinguished and mature male model with a lean and refined silhouette. "
                "He exudes a calm and professional aura, wearing classic tailored premium clothing. "
            )

        # 2. 분석 결과에서 '노출'이나 '신체' 관련 단어가 있을 경우를 대비해 앞부분만 추출
        refined_keywords = style_description[:80] 

        # 3. 최종 프롬프트 조합 (검열을 피하기 위해 NO... 대신 긍정문으로만 구성)
        full_prompt = (
            f"{base_desc} The outfit is based on: {refined_keywords}. "
            f"High-end editorial photography, soft and natural studio lighting, "
            f"classic and calm background, focused on fabric texture and overall style, "
            f"natural and comfortable pose, 4k resolution."
        )
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        # 만약 또 정책 위반이 뜨면 사용자에게 부드럽게 안내
        st.error("이미지 생성 정책으로 인해 일부 표현이 조정되었습니다. 다시 한번 시도해 주셔요!")
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
            <span style="color: #333;">"반갑습니다! 오늘 당신의 성별과 스타일을 딱 맞춰서 베스트 룩을 시각화해드릴게유! ✨"</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">👗 AI 스타일 가이드</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">실시간 비디오 분석으로 완성하는 당신만의 퍼스널 룩</p>', unsafe_allow_html=True)

# --- 업로드 및 성별 선택 섹션 ---
st.markdown("")
c_v, c_u = st.columns([1.2, 1])


# ... 기존 코드 중 c_v, c_u 나누는 부분 ...

with c_v:
    st.markdown('<h4 style="color: #1a73e8; margin-top: 0;">📹 촬영 가이드 및 정보 입력</h4>', unsafe_allow_html=True)
    
    # 형님이 주신 유튜브 쇼츠 주소입니다.
    # 쇼츠 주소도 st.video에서 바로 인식합니다!
    video_url = "https://youtube.com/shorts/watch?v=1vE5QSvW_Vg"
    
    try:
        # 유튜브 영상을 메인 화면 왼쪽 컬럼에 꽉 차게 배치
        st.video(video_url)
        st.caption("▲ 위 가이드 영상을 시청하신 후 촬영해 주세요.")
    except Exception as e:
        st.info("📺 가이드 영상을 참조하세요! (유튜브 연결 확인 중)")

with c_u:
    # 오른쪽 컬럼: 파일 업로드 및 성별 선택
    uploaded_file = st.file_uploader("영상을 업로드하세요", type=["mp4", "mov", "avi"])
    gender = st.radio("시각화할 모델 성별 선택", ["여성", "남성"], horizontal=True)
    
    if uploaded_file:
        st.success("✅ 영상 준비 완료!")

# --- 꿀팁 섹션 ---
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="tip-card"><div class="tip-header">👤 1. 전신 샷 필수</div>머리부터 발끝까지 화면에 들어와야 해요.</div><br><div class="tip-card"><div class="tip-header">🔄 2. 360도 회전</div>천천히 한 바퀴 돌아주세요.</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="tip-card"><div class="tip-header">💡 3. 밝은 조명</div>조명이 밝아야 컬러를 정확히 잡아요.</div><br><div class="tip-card"><div class="tip-header">⏱️ 4. 5~15초 권장</div>너무 길면 업로드가 느려질 수 있어요.</div>', unsafe_allow_html=True)

# --- 분석 실행 로직 (수정된 버전) ---
if uploaded_file is not None:
    st.divider()
    if 'analysis_result' not in st.session_state:
        if st.button("✨ AI 스타일 분석 시작"):
            with st.status("🔍 AI가 성별과 스타일을 정밀 분석 중입니다...", expanded=True) as status:
                # --- 분석 실행 로직 (인종 및 체형 특징 강화 버전) ---
                try:
                    # 1. 모델 설정
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    video_part = {"mime_type": uploaded_file.type, "data": uploaded_file.read()}
                    
                    # [강화된 프롬프트] 인종(Korean), 분위기(Elegant/Distinguished), 체형(Slender) 주입
                    prompt = f"""
                    이 영상의 주인공은 {gender}이며, 한국인(Korean/East Asian)입니다. 
                    반드시 {gender}의 관점에서, '한국인 모델' 특유의 우아함과 세련미를 중심으로 분석하세요.
                
                    분석 규칙:
                    1. 인종 및 성별 확정: 주인공은 '동양인(Korean)'이며 '{gender}'입니다. 서구적인 특징보다는 단아하고 세련된 동양적 미감을 강조하세요.
                    2. 분위기 및 연령: 매우 '우아하고(Elegant)' '지적인(Sophisticated)' 분위기를 가진 성숙한 인물로 가정합니다. 
                    3. 체형 분석: 비현실적인 근육이나 노출은 배제하고, '슬림하고(Slender)' '매끈한(Lean)' 실루엣을 중심으로 분석하세요.
                    4. 금기어: '{'남성적', '보이시' if gender == '여성' else '여성적', '페미닌'}' 표현을 절대 금지합니다.
                    5. 답변 시작: 반드시 첫 줄에 '[성별: {gender}]'이라고 적고 시작하세요.
                
                    항목별 리포트 내용:
                    # 1. 스타일 페르소나 (기품 있는 현대 한국 {gender}의 세련미)
                    # 2. 체형 강점 분석 (슬림한 라인과 동양적 비율의 조화)
                    # 3. 퍼스널 컬러 제안
                    # 4. 오늘의 스타일링 팁 (노출 없는 고급스러운 럭셔리 룩)
                
                    모든 문장은 전문적인 패션 비즈니스 용어를 사용하고, 마침표로 끝내주세요.
                    """
                    
                    response = model.generate_content([prompt, video_part])
                    st.session_state.analysis_result = response.text
                    
                    # [자동 감지] 분석 결과에서 성별 추출
                    if "[성별: 여성]" in response.text:
                        st.session_state.detected_gender = "여성"
                    elif "[성별: 남성]" in response.text:
                        st.session_state.detected_gender = "남성"
                    else:
                        st.session_state.detected_gender = gender # 선택한 기본값 사용
                        
                    status.update(label=f"✅ {st.session_state.detected_gender} 스타일 분석 완료!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"분석 오류: {e}")

    # --- 시각화 버튼 부분 (수정) ---
    if 'analysis_result' in st.session_state:
        st.subheader("📊 AI 프리미엄 스타일 리포트")
        st.markdown(st.session_state.analysis_result)
        
        st.divider()
        # [자동화] 이제 gender 변수 대신 AI가 찾은 detected_gender를 씁니다.
        current_gender = st.session_state.get('detected_gender', '여성')
        
        if st.button(f"🎨 {current_gender} 추천 스타일 화보로 보기"):
            # 분석 결과에서 성별 표시 부분을 제외하고 코디 정보만 추출
            clean_description = st.session_state.analysis_result.replace("[성별: 여성]", "").replace("[성별: 남성]", "")
            img_url = generate_style_visual(clean_description[:150], current_gender)
            if img_url:
                st.image(img_url, caption=f"AI가 감지한 {current_gender} 맞춤 코디 화보입니다!")
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
