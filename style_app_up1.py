import streamlit as st
import google.generativeai as genai
import requests
import re
import urllib.parse
import time

# 1. API 설정
try:
    # Gemini 설정
    genai.configure(api_key=st.secrets["MY_API_KEY"])
    
    # 네이버 API 설정 (Secrets에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 필수)
    NAVER_ID = st.secrets["NAVER_CLIENT_ID"]
    NAVER_SECRET = st.secrets["NAVER_CLIENT_SECRET"]
except Exception as e:
    st.error(f"⚠️ API 키 설정 오류! Secrets를 확인해 주셔요: {e}")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="centered")

# --- [함수] 네이버 쇼핑 API 엔진 ---
def get_naver_products(keyword):
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/shop.json?query={encoded_keyword}&display=4&sort=sim"
    
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

# --- [STEP 1] 분석 로직 (Gemini AI 탑재) ---
if uploaded_file:
    # 1단계 버튼: 영상 분석 실행
    if st.button("1단계: 스타일 분석하기", key="analysis_btn"):
        with st.spinner(f"AI가 {gender} 스타일 영상을 정밀 분석 중입니다..."):
            try:
                # 영상 바이트 읽기
                video_data = uploaded_file.read()
                
                # Gemini 모델 설정 (비전 기능 사용)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # 성별 맞춤 프롬프트
                prompt = f"""
                영상 속 인물의 스타일을 분석해서 패션 리포트를 작성해줘.
                사용자가 선택한 성별은 '{gender}'이야.
                반드시 {gender} 패션 관점에서 분석하고, 마지막에는 아래 형식을 꼭 지켜줘.
                
                형식:
                # 쇼핑 키워드: [{gender} 스타일 키워드]
                """
                
                # AI 호출 (영상 데이터와 프롬프트 전달)
                response = model.generate_content([
                    prompt,
                    {"mime_type": "video/mp4", "data": video_data}
                ])
                
                # 결과 세션 저장
                st.session_state['analysis_result'] = response.text
                st.session_state['search_keyword'] = extract_shop_keywords(response.text)
                st.session_state['analysis_done'] = True
                st.rerun() # 화면 갱신
                
            except Exception as e:
                st.error(f"⚠️ AI 분석 중 에러가 발생했습니다: {e}")

# --- [STEP 2] 결과 출력 및 네이버 상품 매칭 ---
if st.session_state.get('analysis_done'):
    st.divider()
    st.subheader("📊 AI 스타일 리포트")
    st.info(st.session_state.analysis_result)
    
    if st.button("2단계: 추천 상품 실시간 매칭", key="matching_step_btn"):
        base_keyword = st.session_state.get('search_keyword', '패션아이템')
        # 성별을 키워드 앞에 강제 결합 (여성 영상에 남성 옷 방지)
        target_keyword = f"{gender} {base_keyword}"
        
        with st.spinner(f"'{target_keyword}' 상품을 찾는 중..."):
            products = get_naver_products(target_keyword)
            
            if products:
                st.session_state['naver_products'] = products
                st.session_state['products_done'] = True
                st.success(f"'{target_keyword}' 매칭 성공!")
            else:
                st.warning("네이버 쇼핑에서 상품을 찾지 못했습니다.")

# --- [STEP 3] 최종 상품 카드 출력 ---
if st.session_state.get('products_done'):
    st.divider()
    st.subheader(f"🛒 {gender} 실시간 추천 아이템")

    products = st.session_state.get('naver_products', [])
    
    if products:
        cols = st.columns(len(products))
        for i, item in enumerate(products):
            with cols[i]:
                with st.container(border=True):
                    # 이미지 출력
                    st.image(item['image'], use_container_width=True)
                    
                    # 제목 정화 (<b> 제거 및 성별 필터링)
                    clean_title = item['title'].replace('<b>', '').replace('</b>', '')
                    
                    # 여성 선택 시 남성 전용 상품이 섞이면 스킵
                    if gender == "여성" and ("남성" in clean_title or "공용" in clean_title) and "여성" not in clean_title:
                        st.caption("남성/공용 상품 제외됨")
                    else:
                        st.markdown(f"**{clean_title[:15]}...**")
                        price = int(item['lprice']) if item['lprice'].isdigit() else 0
                        st.markdown(f"**{price:,}원**")
                        st.link_button("최저가 확인", item['link'], use_container_width=True)
    
    st.caption(f"※ {gender} 스타일 맞춤형 검색 결과입니다.")
