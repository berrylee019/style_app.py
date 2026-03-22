import streamlit as st
import google.generativeai as genai
import hmac
import hashlib
import requests
from datetime import datetime
import urllib.parse
import re
import datetime

# 1. API 설정
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
    ACCESS_KEY = st.secrets["COUPANG_ACCESS_KEY"]
    SECRET_KEY = st.secrets["COUPANG_SECRET_KEY"]
except:
    st.error("API 키 설정이 필요합니다! .streamlit/secrets.toml을 확인해 주셔요.")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="centered")

# --- [함수] 쿠팡 API 엔진 ---
def get_naver_products(keyword):

    # 1. 네이버 API 설정 (Secrets에서 가져오기)
    client_id = st.secrets["NAVER_CLIENT_ID"]
    client_secret = st.secrets["NAVER_CLIENT_SECRET"]
    
    # 2. API 주소 (쇼핑 검색)
    url = f"https://openapi.naver.com/v1/search/shop.json?query={keyword}&display=5&sort=sim"
    
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('items', []) # 네이버는 'items'라는 이름으로 줍니다.
        else:
            st.sidebar.error(f"⚠️ 네이버 에러: {response.status_code}")
            return []
    except Exception as e:
        st.sidebar.error(f"⚠️ 코드 실행 에러: {e}")
        return []

# --- [함수] 키워드 추출 ---
def extract_shop_keywords(text):
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[?(.*?)\]?$', text, re.MULTILINE)
    if match:
        return [k.strip().replace('[', '').replace(']', '') for k in match.group(1).split(',')]
    return ["트렌디 패션"]

# --- UI 레이아웃 ---
st.title("👗 AI 스타일 가이드 PRO")

gender = st.radio("성별 선택", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("영상 업로드 (5초 내외 권장)", type=["mp4", "mov"])

# --- [STEP 1] 영상 분석 (분석만 수행) ---
if uploaded_file:
    # 1단계 버튼
    if st.button("1단계: 스타일 분석하기", key="btn_step1"):
        # 분석 로직
        pass
        
    if st.button("2단계: 추천 상품 실시간 매칭", key="btn_step2"):
        with st.spinner("네이버 쇼핑에서 최적의 상품을 찾는 중..."):
            # 쿠팡 대신 네이버 함수 호출!
            products = get_naver_products(keyword) 
            
            if products:
                for item in products:
                    # 네이버는 title에 <b> 태그가 섞여 있어 제거해주는 게 좋습니다.
                    clean_title = item['title'].replace('<b>', '').replace('</b>', '')
                    st.write(f"🎁 {clean_title}")
                    st.write(f"🔗 [상품 보러가기]({item['link']})")
            else:
                st.warning("상품을 찾지 못했습니다.")

# --- [STEP 2] 결과 출력 및 상품 매칭 ---
if st.session_state.get('analysis_done'):
    st.divider()
    st.subheader("📊 AI 스타일 리포트")
    st.info(st.session_state.analysis_result)
    
    # 분석이 끝난 후에만 '상품 찾기' 버튼이 등장합니다. (부하 분산)
    if st.button("2단계: 추천 상품 실시간 매칭"):
        with st.spinner("쿠팡에서 최적의 상품을 찾는 중입니다..."):
            # 여기서 keyword가 세션 상태에 잘 저장되어 있는지 확인!
            target_keyword = st.session_state.get('search_keyword', '반팔티') 
            products = get_coupang_products(target_keyword)
            
            if products:
                st.success(f"총 {len(products)}개의 상품을 찾았습니다!")
                st.session_state['coupang_products'] = products
            else:
                st.warning("앗, 상품을 가져오지 못했습니다. 사이드바의 쿠팡 원본 데이터를 확인해 보세요!")

# --- [STEP 3] 최종 상품 카드 출력 ---
if st.session_state.get('products_done'):
    st.divider()
    st.subheader("🛒 실시간 추천 아이템")

    products = st.session_state.get('products', [])
    
    if len(products) > 0:
            # 상품이 1개라도 있을 때만 컬럼을 만듭니다.
            cols = st.columns(len(products))
            for i, item in enumerate(products):
                with cols[i]:
                    with st.container(border=True):
                        st.image(item['productImage'], use_container_width=True)
                        st.markdown(f"**{item['productName'][:18]}...**")
                        st.markdown(f"**{item['productPrice']:,}원**")
                        st.link_button("최저가 확인", item['productUrl'], use_container_width=True)
    else:
        # 상품을 못 찾았을 때의 예외 처리
        st.warning("앗, 현재 키워드와 일치하는 상품이 쿠팡에 없네요. 다른 스타일로 다시 시도해 보셔요!")
        
    st.caption("※ 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.")
