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

# 1. API 설정 및 보안 키 로드 (오류 방지)
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
    ACCESS_KEY = st.secrets["COUPANG_ACCESS_KEY"]
    SECRET_KEY = st.secrets["COUPANG_SECRET_KEY"]
except Exception as e:
    st.error(f"⚠️ API 키 로드 실패: {e}")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="centered")

# --- [함수] 쿠팡 API 호출 엔진 (안전성 강화) ---
def get_coupang_products(keyword):
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        URL = f"/v2/providers/affiliate_open_api/apis/openapi/v1/products/search?keyword={urllib.parse.quote(keyword)}&limit=1"
        METHOD = "GET"
        
        now = datetime.utcnow().strftime('%y%m%dT%H%M%SZ')
        message = now + METHOD + URL
        signature = hmac.new(SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
        
        authorization = f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={now}, signature={signature}"
        
        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json;charset=UTF-8"
        }
        
        # 타임아웃을 짧게 주어 앱 멈춤 방지
        response = requests.get(DOMAIN + URL, headers=headers, timeout=5)
        res_json = response.json()
        
        if res_json.get('data') and res_json['data'].get('productData'):
            return res_json['data']['productData']
        return []
    except Exception as e:
        st.warning(f"쿠팡 검색 중 경미한 오류: {keyword} 결과 없음")
        return []

# --- [함수] 쇼핑 키워드 추출 ---
def extract_shop_keywords(text):
    try:
        match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[?(.*?)\]?$', text, re.MULTILINE)
        if match:
            raw = match.group(1).split(',')
            return [k.strip().replace('[', '').replace(']', '') for k in raw][:3]
    except: pass
    return ["데일리 룩", "패션 아이템"]

# --- UI 레이아웃 ---
st.title("👗 AI 스타일 가이드 PRO")

gender = st.radio("성별 선택", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("영상 업로드 (5~10초 권장)", type=["mp4", "mov"])

# --- 분석 실행 버튼 ---
if uploaded_file:
    if st.button("🚀 스타일 분석 및 상품 찾기", use_container_width=True, type="primary"):
        with st.status("🔍 분석 중... (최대 30초 소요)") as status:
            try:
                # 1. Gemini 분석 (타임아웃 설정)
                model = genai.GenerativeModel('gemini-1.5-flash')
                video_part = {"mime_type": uploaded_file.type, "data": uploaded_file.read()}
                prompt = f"Analyze {gender}'s fashion. Report briefly (Persona, Tips). End with '# 쇼핑 키워드: [Item1, Item2]' in Korean."
                
                response = model.generate_content([prompt, video_part], request_options={"timeout": 300})
                st.session_state.analysis_result = response.text
                
                # 2. 키워드 기반 쿠팡 상품 검색
                keywords = extract_shop_keywords(response.text)
                found_products = []
                for kw in keywords:
                    # 성별 포함 검색으로 정확도UP
                    res = get_coupang_products(f"{gender} {kw}")
                    if res: found_products.append(res[0])
                
                st.session_state.products = found_products
                status.update(label="✅ 분석 완료!", state="complete")
            except Exception as e:
                st.error(f"분석 중 멈춤 발생: {e}. 영상을 더 짧게 잘라서 시도해 보세요.")

# --- 결과 출력 (세션 기반) ---
if 'analysis_result' in st.session_state:
    st.divider()
    st.markdown("### 📊 AI 스타일 리포트")
    st.info(st.session_state.analysis_result)
    
    if st.session_state.get('products'):
        st.divider()
        st.markdown("### 🛍️ AI 추천 실시간 핫템")
        cols = st.columns(len(st.session_state.products))
        for i, item in enumerate(st.session_state.products):
            with cols[i]:
                with st.container(border=True):
                    st.image(item['productImage'], use_container_width=True)
                    # 상품명 짧게 자르기
                    short_name = item['productName'][:15] + "..."
                    st.markdown(f"**{short_name}**")
                    st.markdown(f"**{item['productPrice']:,}원**")
                    st.link_button("최저가 확인", item['productUrl'], use_container_width=True)
        st.caption("※ 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.")
