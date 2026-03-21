import streamlit as st
import google.generativeai as genai
import urllib.parse
import re
import os

# --- [함수] 쇼핑 키워드 추출 (정규식 보강) ---
def extract_shop_keywords(text):
    try:
        # AI가 대괄호 없이 출력하거나 공백이 있어도 잡아낼 수 있도록 정규식 강화
        match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[?(.*?)\]?$', text, re.MULTILINE)
        if match:
            # 쉼표로 구분된 키워드들을 깨끗하게 정리
            raw_keywords = match.group(1).split(',')
            keywords = [k.strip().replace('[', '').replace(']', '') for k in raw_keywords]
            return [k for k in keywords if k][:3] # 비어있지 않은 키워드 최대 3개
    except Exception as e:
        st.error(f"키워드 추출 중 오류: {e}")
    return ["기능성 티셔츠", "린넨 팬츠", "데일리 룩"] # 추출 실패 시 기본값

# ... (기존 설정 코드들: API 설정, CSS 등은 그대로 유지) ...

# --- 섹션 3: 결과 및 수익화 (이 부분이 핵심입니다!) ---
if 'analysis_result' in st.session_state:
    st.divider()
    st.subheader("📊 AI 프리미엄 스타일 리포트")
    st.markdown(st.session_state.analysis_result)

    # 화보 생성 버튼 등 (기존 코드 유지)
    if st.button(f"🎨 {gender} 추천 스타일 화보 생성", use_container_width=True):
        with st.spinner("화보 제작 중..."):
            # generate_style_visual 함수 호출 로직
            pass

    # [수익화 섹션] 리포트 결과가 있다면 무조건 실행되도록 위치 조정
    st.write("---")
    st.markdown("#### 🛍️ AI 추천 아이템 바로 구매하기")
    
    # 1. 키워드 추출
    keywords = extract_shop_keywords(st.session_state.analysis_result)
    
    # 2. 버튼 출력을 위한 컬럼 생성
    cols = st.columns(len(keywords))
    
    for i, keyword in enumerate(keywords):
        with cols[i]:
            # [최종 정밀 인코딩]
            # 검색어 앞에 성별을 붙여 정확도 극대화
            search_term = f"{gender} {keyword}".strip()
            
            # 1단계: 검색 결과 주소 생성 및 인코딩
            encoded_query = urllib.parse.quote(search_term)
            target_url = f"https://www.coupang.com/np/search?q={encoded_query}"
            
            # 2단계: 전체 주소를 pageKey용으로 2차 인코딩 (안전빵)
            # safe='' 를 주어야 : / ? 등의 특수문자가 모두 인코딩되어 유실되지 않습니다.
            final_encoded_url = urllib.parse.quote(target_url, safe='')
            
            # 3단계: 형님의 AF5326630 아이디가 박힌 최종 숏링크 구조
            shop_url = f"https://link.coupang.com/re/PCSWSDP?lptag=AF5326630&subid=stylescan&pageKey={final_encoded_url}"
            
            # 4단계: 버튼 출력 (이 코드가 실행되면 버튼이 무조건 보입니다!)
            st.link_button(f"🛒 {keyword}", shop_url, use_container_width=True)
            
    st.caption("※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다. (ID: AF5326630)")
