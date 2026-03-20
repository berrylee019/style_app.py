import streamlit as st
import replicate
import os
from PIL import Image
import requests
from io import BytesIO

# 1. 페이지 설정 및 API 키 확인
st.set_page_config(page_title="StyleScan AI: 가상 피팅", page_icon="👕", layout="wide")

try:
    REPLICATE_API_TOKEN = st.secrets["REPLICATE_API_TOKEN"]
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
except:
    st.error("Replicate API 토큰이 필요합니다! secrets.toml을 확인해 주셔요.")

# --- 커스텀 CSS ---
st.markdown("""
    <style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; text-align: center; }
    .stButton>button { width: 100%; background-color: #EF4444; color: white; font-weight: 700; border: none; height: 3.5rem; }
    .stButton>button:hover { background-color: #DC2626; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">👕 AI 가상 피팅: Try-On Lab</p>', unsafe_allow_html=True)
st.write("내 사진을 올리고 원하는 옷을 입어보세요. 형님께 딱 맞는 핏을 찾아드립니다!")

# --- UI 레이아웃 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ 내 사진 업로드 (상체/전신)")
    human_file = st.file_uploader("정면 사진을 올려주세요", type=["jpg", "jpeg", "png"], key="human")
    if human_file:
        st.image(human_file, caption="피팅 모델(형님)", use_container_width=True)

with col2:
    st.subheader("2️⃣ 입어볼 옷 사진 업로드")
    garment_file = st.file_uploader("입고 싶은 옷 사진 (바닥샷/모델샷)", type=["jpg", "jpeg", "png"], key="garment")
    if garment_file:
        st.image(garment_file, caption="선택한 아이템", use_container_width=True)

# --- 가상 피팅 실행 ---
if human_file and garment_file:
    st.divider()
    if st.button("🚀 AI 가상 피팅 시작하기"):
        with st.spinner("✨ AI가 옷을 정교하게 입히고 있습니다. 잠시만 기다려 주셔요!"):
            try:
                # Replicate의 최신 Virtual Try-On 모델 호출 (예: yisol/IDM-VTON)
                output = replicate.run(
                    "black-forest-labs/flux-kontext-pro:r8_D5DIyzat2R1go0psPB43T93grZWMxwc2ZCjGx",
                    input={
                        "human_img": human_file,
                        "garm_img": garment_file,
                        "garment_des": "A stylish fashion item",
                        "is_checked": True,
                        "is_checked_crop": False,
                        "denoise_steps": 30,
                        "seed": 42
                    }
                )
                
                # 결과 출력
                if output:
                    st.subheader("✅ 피팅 결과")
                    st.image(output[0], caption="형님의 AI 피팅 샷", use_container_width=True)
                    
                    # 수익화 버튼 (Affiliate 연결 예시)
                    st.success("이 스타일, 형님께 찰떡이네요! 😍")
                    st.link_button("🛍️ 이 상품 최저가로 구매하기 (쿠팡)", "https://www.coupang.com")
                    st.balloons()
                    
            except Exception as e:
                st.error(f"피팅 중 오류가 발생했습니다: {e}")

# --- 하단 안내 ---
st.markdown("<br><hr><center><small>본 기술은 고성능 GPU 서버(Replicate)를 연동하여 실시간으로 처리됩니다.</small></center>", unsafe_allow_html=True)
