import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import ta
import random

########################################################
# 1. Dane przykładowe (dwa instrumenty)
########################################################

# Generujemy 500 losowych punktów dla dwóch instrumentów
custom_prices_A = [random.randint(900, 1400) for _ in range(500)]
custom_prices_B = [random.randint(800, 2000) for _ in range(500)]

# Zakładamy 500 dni kalendarzowych
dates = pd.date_range(start='2023-01-01', periods=len(custom_prices_A), freq='D')

########################################################
# 2. Funkcje pomocnicze
########################################################

def create_instrument_df(prices, instrument_name):
    """
    Tworzy DataFrame dla jednego instrumentu.
    Kolumny: Datetime, Open, High, Low, Close, Volume
    """
    df = pd.DataFrame({
        "Datetime": dates,
        "Open": prices,
        "High": prices,
        "Low": prices,
        "Close": prices,
        "Volume": [1000]*len(prices)
    })
    df["Instrument"] = instrument_name
    return df

def add_technical_indicators(df, close_col="Close"):
    """
    Dodaje przykładowe wskaźniki SMA i EMA (z oknem=3 dla krótkich danych).
    Możesz zmienić na większe okno np. 20, 50 w zależności od potrzeb.
    """
    df["SMA_20"] = ta.trend.sma_indicator(df[close_col], window=3)
    df["EMA_20"] = ta.trend.ema_indicator(df[close_col], window=3)
    return df

def calculate_metrics(df, close_col="Close"):
    """
    Oblicza proste metryki: last_close, zmiana, % zmiana, high, low, sharpe, sortino.
    """
    if df.empty:
        return None, None, None, None, None, None, None
    last_close = df[close_col].iloc[-1]
    prev_close = df[close_col].iloc[0]
    change = last_close - prev_close
    pct_change = (change / prev_close) * 100
    high = df["High"].max()
    low = df["Low"].min()
    # Przykładowe wartości Sharpe/Sortino – w realnych warunkach licz je naprawdę.
    sharpe = 1.3
    sortino = 3.38
    return last_close, change, pct_change, high, low, sharpe, sortino

########################################################
# 3. Przygotowanie DataFrame dla obu instrumentów
########################################################

dfA = create_instrument_df(custom_prices_A, instrument_name="Our Strategy")
dfB = create_instrument_df(custom_prices_B, instrument_name="SP500")

# Dodajemy wskaźniki
dfA = add_technical_indicators(dfA, close_col="Close")
dfB = add_technical_indicators(dfB, close_col="Close")

# Obliczamy metryki
last_closeA, changeA, pctA, highA, lowA, sharpeA, sortinoA = calculate_metrics(dfA)
last_closeB, changeB, pctB, highB, lowB, sharpeB, sortinoB = calculate_metrics(dfB)

# Łączymy do jednego DF (zawiera dane obu instrumentów)
df_combined = pd.concat([dfA, dfB], ignore_index=True).sort_values("Datetime")
df_combined.reset_index(drop=True, inplace=True)

########################################################
# 4. Streamlit – panel boczny i wykres statyczny
########################################################

st.set_page_config(layout="wide")
st.title("Nasza Strategia vs. SP500 – Statycznie i Animowanie")

st.sidebar.header("Ustawienia Wykresu (statycznego)")
chart_type = st.sidebar.selectbox("Typ Wykresu", ["Line", "Candlestick"])
indicators = st.sidebar.multiselect("Wskaźniki Techniczne", ["SMA_20", "EMA_20"])

