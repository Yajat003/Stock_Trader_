import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# Helper functions
def fetch_stock_data(ticker, period='max'):
    stock = yf.Ticker(ticker)
    return stock.history(period=period)

def calculate_bollinger_bands(data, window=20, no_of_std=2):
    data['SMA'] = data['Close'].rolling(window=window).mean()
    data['STD'] = data['Close'].rolling(window=window).std()
    data['Upper Band'] = data['SMA'] + (no_of_std * data['STD'])
    data['Lower Band'] = data['SMA'] - (no_of_std * data['STD'])
    return data

def calculate_sma(data, short_window=50, long_window=200):
    data['SMA_Short'] = data['Close'].rolling(window=short_window).mean()
    data['SMA_Long'] = data['Close'].rolling(window=long_window).mean()
    return data

def apply_strategy(data, strategy):
    if strategy == "Bollinger Bands":
        data = calculate_bollinger_bands(data)
        data['Signal'] = 0
        data.loc[data['Close'] < data['Lower Band'], 'Signal'] = 1  # Buy signal
        data.loc[data['Close'] > data['Upper Band'], 'Signal'] = -1 # Sell signal
    elif strategy == "SMA Crossover":
        data = calculate_sma(data)
        data['Signal'] = 0
        data.loc[data['SMA_Short'] > data['SMA_Long'], 'Signal'] = 1  # Buy signal
        data.loc[data['SMA_Short'] < data['SMA_Long'], 'Signal'] = -1 # Sell signal
    return data

def calculate_investment_growth(data, amount, style):
    start_price = data['Close'].iloc[0]
    end_price = data['Close'].iloc[-1]
    style_multipliers = {'Aggressive': 1.5, 'Moderate': 1.0, 'Passive': 0.75}
    multiplier = style_multipliers.get(style, 1.0)
    growth = (end_price / start_price) * amount * multiplier
    roi = ((growth - amount) / amount) * 100
    data[f'{style} Growth'] = (data['Close'] / start_price) * amount * multiplier
    return growth, roi

def plot_investment_comparison(data, styles, start_date, end_date):
    # Filter data between the start and end dates
    filtered_data = data.loc[start_date:end_date]
    
    # Create the plot
    fig = go.Figure()
    
    for style in styles:
        growth_column = f'{style} Growth'
        if growth_column in filtered_data:
            fig.add_trace(go.Scatter(
                x=filtered_data.index,
                y=filtered_data[growth_column],
                mode='lines',
                name=f"{style} Investment",
                line=dict(width=2)
            ))
    
    # Update layout to improve visibility
    fig.update_layout(
        title="Investment Growth Comparison",
        xaxis_title="Date",
        yaxis_title="Investment Value",
        template="plotly_white",
        height=600,
        width=900,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig)

def visualize_interactive(data, strategy_name, start_date, end_date):
    filtered_data = data.loc[start_date:end_date]
    fig = go.Figure()

    # Plot Close Price
    fig.add_trace(go.Candlestick(
        x=filtered_data.index,
        open=filtered_data['Open'],
        high=filtered_data['High'],
        low=filtered_data['Low'],
        close=filtered_data['Close'],
        name='Price'
    ))

    if strategy_name == 'Bollinger Bands':
        fig.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data['Upper Band'], mode='lines', name='Upper Band', line=dict(dash='dash', color='red')))
        fig.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data['Lower Band'], mode='lines', name='Lower Band', line=dict(dash='dash', color='green')))
    elif strategy_name == 'SMA Crossover':
        fig.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data['SMA_Short'], mode='lines', name='Short-term SMA', line=dict(color='orange')))
        fig.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data['SMA_Long'], mode='lines', name='Long-term SMA', line=dict(color='purple')))

    # Add Buy and Sell signals
    fig.add_trace(go.Scatter(x=filtered_data[filtered_data['Signal'] == 1].index, y=filtered_data[filtered_data['Signal'] == 1]['Close'], mode='markers', name='Buy Signal', marker=dict(symbol='triangle-up', color='green', size=8)))
    fig.add_trace(go.Scatter(x=filtered_data[filtered_data['Signal'] == -1].index, y=filtered_data[filtered_data['Signal'] == -1]['Close'], mode='markers', name='Sell Signal', marker=dict(symbol='triangle-down', color='red', size=8)))

    fig.update_layout(title=f'{strategy_name} Strategy - Buy/Sell Signals', xaxis_title='Date', yaxis_title='Price', showlegend=True, height=800, width=1200)
    st.plotly_chart(fig)

# Main function for the Streamlit app
def main():
    st.title("Stock Strategy Analyzer")

    # Data source selection
    data_source = st.selectbox("Select Data Source", ["Upload CSV", "Enter Ticker Symbol"])
    data = None

    if data_source == "Upload CSV":
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file is not None:
            data = pd.read_csv(uploaded_file, parse_dates=['Date'])
            data.set_index('Date', inplace=True)
            st.write(data)  # Display the first few rows of the data


    elif data_source == "Enter Ticker Symbol":
        ticker = st.text_input("Enter Ticker Symbol", "AAPL")
        if ticker:
            data = fetch_stock_data(ticker, period="max")
            st.write(data)  # Display the first few rows of the data



    if data is not None:
        # Ensure datetime index is tz-naive
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)

        # Input parameters
        strategy = st.selectbox("Choose Strategy", ["Bollinger Bands", "SMA Crossover"])
        investment_style = st.selectbox("Select Investment Style", ["Aggressive", "Moderate", "Passive"])
        initial_capital = st.number_input("Enter Initial Capital", min_value=1000, value=10000)

        start_date = pd.to_datetime(st.text_input("Enter Start Date (YYYY-MM-DD)", "2020-01-01"))
        end_date = pd.to_datetime(st.text_input("Enter End Date (YYYY-MM-DD)", "2021-01-01"))

        if start_date > end_date:
            st.error("End date must be later than start date")
        else:
            if st.button("Analyze Stock"):
                # Apply the chosen strategy
                data = apply_strategy(data, strategy)

                # Visualize results
                st.subheader("Visualizing Investment Growth")
                visualize_interactive(data, strategy, start_date, end_date)


                # Calculate investment growth for all styles
                styles = ["Aggressive", "Moderate", "Passive"]
                for style in styles:
                    data[f'{style} Growth'] = None  # Initialize the column
                    growth, roi = calculate_investment_growth(data, initial_capital, style)
                    st.write(f"{style} Style Results: Final Value: {growth:.2f}, ROI: {roi:.2f}%")


                plot_investment_comparison(data, styles, start_date, end_date)

if __name__ == "__main__":
    main()
