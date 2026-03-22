import streamlit as st
import google.generativeai as genai
import urllib.parse
import re
import os

# 1. API 설정
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("API 키가 없습니다! secrets.toml을 확인해 주세요.")

# --- [함수] 쇼핑 키워드 추출 (에러 방지용) ---
def extract_shop_keywords(text):
    try:
        match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[?(.*?)\]?$', text, re.MULTILINE)
        if match:
            raw = match.group(1).split(',')
            keywords = [k.strip().replace('[', '').replace(']', '') for k in raw]
            return [k for k in keywords if k][:3]
    except:
        pass
    return ["기능성 반팔티", "와이드 팬츠", "데일리 코디"] # 기본값

# --- 메인 레이아웃 ---
st.title("👗 AI 스타일 가이드")
gender = st.radio("성별 선택", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("영상 업로드 (10초 내외 권장)", type=["mp4", "mov"])

# --- 분석 실행 섹션 ---
if uploaded_file:
    if st.button("🚀 AI 스타일 분석 시작", use_container_width=True, type="primary"):
        # 이전 결과 초기화
        if 'analysis_result' in st.session_state:
            del st.session_state.analysis_result
            
        with st.status("🔍 AI가 영상을 정밀 분석 중입니다...", expanded=True) as status:
            try:
                # [중요] 모델명을 안정적인 1.5-flash로 고정
                model = genai.GenerativeModel('gemini-2.5-flash')
                video_data = uploaded_file.read()
                video_part = {"mime_type": uploaded_file.type, "data": video_data}
                
                # 프롬프트를 간결하게 하여 처리 속도 향상
                prompt = f"""
                Analyze the {gender}'s style in this video. 
                Write a brief report (Persona, Strengths, Tips). 
                At the end, add '# 쇼핑 키워드: [Keyword1, Keyword2, Keyword3]' in Korean.
                """
                
                # [핵심] 타임아웃을 10분으로 늘려 멈춤 현상 방지
                response = model.generate_content(
                    [prompt, video_part], 
                    request_options={"timeout": 600}
                )
                
                st.session_state.analysis_result = response.text
                status.update(label="✅ 분석 완료!", state="complete")
                
            except Exception as e:
                st.error(f"분석 중 멈춤/오류 발생: {e}")
                st.info("💡 팁: 영상을 5~10초로 더 짧게 잘라서 다시 시도해 보세요!")

# --- [결과 및 쿠팡 버튼] 섹션 ---
# 분석 결과가 세션에 저장되어 있다면 '무조건' 화면에 그립니다.
if 'analysis_result' in st.session_state:
    st.divider()
    st.subheader("📊 AI 스타일 리포트")
    st.markdown(st.session_state.analysis_result)

    # 쇼핑 버튼 생성
    keywords = extract_shop_keywords(st.session_state.analysis_result)
    st.markdown("#### 🛍️ AI 추천 아이템 바로 구매하기")
    
    cols = st.columns(len(keywords))
    for i, keyword in enumerate(keywords):
        with cols[i]:
            # 1. 실제 쿠팡 검색 결과 주소를 먼저 만듭니다.
            # 예: https://www.coupang.com/np/search?q=남성+린넨+셔츠
            search_url = f"https://www.coupang.com/np/search?q={urllib.parse.quote(f'{gender} {keyword}')}"
            
            # 2. 이 주소 전체를 다시 한 번 안전하게 인코딩합니다. (가장 중요!)
            # 특수문자(:, /, ?)가 살아있으면 쿠팡 리다이렉터가 주소를 잘라먹습니다.
            encoded_full_url = urllib.parse.quote(search_url, safe='')
            
            # 3. 쿠팡 파트너스 'PC/모바일 공용 딥링크' 구조에 넣습니다.
            # PCSWSDP는 주소(pageKey)를 그대로 목적지로 보내주는 강력한 리다이렉터입니다.
            shop_url = f"https://link.coupang.com/re/PCSWSDP?lptag=AF5326630&subid=stylescan&pageKey={encoded_full_url}"
            
            st.link_button(f"🛒 {keyword}", shop_url, use_container_width=True)
            
    st.caption("※ 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다. (ID: AF5326630)")
