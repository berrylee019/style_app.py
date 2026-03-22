import streamlit as st
import google.generativeai as genai
import hmac
import hashlib
import requests
from datetime import datetime
import urllib.parse
import re

# 1. API 설정
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
    ACCESS_KEY = st.secrets["COUPANG_ACCESS_KEY"]
    SECRET_KEY = st.secrets["COUPANG_SECRET_KEY"]
except:
    st.error("API 키 설정이 필요합니다! .streamlit/secrets.toml을 확인해 주셔요.")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="centered")

# --- [함수] 쿠팡 API 엔진 ---
def get_coupang_products(keyword):
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        URL = f"/v2/providers/affiliate_open_api/apis/openapi/v1/products/search?keyword={urllib.parse.quote(keyword)}&limit=1"
        now = datetime.utcnow().strftime('%y%m%dT%H%M%SZ')
        message = now + "GET" + URL
        signature = hmac.new(SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
        authorization = f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={now}, signature={signature}"
        headers = {"Authorization": authorization, "Content-Type": "application/json;charset=UTF-8"}
        response = requests.get(DOMAIN + URL, headers=headers, timeout=5)
        res_json = response.json()
        return res_json['data']['productData'] if res_json.get('data') else []
    except: return []

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
    if st.button("🚀 1단계: 스타일 분석 시작", use_container_width=True, type="primary"):
        with st.spinner("AI가 영상을 분석 중입니다... 잠시만 기다려 주세요."):
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                video_part = {"mime_type": uploaded_file.type, "data": uploaded_file.read()}
                prompt = f"Analyze {gender}'s style. Write a brief report. End with '# 쇼핑 키워드: [Item1, Item2, Item3]' in Korean."
                
                response = model.generate_content([prompt, video_part], request_options={"timeout": 300})
                st.session_state.analysis_result = response.text
                st.session_state.analysis_done = True # 분석 완료 플래그
                st.rerun() # 결과 출력을 위해 화면 갱신
            except Exception as e:
                st.error(f"분석 중 오류: {e}")

# --- [STEP 2] 결과 출력 및 상품 매칭 ---
if st.session_state.get('analysis_done'):
    st.divider()
    st.subheader("📊 AI 스타일 리포트")
    st.info(st.session_state.analysis_result)
    
    # 분석이 끝난 후에만 '상품 찾기' 버튼이 등장합니다. (부하 분산)
    if st.button("🛍️ 2단계: 추천 상품 실시간 매칭", use_container_width=True):
        with st.spinner("쿠팡에서 최적의 상품을 찾는 중..."):
            keywords = extract_shop_keywords(st.session_state.analysis_result)
            found_products = []
            for kw in keywords:
                res = get_coupang_products(f"{gender} {kw}")
                if res: found_products.append(res[0])
            st.session_state.products = found_products
            st.session_state.products_done = True

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
