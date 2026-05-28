import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # 💡 복합적인 그래프를 그리기 위해 추가했어요!
from datetime import datetime, timedelta
import time
import numpy as np # 💡 수학적 계산을 위한 라이브러리
from sklearn.linear_model import LinearRegression # 💡 머신러닝(선형 회귀) 모델

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="글로벌 주식 분석 & 예측 대시보드 📊",
    page_icon="📈",
    layout="wide"
)

# CSS 스타일링
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
    .ml-box {
        background-color: #f5eef8;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #9b59b6;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

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

# 3. 데이터 불러오기 함수 (Rate Limit 방어 로직 유지)
@st.cache_data(ttl=3600)
def load_stock_data(tickers, start_date, end_date):
    df = pd.DataFrame()
    for name, ticker in tickers.items():
        try:
            stock_obj = yf.Ticker(ticker)
            hist = stock_obj.history(start=start_date, end=end_date)
            
            if not hist.empty:
                df[name] = hist['Close']
            
            time.sleep(1) # 봇 차단 방지
            
        except Exception as e:
            st.warning(f"⚠️ '{name}' 데이터를 가져오는 중 문제가 발생했습니다.")
            
    return df

# --- 메인 화면 ---
st.markdown('<h1 class="title-text">📈 글로벌 주식 분석 및 5년 예측 대시보드</h1>', unsafe_allow_html=True)
st.markdown("""
<div class="info-box">
    <b>💡 학습 포인트:</b> 파이썬을 활용한 과거 데이터 시각화와 더불어, 고등학교 수학의 <b>'최소제곱법을 이용한 선형 회귀(Linear Regression)'</b> 개념을 코드로 구현하여 미래를 예측해봅니다!
</div>
""", unsafe_allow_html=True)

# --- 사이드바 (설정 영역) ---
with st.sidebar:
    st.header("⚙️ 분석 설정")
    
    today = datetime.today()
    one_year_ago = today - timedelta(days=365)
    
    start_date = st.date_input("📅 시작일", one_year_ago)
    end_date = st.date_input("📅 종료일", today)
    
    selected_stocks = st.multiselect(
        "🔍 비교할 기업을 선택하세요",
        options=list(STOCKS.keys()),
        default=["🇺🇸 애플 (AAPL)", "🇰🇷 삼성전자"]
    )

# --- 데이터 처리 및 화면 출력 ---
if start_date > end_date:
    st.error("🚨 오류: 시작일이 종료일보다 늦을 수 없습니다.")
elif not selected_stocks:
    st.warning("👈 왼쪽 사이드바에서 분석할 기업을 1개 이상 선택해주세요!")
else:
    with st.spinner("로딩 중... 데이터를 불러오고 있습니다 🔄"):
        selected_tickers = {name: STOCKS[name] for name in selected_stocks}
        raw_df = load_stock_data(selected_tickers, start_date, end_date)
        
        if raw_df.empty:
            st.error("🚨 데이터를 불러오지 못했습니다. 몇 분 후 다시 시도해주세요.")
        else:
            return_df = ((raw_df / raw_df.iloc[0]) - 1) * 100
            
            # --- 1. 과거 수익률 분석 섹션 ---
            st.markdown("### 📊 1. 누적 수익률 비교 분석")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = px.line(
                    return_df, 
                    labels={"value": "수익률 (%)", "index": "날짜", "variable": "기업명"},
                    template="plotly_white"
                )
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                final_returns = return_df.iloc[-1].sort_values(ascending=False)
                for stock_name, current_return in final_returns.items():
                    if current_return > 0:
                        delta_color = "normal"
                    else:
                        delta_color = "inverse"
                        
                    st.metric(
                        label=stock_name, 
                        value=f"{raw_df[stock_name].iloc[-1]:,.0f}", 
                        delta=f"{current_return:.2f}%", 
                        delta_color=delta_color
                    )
            
            st.markdown("---")
            
            # --- 2. 향후 5년 인공지능 주가 예측 섹션 ---
            st.markdown("### 🤖 2. 머신러닝 기반 향후 5년 추세 예측")
            st.markdown("""
            <div class="ml-box">
                <b>🔍 어떻게 예측하나요?</b><br>
                Scikit-Learn 라이브러리의 <b>선형 회귀(Linear Regression) 모델</b>을 사용합니다. 선택한 기간 동안의 과거 주가 변동 추세를 분석하여, 이를 바탕으로 앞으로 5년(약 1825일) 동안의 가상의 추세선을 그립니다.
            </div>
            """, unsafe_allow_html=True)
            
            # 예측을 원하는 종목 1개 선택
            target_stock = st.selectbox("🎯 5년 후를 예측해볼 기업을 하나만 선택하세요!", selected_stocks)
            
            if target_stock:
                # 1. 데이터 준비 (결측치 제거)
                df_target = raw_df[[target_stock]].dropna()
                
                # 머신러닝을 위해 날짜(index)를 숫자(0, 1, 2...)로 변환
                df_target['Days'] = np.arange(len(df_target))
                
                # 독립변수(X)는 시간(일수), 종속변수(y)는 주가
                X = df_target[['Days']]
                y = df_target[target_stock]
                
                # 2. 선형 회귀 모델 학습 (AI 공부시키기)
                model = LinearRegression()
                model.fit(X, y)
                
                # 3. 향후 5년(1825일) 데이터 예측하기
                future_days = 5 * 365
                last_day = df_target['Days'].iloc[-1]
                
                # 미래의 X값 생성 (마지막 날 다음날부터 1825일치)
                # 모델에 넣기 위해 2차원 배열(.reshape(-1, 1))로 변환합니다.
                future_X = np.arange(last_day + 1, last_day + 1 + future_days).reshape(-1, 1)
                
                # 예측된 미래 주가(y값)
                future_y = model.predict(future_X)
                
                # 미래의 날짜(Date) 생성
                last_date = df_target.index[-1]
                future_dates = [last_date + timedelta(days=int(i)) for i in range(1, future_days + 1)]
                
                # 4. 결과 시각화 (그래프 그리기)
                fig2 = go.Figure()
                
                # 과거 실제 데이터 선 그리기
                fig2.add_trace(go.Scatter(
                    x=df_target.index, 
                    y=df_target[target_stock], 
                    mode='lines', 
                    name='과거 실제 주가',
                    line=dict(color='blue')
                ))
                
                # 미래 예측 데이터 선 그리기 (빨간색 점선)
                fig2.add_trace(go.Scatter(
                    x=future_dates, 
                    y=future_y, 
                    mode='lines', 
                    name='향후 5년 예측 (추세선)', 
                    line=dict(dash='dash', color='red')
                ))
                
                fig2.update_layout(
                    title=f"{target_stock} 향후 5년 추세 예측 그래프",
                    xaxis_title="날짜",
                    yaxis_title="주가",
                    template="plotly_white",
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig2, use_container_width=True)
                
                # 학생들을 위한 생각 거리 제시
                st.warning("⚠️ **주의:** 이 그래프는 과거의 수학적 평균 '추세(Trend)'만 보여줄 뿐입니다. 전염병, 전쟁, 혁신적인 신제품 개발 등 경제를 뒤흔드는 실제 변수들은 반영되지 않았으므로 맹신하면 안 됩니다!")

# 하단 꼬리말
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; font-size: 0.9em;'>
    당곡고등학교 AI 도우미 🤖 | 본 데이터는 프로그래밍 및 수학적 모델링 학습 목적으로 제공됩니다.
</div>
""", unsafe_allow_html=True)
