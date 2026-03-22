import streamlit as st
import google.generativeai as genai
import hmac
import hashlib
import requests
import json
from datetime import datetime
import urllib.parse
import re
import os

# 1. API 설정 및 보안 키 로드
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
    ACCESS_KEY = st.secrets["COUPANG_ACCESS_KEY"]
    SECRET_KEY = st.secrets["COUPANG_SECRET_KEY"]
except:
    st.error("API 키 설정이 필요합니다! .streamlit/secrets.toml에 COUPANG_ACCESS_KEY와 SECRET_KEY를 넣어주세요.")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="centered")

# --- [함수] 쿠팡 API 호출 엔진 (HMAC 서명 로직 포함) ---
def get_coupang_products(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    URL = f"/v2/providers/affiliate_open_api/apis/openapi/v1/products/search?keyword={urllib.parse.quote(keyword)}&limit=3"
    METHOD = "GET"
    
    # 시간 생성 (GMT 기준)
    now = datetime.utcnow().strftime('%y%m%dT%H%M%SZ')
    
    # 서명(Signature) 생성
    message = now + METHOD + URL
    signature = hmac.new(SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    
    authorization = f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={now}, signature={signature}"
    
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json;charset=UTF-8"
    }
    
    try:
        response = requests.get(DOMAIN + URL, headers=headers, timeout=10)
        res_json = response.json()
        if res_json.get('data'):
            return res_json['data']['productData']
        return []
    except Exception as e:
        print(f"쿠팡 API 호출 오류: {e}")
        return []

# --- [함수] 쇼핑 키워드 추출 ---
def extract_shop_keywords(text):
    try:
        match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[?(.*?)\]?$', text, re.MULTILINE)
        if match:
            raw = match.group(1).split(',')
            return [k.strip().replace('[', '').replace(']', '') for k in raw][:3]
    except: pass
    return ["데일리 룩", "트렌디 패션"]

# --- UI 상단 ---
st.title("👗 AI 스타일 가이드 PRO")
st.info("형님, 이제 API 연동으로 실제 상품 정보를 실시간으로 긁어옵니다!")

gender = st.radio("성별 선택", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("영상 업로드 (10초 내외)", type=["mp4", "mov"])

# --- 분석 및 상품 출력 ---
if uploaded_file:
    if st.button("🚀 AI 스타일 분석 및 상품 찾기", use_container_width=True, type="primary"):
        with st.status("🔍 분석 및 상품 검색 중...") as status:
            try:
                # 1. Gemini 스타일 분석
                model = genai.GenerativeModel('gemini-1.5-flash')
                video_part = {"mime_type": uploaded_file.type, "data": uploaded_file.read()}
                prompt = f"Analyze {gender}'s style. Report briefly. Add '# 쇼핑 키워드: [Item1, Item2]' in Korean at the end."
                
                response = model.generate_content([prompt, video_part])
                st.session_state.analysis_result = response.text
                
                # 2. 키워드 추출 및 쿠팡 상품 검색
                keywords = extract_shop_keywords(response.text)
                all_products = []
                for kw in keywords:
                    # 성별을 붙여서 검색 정확도 높임
                    products = get_coupang_products(f"{gender} {kw}")
                    if products:
                        all_products.append(products[0]) # 각 키워드별 1등 상품만
                
                st.session_state.products = all_products
                status.update(label="✅ 분석 및 상품 매칭 완료!", state="complete")
            except Exception as e:
                st.error(f"오류 발생: {e}")

# --- 결과 화면 출력 ---
if 'analysis_result' in st.session_state:
    st.divider()
    st.markdown("### 📊 AI 스타일 리포트")
    st.write(st.session_state.analysis_result)
    
    st.divider()
    st.markdown("### 🛍️ AI 추천 실시간 핫템")
    
    if st.session_state.get('products'):
        cols = st.columns(len(st.session_state.products))
        for i, item in enumerate(st.session_state.products):
            with cols[i]:
                # 상품 카드 구현
                st.image(item['productImage'], use_container_width=True)
                st.markdown(f"**{item['productName'][:20]}...**")
                st.markdown(f"### {item['productPrice']:,}원")
                # 쿠팡 파트너스 API가 주는 주소는 100% 수익 링크입니다.
                st.link_button("🚀 최저가 확인", item['productUrl'], use_container_width=True)
    else:
        st.warning("아직 매칭된 상품이 없습니다. 키워드를 다시 확인해 주세요.")

    st.caption("※ 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.")
