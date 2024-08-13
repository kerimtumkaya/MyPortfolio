import streamlit as st
import pandas as pd
import yfinance as yf
from pycaret.regression import *
import plotly.graph_objs as go
import matplotlib.pyplot as plt

# EMA hesaplama fonksiyonu
def calculate_ema(df, column, window):
    return df[column].ewm(span=window, adjust=False).mean()

# VWMA hesaplama fonksiyonu
def calculate_vwma(data, window):
    data['Typical_Price'] = (data['High'] + data['Low'] + data['Close']) / 3
    vwp = (data['Typical_Price'] * data['Volume']).rolling(window=window).sum() / data['Volume'].rolling(window=window).sum()
    return vwp

# Streamlit başlığı
st.title("Stock Price Prediction")

# Kullanıcıdan hisse senedi sembolü al
ticker = st.text_input("Plase, enter the stock's ticker (örneğin: AAPL):", "AAPL")

# Veriyi Yfinance'dan çek
st.write(f"{ticker} Data collecting for the stock...")
data = yf.download(ticker, period="max")

# EMA ve VWMA hesapla
st.write("Calculating EMA and VWMA...")
data['EMA_200'] = calculate_ema(data, 'Close', 200)
data['VWMA_200'] = calculate_vwma(data, 200)
data['EMA_100'] = calculate_ema(data, 'Close', 100)
data['VWMA_100'] = calculate_vwma(data, 100)


# Veriyi görüntüle
st.subheader(f"Prices for {ticker}")
st.write(data.tail())

# Veriyi görselleştir
# Veriyi görselleştir
st.subheader(f"Price Plot for {ticker}")

fig = go.Figure()

# Kapanış fiyatını ekle
fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close Price'))

# EMA 100'yi ekle
fig.add_trace(go.Scatter(x=data.index, y=data['EMA_100'], mode='lines', name='EMA 100', line=dict(dash='dash')))

# VWMA 100'yi ekle
fig.add_trace(go.Scatter(x=data.index, y=data['VWMA_100'], mode='lines', name='VWMA 100', line=dict(dash='dash')))

# EMA 200'yi ekle
fig.add_trace(go.Scatter(x=data.index, y=data['EMA_200'], mode='lines', name='EMA 200', line=dict(dash='dash')))

# VWMA 200'yi ekle
fig.add_trace(go.Scatter(x=data.index, y=data['VWMA_200'], mode='lines', name='VWMA 200', line=dict(dash='dash')))

# Grafiğe başlık ve etiketler ekle
fig.update_layout(
    title=f"{ticker} Price Plot",
    xaxis_title="Date",
    yaxis_title="Price",
    xaxis_rangeslider_visible=True
)

# Grafiği Streamlit ile göster
st.plotly_chart(fig)

# PyCaret modeli eğit
st.write("ML model training with the stock's prices...")
exp_name = setup(data=data, target='Close')
best_model = compare_models()

# Tahmin yap
st.write("Making predictions...")
predictions = predict_model(best_model, data=data)

st.subheader(f"Predictions for {ticker}")
st.write(predictions.head())

# Tahmin sonuçlarını görselleştir
st.subheader("Results")
plt.figure(figsize=(10, 5))
plt.plot(data.index, data['Close'], label='Actual')
plt.plot(predictions.index, predictions['prediction_label'], label='Predicted', linestyle='--')
plt.legend(loc='best')
st.pyplot(plt)
