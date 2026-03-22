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
def get_coupang_products(keyword):

    try:
        DOMAIN = "https://api-gateway.coupang.com"
        # 1. 경로와 쿼리를 분리해서 관리해야 에러가 안 납니다.
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        query = f"keyword={urllib.parse.quote(keyword)}&limit=1"
        URL = f"{path}?{query}"
        
        # 2. 시간 생성 (UTC)
        now = datetime.datetime.now(datetime.timezone.utc).strftime('%y%m%d%H%M%S')
        method = "GET"
        
        # 3. [핵심] HMAC 메시지 구성 (DOMAIN을 제외한 'URL' 전체가 포함되어야 함)
        # 중요: URL 변수 안에 path와 query가 모두 포함된 상태여야 합니다.
        message = now + method + URL
        
        signature = hmac.new(
            SECRET_KEY.encode('utf-8'), 
            message.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()
        
        # 4. 헤더 설정 (공백 하나하나가 중요합니다)
        authorization = f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={now}, signature={signature}"
        headers = {
            "Authorization": authorization, 
            "Content-Type": "application/json;charset=UTF-8"
        }
        
        # 5. 실제 요청
        response = requests.get(DOMAIN + URL, headers=headers, timeout=10)
        data = response.json()

        # 디버깅용 출력
        with st.sidebar:
            st.write("🔍 **쿠팡 응답 데이터 원본:**")
            st.json(data)
            
        if 'data' in data and 'productData' in data['data']:
            return data['data']['productData']
        else:
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