if st.sidebar.button("Update"):
    # ---- WYŚWIETLANIE METRYK ----

    # Instrument A
    if last_closeA is not None:
        colA1, colA2, colA3, colA4, colA5 = st.columns(5)
        colA1.metric("Our Strategy - Last Price", 
                     f"{last_closeA:.2f}", 
                     f"{changeA:.2f} ({pctA:.2f}%)")
        colA2.metric("Starting Capital", f"{highA:.2f}")
        colA3.metric("Current Capital", f"{lowA:.2f}")
        colA4.metric("Sharpe Ratio", f"{sharpeA:.2f}")
        colA5.metric("Sortino Ratio", f"{sortinoA:.2f}")

    # Instrument B
    if last_closeB is not None:
        colB1, colB2, colB3, colB4, colB5 = st.columns(5)
        colB1.metric("SP500 - Last Price", 
                     f"{last_closeB:.2f}", 
                     f"{changeB:.2f} ({pctB:.2f}%)")
        colB2.metric("Starting Capital", f"{highB:.2f}")
        colB3.metric("Current Capital", f"{lowB:.2f}")
        colB4.metric("Sharpe Ratio", f"{sharpeB:.2f}")
        colB5.metric("Sortino Ratio", f"{sortinoB:.2f}")

    # ---- TWORZENIE WYKRESU STATYCZNEGO ----
    st.subheader("Wykres Statyczny")
    fig_static = go.Figure()

    dfA_sorted = dfA.sort_values("Datetime")
    dfB_sorted = dfB.sort_values("Datetime")

    if chart_type == "Line":
        # Instrument A (niebieski)
        fig_static.add_trace(go.Scatter(
            x=dfA_sorted["Datetime"],
            y=dfA_sorted["Close"],
            mode='lines',
            name="Our Strategy",
            line=dict(color='blue')
        ))
        # Instrument B (czerwony)
        fig_static.add_trace(go.Scatter(
            x=dfB_sorted["Datetime"],
            y=dfB_sorted["Close"],
            mode='lines',
            name="SP500",
            line=dict(color='red')
        ))

        # Dodawanie wybranych wskaźników
        for ind in indicators:
            if ind == "SMA_20":
                fig_static.add_trace(go.Scatter(
                    x=dfA_sorted["Datetime"],
                    y=dfA_sorted["SMA_20"],
                    mode='lines',
                    name="SMA_20 (Our Strat.)",
                    line=dict(color='blue', dash='dash')
                ))
                fig_static.add_trace(go.Scatter(
                    x=dfB_sorted["Datetime"],
                    y=dfB_sorted["SMA_20"],
                    mode='lines',
                    name="SMA_20 (SP500)",
                    line=dict(color='red', dash='dash')
                ))
            elif ind == "EMA_20":
                fig_static.add_trace(go.Scatter(
                    x=dfA_sorted["Datetime"],
                    y=dfA_sorted["EMA_20"],
                    mode='lines',
                    name="EMA_20 (Our Strat.)",
                    line=dict(color='blue', dash='dot')
                ))
                fig_static.add_trace(go.Scatter(
                    x=dfB_sorted["Datetime"],
                    y=dfB_sorted["EMA_20"],
                    mode='lines',
                    name="EMA_20 (SP500)",
                    line=dict(color='red', dash='dot')
                ))

    else:
        # Candlestick - 2 instrumenty na jednym wykresie (nakładają się)
        fig_static.add_trace(go.Candlestick(
            x=dfA_sorted["Datetime"],
            open=dfA_sorted["Open"],
            high=dfA_sorted["High"],
            low=dfA_sorted["Low"],
            close=dfA_sorted["Close"],
            name="Our Strategy",
            increasing_line_color='blue',
            decreasing_line_color='blue'
        ))
        fig_static.add_trace(go.Candlestick(
            x=dfB_sorted["Datetime"],
            open=dfB_sorted["Open"],
            high=dfB_sorted["High"],
            low=dfB_sorted["Low"],
            close=dfB_sorted["Close"],
            name="SP500",
            increasing_line_color='red',
            decreasing_line_color='red'
        ))

    fig_static.update_layout(
        title="Porównanie (Statyczny)",
        xaxis_title="Data",
        yaxis_title="Price",
        height=500
    )

    st.plotly_chart(fig_static, use_container_width=True)

    ########################################################
    # 5. WYKRES ANIMOWANY (z tymi samymi danymi)
    ########################################################
    st.markdown("---")
    st.header("Wykres Dynamiczny")

    # Tworzymy listę klatek animacji opartą na unikalnych datach,
    # aby animacja pokazywała stopniowo dane dzień po dniu
    unique_dates = sorted(df_combined["Datetime"].unique())
    df_anim_list = []

    for i, date_i in enumerate(unique_dates):
        # Bierzemy wszystkie wiersze z datą <= obecnej dacie 'date_i'
        subset = df_combined[df_combined["Datetime"] <= date_i].copy()
        # Ustawiamy numer klatki
        subset["frame"] = i  
        df_anim_list.append(subset)

    # Łączymy wszystkie subsety w jeden DataFrame
    df_anim = pd.concat(df_anim_list, ignore_index=True)

    # Stały zakres Y, żeby wykres nie "skakał"
    y_min = df_combined["Close"].min() - 50
    y_max = df_combined["Close"].max() + 50

    # Możemy też ustawić range_x, żeby oś X się nie zmieniała
    x_min = df_combined["Datetime"].min()
    x_max = df_combined["Datetime"].max()

    # Tworzymy wykres animowany
    fig_anim = px.line(
        df_anim,
        x="Datetime",
        y="Close",
        color="Instrument",
        animation_frame="frame",
        range_y=[y_min, y_max],
        range_x=[x_min, x_max],
        title="Animacja - Our Strategy vs SP500 (dzień po dniu)"
    )
    fig_anim.update_layout(height=500)

    st.plotly_chart(fig_anim, use_container_width=True)

    st.write("""
    **Instrukcja**:
    - Kliknij "Play" (ikonka w lewym dolnym rogu wykresu) 
      lub użyj suwaka "frame" do przeglądania kolejnych dni.
    - Obie linie narastają jednocześnie – 
      w klatce nr i widać dane od początku do i-tego dnia.
    """)

else:
    st.info("Kliknij 'Update' w panelu bocznym, aby zobaczyć wykresy i animację.")
