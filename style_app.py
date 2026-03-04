import streamlit as st
import google.generativeai as genai
import time
from fpdf import FPDF
from datetime import datetime

# 1. API 키 설정
genai.configure(api_key=st.secrets["MY_API_KEY"])

# 페이지 설정
st.set_page_config(page_title="AI 스타일 가이드", page_icon="👗", layout="centered")

# --- 커스텀 CSS (세련된 디자인 적용) ---
st.markdown("""
    <style>
    /* 메인 배경 및 폰트 설정 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
   
    /* 헤더 스타일링 */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 2rem;
    }
   
    /* 카드 스타일 UI */
    .tip-card {
        background-color: #f8fafc;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #3B82F6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        height: 100%;
    }
    .tip-header {
        font-weight: 700;
        color: #1E40AF;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
   
    /* 버튼 스타일 커스텀 */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        background-color: #2563EB;
        color: white;
        font-weight: 700;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #1E40AF;
        border: none;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 헤더 섹션 (이미지 + 인사말풍선) ---
col_img, col_txt = st.columns([1, 4]) # 이미지와 말풍선 비율 조절

with col_img:
    try:
        st.image("styley.png", width=110)
    except:
        st.write("🖼️") # 이미지 없을 때 대비

with col_txt:
    # 스타일리 전용 말풍선 디자인 (CSS 포함)
    st.markdown("""
        <div style="position: relative; background: #E1F5FE; border-radius: 15px; padding: 15px; margin-top: 10px; border: 1px solid #B3E5FC;">
            <strong style="color: #0288D1; font-size: 1.1rem;">Styley:</strong><br>
            <span style="color: #333;">"반가워요! 오늘도 당신의 스타일을 완벽하게 분석해 드릴게요. <br>준비되셨으면 아래에 영상을 올려주세요! ✨"</span>
            <div style="position: absolute; left: -10px; top: 20px; width: 0; height: 0; border-top: 10px solid transparent; border-bottom: 10px solid transparent; border-right: 10px solid #E1F5FE;"></div>
        </div>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">👗 AI 스타일 가이드</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">실시간 비디오 분석으로 완성하는 당신만의 퍼스널 룩</p>', unsafe_allow_html=True)

# --- 촬영 꿀팁 섹션 (카드형 레이아웃) ---
st.markdown("#### 🎥 더 정확한 분석을 위한 촬영 꿀팁")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
        <div class="tip-card">
            <div class="tip-header">👤 1. 전신 샷 필수</div>
            머리부터 발끝까지 화면에 다 들어와야 정확한 비율 분석이 가능해요.
        </div><br>
        <div class="tip-card">
            <div class="tip-header">🔄 2. 360도 회전</div>
            천천히 한 바퀴 돌아주시면 입체적인 핏 가이드를 드릴 수 있습니다.
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="tip-card">
            <div class="tip-header">💡 3. 밝은 조명</div>
            조명이 밝아야 옷의 질감과 퍼스널 컬러를 정확히 잡아내요.
        </div><br>
        <div class="tip-card">
            <div class="tip-header">⏱️ 4. 5~15초 권장</div>
            분석 최적화 시간입니다. 너무 길면 업로드 속도가 느려질 수 있어요.
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 파일 업로드 섹션 ---
uploaded_file = st.file_uploader("분석할 영상을 업로드하세요 (MP4, MOV, AVI)", type=["mp4", "mov", "avi"])

# Gemini 모델 설정 (1.5 Flash가 현재 안정적입니다)
model = genai.GenerativeModel('gemini-2.5-flash')
prompt = """
당신은 세계 최고의 패션 스타일리스트이자 퍼스널 쇼퍼입니다.
업로드된 영상을 분석하여 다음 항목을 포함한 '프리미엄 스타일 리포트'를 작성하세요.

1. 스타일 페르소나: 현재 스타일을 정의하는 멋진 키워드
2. 체형 및 핏 분석: 옷의 실루엣이 체형과 얼마나 잘 어울리는지 분석
3. 컬러 매칭: 착용한 옷의 색상 조화와 추천 퍼스널 컬러
4. 개선 제안: 더 완벽한 룩을 위한 한 가지 포인트 조언

모든 내용은 한국어로, 아주 친절하고 전문적인 톤으로 작성하세요.
중요한 제목 앞에는 #을 붙여서 구분해 주세요.
"""

if uploaded_file is not None:
    st.divider()
    st.video(uploaded_file)
   
    if 'analysis_result' not in st.session_state:
        if st.button("✨ AI 스타일 분석 시작"):
            with st.status("🔍 AI가 스타일을 정밀 분석 중입니다...", expanded=True) as status:
                bytes_data = uploaded_file.getvalue()
                # 비디오 분석을 위한 설정
                video_part = {"mime_type": uploaded_file.type, "data": bytes_data}
               
                try:
                    response = model.generate_content([prompt, video_part])
                    st.session_state.analysis_result = response.text
                    status.update(label="✅ 분석 완료!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"분석 중 오류 발생: {e}")

    # --- 분석 결과 출력 ---
    if 'analysis_result' in st.session_state:
        st.success("분석이 완료되었습니다!")
        st.subheader("📊 AI 프리미엄 스타일 리포트")
        st.markdown(st.session_state.analysis_result)
        st.balloons()

        # PDF 생성 함수
    def create_pdf_file(text_content):
        pdf = FPDF()
        pdf.add_page()
        
        # 폰트 파일이 있는지 확인하고 로드
        font_path = "NanumGothic.ttf" # 파일이 같은 폴더에 있어야 함!
        
        if os.path.exists(font_path):
            pdf.add_font('Nanum', '', font_path, unicode=True)
            pdf.set_font('Nanum', '', 12)
        else:
            # 폰트가 없으면 기본 Arial로 영어만 나오게 (에러 방지용)
            pdf.set_font("Arial", size=12)
            text_content = "Font file missing. Please check NanumGothic.ttf on server."
    
        pdf.set_text_color(31, 41, 55)
        pdf.multi_cell(0, 10, txt=text_content)
        
        # latin-1 에러 방지를 위해 'dest=S' 대신 바이트스트림 직접 처리
        return pdf.output(dest='S').encode('latin-1', errors='replace')

        # --- 네이버 카페 연동 섹션 ---
        st.divider()
        st.markdown("### 🚀 스타일 업그레이드 본부")
       
        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.info("💡 **카페 회원 전용 혜택**\n- 분석 리포트 PDF 평생 소장\n- 체형별 코디 가이드북 즉시 증정\n- 매월 베스트 드레서 이벤트 참여")
            st.link_button("☕ 네이버 카페 가입하고 비번 확인", "https://cafe.naver.com/stylely")
       
        with c2:
            input_pw = st.text_input("카페 비밀번호를 입력하세요", type="password")
            if input_pw == "style77":
                try:
                    pdf_data = create_pdf_file(st.session_state.analysis_result)
                    st.download_button(
                        label="📄 PDF 리포트 다운로드",
                        data=pdf_data,
                        file_name=f"Style_Report_{datetime.now().strftime('%m%d')}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.warning("PDF 생성 중 글꼴 설정을 확인해 주세요.")

st.markdown("<br><br><p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>Copyright 2026. Microhard All rights reserved.</p>", unsafe_allow_html=True)


