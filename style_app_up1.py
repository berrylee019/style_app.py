import streamlit as st
import google.generativeai as genai
import requests
import re
import urllib.parse

# 1. API 설정
try:
    # Gemini 설정
    genai.configure(api_key=st.secrets["MY_API_KEY"])
    
    # 네이버 API 설정 (Secrets에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET이 있어야 함)
    NAVER_ID = st.secrets["NAVER_CLIENT_ID"]
    NAVER_SECRET = st.secrets["NAVER_CLIENT_SECRET"]
except Exception as e:
    st.error(f"⚠️ API 키 설정 오류! Secrets를 확인해 주셔요: {e}")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="centered")

# --- [함수] 네이버 쇼핑 API 엔진 ---
def get_naver_products(keyword):
    # API 주소 (쇼핑 검색)
    url = f"https://openapi.naver.com/v1/search/shop.json?query={urllib.parse.quote(keyword)}&display=4&sort=sim"
    
    headers = {
        "X-Naver-Client-Id": NAVER_ID,
        "X-Naver-Client-Secret": NAVER_SECRET
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('items', [])
        else:
            st.sidebar.error(f"⚠️ 네이버 에러 코드: {response.status_code}")
            return []
    except Exception as e:
        st.sidebar.error(f"⚠️ 네이버 호출 에러: {e}")
        return []

# --- [함수] 키워드 추출 ---
def extract_shop_keywords(text):
    # 텍스트에서 # 쇼핑 키워드: [키워드] 형태를 찾아냅니다.
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[?(.*?)\]?$', text, re.MULTILINE)
    if match:
        keywords = [k.strip().replace('[', '').replace(']', '') for k in match.group(1).split(',')]
        return keywords[0] if keywords else "트렌디 패션"
    return "트렌디 패션"

# --- UI 레이아웃 ---
st.title("👗 AI 스타일 가이드 PRO")

gender = st.radio("성별 선택", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("영상 업로드 (5초 내외 권장)", type=["mp4", "mov"])

# --- [STEP 1] 분석 로직 (세션 상태 활용) ---
if uploaded_file:
    if st.button("1단계: 스타일 분석하기", key="analysis_btn"):
        with st.spinner("AI가 영상을 분석 중입니다..."):
            # (여기에 원래 있던 Gemini 영상 분석 로직이 들어갑니다)
            # 예시를 위해 가짜 데이터를 넣었습니다. 형님의 실제 분석 로직을 여기 넣으셔요.
            fake_result = "오늘의 추천 스타일은 '세미 오버핏'입니다. \n\n# 쇼핑 키워드: [남성 반팔티]"
            
            st.session_state['analysis_result'] = fake_result
            st.session_state['search_keyword'] = extract_shop_keywords(fake_result)
            st.session_state['analysis_done'] = True

# --- [STEP 2] 결과 출력 및 네이버 상품 매칭 ---
if st.session_state.get('analysis_done'):
    st.divider()
    st.subheader("📊 AI 스타일 리포트")
    st.info(st.session_state.analysis_result)
    
    # 중복 ID 에러 방지를 위해 고유한 key 부여
    if st.button("2단계: 추천 상품 실시간 매칭", key="matching_step_btn"):
        target_keyword = st.session_state.get('search_keyword', '패션아이템')
        
        with st.spinner(f"'{target_keyword}' 상품을 찾는 중..."):
            products = get_naver_products(target_keyword)
            
            if products:
                st.session_state['naver_products'] = products
                st.session_state['products_done'] = True
                st.success(f"'{target_keyword}' 매칭 성공!")
            else:
                st.warning("네이버 쇼pping에서 상품을 찾지 못했습니다. 키워드를 확인해 보세요.")

# --- [STEP 3] 최종 상품 카드 출력 (네이버 버전) ---
if st.session_state.get('products_done'):
    st.divider()
    st.subheader("🛒 네이버 실시간 추천 아이템")

    products = st.session_state.get('naver_products', [])
    
    if products:
        # 네이버 결과는 보통 4~5개이므로 2개씩 2줄로 배치하거나 4개를 한 줄로 배치
        cols = st.columns(len(products))
        for i, item in enumerate(products):
            with cols[i]:
                with st.container(border=True):
                    # 네이버는 'image' 키를 사용합니다.
                    st.image(item['image'], use_container_width=True)
                    
                    # 제목에서 <b> 태그 제거
                    clean_title = item['title'].replace('<b>', '').replace('</b>', '')
                    st.markdown(f"**{clean_title[:15]}...**")
                    
                    # 가격 표시 (네이버는 lprice가 가격입니다)
                    price = int(item['lprice']) if item['lprice'].isdigit() else 0
                    st.markdown(f"**{price:,}원**")
                    
                    # 상품 링크
                    st.link_button("최저가 확인", item['link'], use_container_width=True)
    
    st.caption("※ 네이버 쇼핑 검색 결과입니다.")
