import streamlit as st
import google.generativeai as genai
import urllib.parse
import re

# 1. 페이지 설정 및 API 연결
st.set_page_config(page_title="AI 스타일 가이드", layout="centered")

try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("API 키를 확인해주세요!")

# --- [함수] 쇼핑 키워드 추출 (오류 방지용 기본값 포함) ---
def extract_shop_keywords(text):
    # 정규식으로 '# 쇼핑 키워드: [값]' 형태를 찾음
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[(.*?)\]', text)
    if match:
        return [k.strip() for k in match.group(1).split(',')][:3]
    return ["기능성 티셔츠", "슬랙스", "린넨 셔츠"] # 추출 실패 시 강제 출력

# --- UI 레이아웃 ---
st.title("👗 AI 스타일 가이드 (수익형)")
gender = st.radio("성별 선택", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("영상을 업로드하세요", type=["mp4", "mov"])

# --- 분석 실행 ---
if uploaded_file:
    if st.button("🚀 AI 분석 시작", use_container_width=True, type="primary"):
        with st.spinner("AI 분석 중..."):
            model = genai.GenerativeModel('gemini-2.5-flash')
            video_part = {"mime_type": uploaded_file.type, "data": uploaded_file.read()}
            
            # 분석 리포트와 키워드를 동시에 요청
            prompt = f"Analyze this {gender}'s style. Provide a report with styling tips. At the end, add '# 쇼핑 키워드: [Item1, Item2, Item3]'"
            
            response = model.generate_content([prompt, video_part])
            st.session_state.analysis_result = response.text

# --- 결과 출력 영역 (이 부분이 무조건 실행되어야 합니다) ---
if 'analysis_result' in st.session_state:
    st.divider()
    st.markdown("### 📊 AI 스타일 리포트")
    st.write(st.session_state.analysis_result)
    
    # [쇼핑 버튼 생성 로직] - 리포트가 있으면 무조건 실행
    st.markdown("#### 🛍️ AI 추천 아이템 (쿠팡)")
    keywords = extract_shop_keywords(st.session_state.analysis_result)
    
    cols = st.columns(len(keywords))
    for i, keyword in enumerate(keywords):
        with cols[i]:
            # [수익 링크 생성] 형님 아이디: AF5326630
            search_query = f"{gender} {keyword}".strip()
            encoded_query = urllib.parse.quote(search_query)
            
            # 쿠팡 검색창에 키워드를 꽂아넣는 가장 단순하고 강력한 방식
            # NONAMEP 리다이렉터를 사용하여 검색어 유실 방지
            target_url = f"https://www.coupang.com/np/search?q={encoded_query}"
            encoded_target = urllib.parse.quote(target_url, safe='')
            shop_url = f"https://link.coupang.com/re/NONAMEP?lptag=AF5326630&subid=stylescan&pageKey={encoded_target}"
            
            st.link_button(f"🛒 {keyword}", shop_url, use_container_width=True)
            
    st.caption("※ 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다. (ID: AF5326630)")
