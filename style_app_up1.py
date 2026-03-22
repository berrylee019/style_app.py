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
    import hmac
    import hashlib
    import datetime
    import requests
    import urllib.parse
    import streamlit as st

    # 1. 설정값 (SECRET에서 가져오기)
    DOMAIN = "https://api-gateway.coupang.com"
    URL = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    METHOD = "GET"
    
    # 2. 파라미터 구성
    params = {"keyword": keyword, "limit": 1}
    query_string = urllib.parse.urlencode(params)
    full_path = f"{URL}?{query_string}"

    try:
        # 3. [핵심 변경] 쿠팡이 가장 선호하는 GMT 날짜 형식
        # 예: 260323T124500Z (YYMMDDTHHMMSSZ)
        now = datetime.datetime.now(datetime.timezone.utc)
        datetime_str = now.strftime('%y%m%dT%H%M%SZ')
        
        # 4. HMAC 메시지 조립
        message = datetime_str + METHOD + full_path
        
        # 5. 서명 생성
        signature = hmac.new(
            SECRET_KEY.encode('utf-8'), 
            message.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()
        
        # 6. [결정적 차이] Authorization 헤더의 공백과 형식을 공식 문서와 100% 일치시킴
        # 주의: 'signed-date'와 'signature' 사이의 공백, 콤마 위치 확인!
        authorization = (
            f"CEA algorithm=HmacSHA256, "
            f"access-key={ACCESS_KEY}, "
            f"signed-date={datetime_str}, "
            f"signature={signature}"
        )
        
        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json;charset=UTF-8"
        }
        
        # 7. 호출
        response = requests.get(DOMAIN + full_path, headers=headers, timeout=10)
        data = response.json()

        # 사이드바 확인용
        with st.sidebar:
            st.write("🔍 **쿠팡 최종 응답 데이터:**")
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
