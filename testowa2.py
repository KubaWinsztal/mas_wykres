import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import ta
import pickle
import numpy as np

########################################################
# 1. Dane przykładowe (dwa instrumenty)
########################################################

# Wczytanie strategii z pliku (upewnij się, że plik istnieje i ma odpowiednią nazwę)
with open('ensemble_scaling_thr_06_kelly', 'rb') as f:
    strategy = pickle.load(f)

cleaned_prices = pd.read_csv("sp500_full.csv")
spy = list(cleaned_prices['SPY'].iloc[1561:])
spy = [i * 1000 / spy[0] for i in spy]

strategy = strategy[::10]
spy = spy[::10]

# Dostosowanie zakresu dat do długości przefiltrowanych danych
dates = pd.date_range(start='2006-03-01', periods=len(strategy), freq='15D')

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
    Dodaje wskaźniki SMA i EMA (z oknem=3 dla przykładowych danych).
    """
    df["SMA_20"] = ta.trend.sma_indicator(df[close_col], window=3)
    df["EMA_20"] = ta.trend.ema_indicator(df[close_col], window=3)
    return df

def calculate_metrics(df, close_col="Close"):
    """
    Oblicza metryki: last_close, zmiana, % zmiana, high, low, sharpe, sortino.
    """
    if df.empty:
        return None, None, None, None, None, None, None
    last_close = df[close_col].iloc[-1]
    prev_close = df[close_col].iloc[0]
    change = last_close - prev_close
    pct_change = (change / prev_close) * 100
    high = df["High"].max()
    low = df["Low"].min()
    # Przykładowe wartości; w realnej analizie liczymy je na podstawie danych
    sharpe = 1.3
    sortino = 3.38
    return last_close, change, pct_change, high, low, sharpe, sortino

########################################################
# 3. Przygotowanie DataFrame dla obu instrumentów
########################################################

dfA = create_instrument_df(strategy, instrument_name="Nasza Strategia")
dfB = create_instrument_df(spy, instrument_name="SP500")

# Dodanie wskaźników technicznych
dfA = add_technical_indicators(dfA, close_col="Close")
dfB = add_technical_indicators(dfB, close_col="Close")

# Obliczenie metryk
last_closeA, changeA, pctA, highA, lowA, sharpeA, sortinoA = calculate_metrics(dfA)
last_closeB, changeB, pctB, highB, lowB, sharpeB, sortinoB = calculate_metrics(dfB)

# Połączenie danych obu instrumentów w jeden DataFrame
df_combined = pd.concat([dfA, dfB], ignore_index=True).sort_values("Datetime")
df_combined.reset_index(drop=True, inplace=True)

########################################################
# Przygotowanie ticków dla osi logarytmicznej
########################################################

min_val = df_combined["Close"].min()
max_val = df_combined["Close"].max()
tick_exponents = np.arange(np.floor(np.log10(min_val)), np.ceil(np.log10(max_val)) + 1)
tick_vals = [10**int(e) for e in tick_exponents]
tick_text = [str(10**int(e)) for e in tick_exponents]

########################################################
# 4. Streamlit – panel boczny i wykresy
########################################################

st.set_page_config(layout="wide")
st.title("Nasza Strategia vs. SP500")

st.sidebar.header("Ustawienia wykresu")
chart_type = st.sidebar.selectbox("Typ wykresu", ["Line", "Candlestick"])
indicators = st.sidebar.multiselect("Wskaźniki Techniczne", ["SMA_20", "EMA_20"])

if st.sidebar.button("Update"):
    # ---- WYŚWIETLANIE METRYK ----

    # Instrument A (Nasza Strategia)
    if last_closeA is not None:
        colA1, colA2, colA3, colA4 = st.columns(4)
        colA1.metric("Nasza Strategia - Kapitał Początkowy", f"{dfA['Close'].iloc[0]:.2f}")
        colA2.metric("Current Capital", f"{last_closeA:.2f}", f"{changeA:.2f} ({pctA:.2f}%)")
        colA3.metric("Sharpe Ratio", f"{sharpeA:.2f}")
        colA4.metric("Sortino Ratio", f"{sortinoA:.2f}")

    # Instrument B (SP500)
    if last_closeB is not None:
        colB1, colB2, colB3, colB4 = st.columns(4)
        colB1.metric("SP500 - Kapitał Początkowy", f"{dfB['Close'].iloc[0]:.2f}")
        colB2.metric("Current Capital", f"{last_closeB:.2f}", f"{changeB:.2f} ({pctB:.2f}%)")
        colB3.metric("Sharpe Ratio", f"{0.45:.2f}")
        colB4.metric("Sortino Ratio", f"{0.7:.2f}")

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
            name="Nasza Strategia",
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

        # Dodawanie wskaźników technicznych
        for ind in indicators:
            if ind == "SMA_20":
                fig_static.add_trace(go.Scatter(
                    x=dfA_sorted["Datetime"],
                    y=dfA_sorted["SMA_20"],
                    mode='lines',
                    name="SMA_20 (Nasza Strategia)",
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
                    name="EMA_20 (Nasza Strategia)",
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
        # Wykres candlestick
        fig_static.add_trace(go.Candlestick(
            x=dfA_sorted["Datetime"],
            open=dfA_sorted["Open"],
            high=dfA_sorted["High"],
            low=dfA_sorted["Low"],
            close=dfA_sorted["Close"],
            name="Nasza Strategia",
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
    
    # Ustawienie logarytmicznej skali osi Y wraz z etykietami
    fig_static.update_layout(
        title="Rynek Akcji",
        xaxis_title="Data",
        yaxis=dict(
            title="Cena",
            type="log",
            tickvals=tick_vals,
            ticktext=tick_text
        ),
        height=500
    )

    st.plotly_chart(fig_static, use_container_width=True)

    ########################################################
    # 5. WYKRES ANIMOWANY (z danymi)
    ########################################################
    st.markdown("---")
    st.header("Wykres Dynamiczny")

    # Tworzenie klatek animacji (każda klatka = dane do określonej daty)
    unique_dates = sorted(df_combined["Datetime"].unique())
    df_anim_list = []
    for i, date_i in enumerate(unique_dates):
        subset = df_combined[df_combined["Datetime"] <= date_i].copy()
        subset["frame"] = i  
        df_anim_list.append(subset)
    df_anim = pd.concat(df_anim_list, ignore_index=True)

    # Ustalenie stałych zakresów dla osi
    y_min = df_combined["Close"].min() - 50
    y_max = df_combined["Close"].max() + 50
    x_min = df_combined["Datetime"].min()
    x_max = df_combined["Datetime"].max()

    # Tworzenie wykresu animowanego
    fig_anim = px.line(
        df_anim,
        x="Datetime",
        y="Close",  # Zmienione z "Cena" na "Close"
        color="Instrument",
        animation_frame="frame",
        range_y=[0, 600000],
        range_x=[x_min, x_max],
        color_discrete_map={
            "Nasza Strategia": "blue",  # Kolor dla "Nasza Strategia"
            "SP500": "red"              # Kolor dla "SP500"
        },
        title='Rynek Krypto'
    )

    # Ustawienie logarytmicznej skali osi Y na wykresie animowanym
    fig_anim.update_layout(
        yaxis=dict(
            type="log",
            tickvals=tick_vals,
            ticktext=tick_text
        ),
        height=500
    )
    fig_anim.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 50
    fig_anim.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 30
    st.plotly_chart(fig_anim, use_container_width=True)
