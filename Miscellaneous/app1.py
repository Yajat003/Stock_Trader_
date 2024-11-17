import pandas as pd
import plotly.graph_objects as go
import numpy as np
import streamlit as st


# Function to calculate Bollinger Bands
def calculate_bollinger_bands(data, window=20, no_of_std=2):
    data['SMA'] = data['Adj Close'].rolling(window=window).mean()
    data['STD'] = data['Adj Close'].rolling(window=window).std()
    data['Upper Band'] = data['SMA'] + (no_of_std * data['STD'])
    data['Lower Band'] = data['SMA'] - (no_of_std * data['STD'])
    return data


# Function to calculate Simple Moving Averages
def calculate_sma(data, short_window=50, long_window=200):
    data['SMA_Short'] = data['Adj Close'].rolling(window=short_window).mean()
    data['SMA_Long'] = data['Adj Close'].rolling(window=long_window).mean()
    return data


# Strategy 1: Bollinger Bands Strategy
def apply_bollinger_strategy(data):
    data['Signal'] = 0
    data.loc[data['Adj Close'] < data['Lower Band'], 'Signal'] = 1  # Buy signal
    data.loc[data['Adj Close'] > data['Upper Band'], 'Signal'] = -1  # Sell signal
    return data


# Strategy 2: SMA Crossover Strategy
def apply_sma_strategy(data):
    data['Signal'] = 0
    data.loc[data['SMA_Short'] > data['SMA_Long'], 'Signal'] = 1  # Buy signal
    data.loc[data['SMA_Short'] < data['SMA_Long'], 'Signal'] = -1  # Sell signal
    return data


# Function to adjust strategy parameters based on investment style
def adjust_strategy_parameters(style):
    if style == 'Aggressive':
        return {'bollinger_window': 10, 'bollinger_std': 1.5, 'sma_short': 20, 'sma_long': 50}
    elif style == 'Moderate':
        return {'bollinger_window': 20, 'bollinger_std': 2, 'sma_short': 50, 'sma_long': 200}
    elif style == 'Passive':
        return {'bollinger_window': 30, 'bollinger_std': 2.5, 'sma_short': 100, 'sma_long': 300}
    return {'bollinger_window': 20, 'bollinger_std': 2, 'sma_short': 50, 'sma_long': 200}


# Function to visualize buy/sell signals and capital growth
def visualize_interactive(data, strategy_name, initial_capital):
    # Calculate log returns
    data['Returns'] = np.log(data['Adj Close'] / data['Adj Close'].shift(1))
    data['Position'] = data['Signal'].shift(1).fillna(0)
    data['Strategy_Returns'] = data['Position'] * data['Returns']
    data['Cumulative_Strategy_Returns'] = (data['Strategy_Returns'] + 1).cumprod()
    data['Capital'] = initial_capital * data['Cumulative_Strategy_Returns']
    final_capital = data['Capital'].iloc[-1]
    cumulative_roi = (final_capital - initial_capital) / initial_capital * 100

    # Plot Buy/Sell Signals
    fig1 = go.Figure()
    fig1.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Candlestick'
    ))

    if strategy_name == 'Bollinger Bands':
        fig1.add_trace(go.Scatter(x=data.index, y=data['Upper Band'], mode='lines', name='Upper Band', line=dict(dash='dash', color='red')))
        fig1.add_trace(go.Scatter(x=data.index, y=data['Lower Band'], mode='lines', name='Lower Band', line=dict(dash='dash', color='green')))
    elif strategy_name == 'SMA Crossover':
        fig1.add_trace(go.Scatter(x=data.index, y=data['SMA_Short'], mode='lines', name='Short SMA', line=dict(color='orange')))
        fig1.add_trace(go.Scatter(x=data.index, y=data['SMA_Long'], mode='lines', name='Long SMA', line=dict(color='purple')))

    fig1.add_trace(go.Scatter(x=data[data['Signal'] == 1].index, y=data[data['Signal'] == 1]['Adj Close'],
                              mode='markers', name='Buy Signal', marker=dict(symbol='triangle-up', color='green', size=10)))
    fig1.add_trace(go.Scatter(x=data[data['Signal'] == -1].index, y=data[data['Signal'] == -1]['Adj Close'],
                              mode='markers', name='Sell Signal', marker=dict(symbol='triangle-down', color='red', size=10)))
    fig1.update_layout(title=f'{strategy_name} Strategy - Buy/Sell Signals', xaxis_title='Date', yaxis_title='Price')

    # Plot Capital Growth
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=data.index, y=data['Capital'], mode='lines', name='Capital Growth', line=dict(color='green')))
    fig2.update_layout(title=f'{strategy_name} Strategy - Capital Growth', xaxis_title='Date', yaxis_title='Capital')

    st.plotly_chart(fig1)
    st.plotly_chart(fig2)

    # Display Final Capital and ROI
    st.write(f"Final Capital: {final_capital:.2f}")
    st.write(f"Cumulative ROI: {cumulative_roi:.2f}%")


# Streamlit App
def main():
    st.title("Stock Trading Strategy Simulator")

    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")

        # Upload data
        uploaded_file = st.file_uploader("1. Upload your stock data (CSV format)", type=["csv"])
        if not uploaded_file:
            st.error("Please upload a CSV file to proceed.")
            return

        # Start date
        start_date = st.date_input("2. Start Date")

        # End date
        end_date = st.date_input("3. End Date")

        # Initial capital
        initial_capital = st.number_input("4. Initial Capital", value=100000.0, step=1000.0)

        # Strategy selection
        strategy_name = st.selectbox("5. Select Strategy", options=["Bollinger Bands", "SMA Crossover"])

        # Investment style
        investment_style = st.selectbox("6. Select Investment Style", options=["Aggressive", "Moderate", "Passive"])

    # Process uploaded data
    data = pd.read_csv(uploaded_file, parse_dates=['Date'], index_col='Date')

    # Debugging: Ensure both data index and inputs are timezone-naive
    data.index = data.index.tz_localize(None)
    start_date = pd.Timestamp(start_date).tz_localize(None)
    end_date = pd.Timestamp(end_date).tz_localize(None)

    # Filter data for the selected date range
    data = data.loc[start_date:end_date]

    # Check if the data is empty after filtering
    if data.empty:
        st.error("No data found for the selected date range. Please choose a valid range.")
        return

    # Adjust parameters based on investment style
    params = adjust_strategy_parameters(investment_style)

    # Apply the selected strategy
    if strategy_name == 'Bollinger Bands':
        data = calculate_bollinger_bands(data, params['bollinger_window'], params['bollinger_std'])
        data = apply_bollinger_strategy(data)
    elif strategy_name == 'SMA Crossover':
        data = calculate_sma(data, params['sma_short'], params['sma_long'])
        data = apply_sma_strategy(data)

    # Visualize results
    visualize_interactive(data, strategy_name, initial_capital)


if __name__ == "__main__":
    main()
