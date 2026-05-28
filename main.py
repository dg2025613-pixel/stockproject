import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="글로벌 주식 분석 대시보드 📊",
    page_icon="📈",
    layout="wide"
)

# CSS 스타일링 (앱을 예쁘게 꾸며줘요!)
st.markdown("""
    <style>
    .title-text {
        text-align: center;
        color: #2e4053;
        font-weight: bold;
        padding: 20px;
    }
    .info-box {
        background-color: #e8f8f5;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1abc9c;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 분석할 주요 주식 종목 사전 (이름: 티커)
# 탐구 활동: 학생이 원하는 다른 기업의 티커(Ticker)를 찾아서 추가해보세요!
STOCKS = {
    "🇺🇸 애플 (AAPL)": "AAPL",
    "🇺🇸 마이크로소프트 (MSFT)": "MSFT",
    "🇺🇸 테슬라 (TSLA)": "TSLA",
    "🇺🇸 엔비디아 (NVDA)": "NVDA",
    "🇰🇷 삼성전자": "005930.KS",
    "🇰🇷 SK하이닉스": "000660.KS",
    "🇰🇷 현대자동차": "005380.KS",
    "🇰🇷 카카오": "035720.KS"
}

# 3. 데이터 불러오기 함수 (캐싱을 사용하여 속도 향상)
@st.cache_data
def load_stock_data(tickers, start_date, end_date):
    """
    선택한 주식들의 종가(Close) 데이터를 가져오는 함수입니다.
    """
    df = pd.DataFrame()
    for name, ticker in tickers.items():
        # yfinance를 통해 데이터 다운로드
        stock_obj = yf.Ticker(ticker)
        hist = stock_obj.history(start=start_date, end=end_date)
        
        if not hist.empty:
            df[name] = hist['Close']
    return df

# --- 메인 화면 ---
st.markdown('<h1 class="title-text">📈 글로벌 주요 주식 수익률 분석기</h1>', unsafe_allow_html=True)
st.markdown("""
<div class="info-box">
    <b>💡 학습 포인트:</b> 파이썬의 <code>yfinance</code>와 <code>pandas</code>를 활용해 실제 금융 데이터를 수집하고 분석합니다.<br>
    기준일 대비 주가가 얼마나 상승/하락했는지 비율(수익률)을 계산하여 차트로 비교해봅시다!
</div>
""", unsafe_allow_html=True)

# --- 사이드바 (설정 영역) ---
with st.sidebar:
    st.header("⚙️ 분석 설정")
    
    # 날짜 선택기
    today = datetime.today()
    one_year_ago = today - timedelta(days=365)
    
    start_date = st.date_input("📅 시작일", one_year_ago)
    end_date = st.date_input("📅 종료일", today)
    
    # 종목 선택기
    selected_stocks = st.multiselect(
        "🔍 비교할 기업을 선택하세요",
        options=list(STOCKS.keys()),
        default=["🇺🇸 애플 (AAPL)", "🇰🇷 삼성전자"]
    )

# --- 데이터 처리 및 화면 출력 ---
if start_date > end_date:
    st.error("🚨 오류: 시작일이 종료일보다 늦을 수 없습니다. 날짜를 다시 설정해주세요!")
elif not selected_stocks:
    st.warning("👈 왼쪽 사이드바에서 분석할 기업을 1개 이상 선택해주세요!")
else:
    with st.spinner("로딩 중... 실시간 데이터를 불러오고 있습니다 🔄"):
        # 선택한 주식들의 티커 딕셔너리 생성
        selected_tickers = {name: STOCKS[name] for name in selected_stocks}
        
        # 데이터 로드
        raw_df = load_stock_data(selected_tickers, start_date, end_date)
        
        if raw_df.empty:
            st.error("선택한 기간의 데이터가 없습니다. 주말이나 휴일인지 확인해주세요.")
        else:
            # 1. 수익률 계산 (누적 수익률)
            # 수식: (현재 주가 - 시작 주가) / 시작 주가 * 100
            # 학습 포인트: 데이터프레임(DataFrame)의 첫 번째 행(iloc[0])을 기준으로 비율을 계산합니다.
            return_df = ((raw_df / raw_df.iloc[0]) - 1) * 100
            
            # --- 레이아웃 나누기 ---
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📊 누적 수익률 비교 차트 (%)")
                # Plotly를 이용해 상호작용 가능한 꺾은선 그래프 그리기
                fig = px.line(
                    return_df, 
                    labels={"value": "수익률 (%)", "Date": "날짜", "variable": "기업명"},
                    template="plotly_white"
                )
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.subheader("💰 기간 내 최종 수익률")
                # 마지막 날짜의 수익률 데이터를 가져옴
                final_returns = return_df.iloc[-1].sort_values(ascending=False)
                
                # 결과를 예쁘게 메트릭으로 출력
                for stock_name, current_return in final_returns.items():
                    # 부호에 따라 색상과 화살표 결정
                    if current_return > 0:
                        delta_color = "normal"
                    else:
                        delta_color = "inverse"
                        
                    st.metric(
                        label=stock_name, 
                        value=f"{raw_df[stock_name].iloc[-1]:,.0f}", # 현재 가격
                        delta=f"{current_return:.2f}%", # 수익률
                        delta_color=delta_color
                    )
                    
            st.markdown("---")
            with st.expander("📝 원본 주가 데이터 (DataFrame) 보기"):
                st.dataframe(raw_df)

# 하단 꼬리말
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; font-size: 0.9em;'>
    당곡고등학교 AI 도우미 🤖 | 본 데이터는 학습 및 탐구 목적으로 제공됩니다.
</div>
""", unsafe_allow_html=True)
