import streamlit as st
import requests
import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt

load_dotenv()
BASE_URL = os.getenv("BASE_URL")

# Configure the API URL
api_url = f"{BASE_URL}/api/Query/GetTokensConsumptionHistory/a3c09d9b-4baf-4c8a-92f1-1d33cb65e4f8"  # Replace with your API URL

# API call to get data
def fetch_data():
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        if data["isSuccess"]:
            return data["data"]
        else:
            st.error("Error retrieving data: " + data["message"])
    else:
        st.error("Error connecting to the API")
    return []

# Process data for the chart
def prepare_data(data):
    # Extract year, month, and consumption
    df = pd.DataFrame(data)
    df['month'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str))
    df = df[['month', 'tokensConsumed']].groupby('month').sum().reset_index()
    return df

if 'id' in st.session_state:
    # Streamlit setup
    st.title("Token Consumption History")

    # Get data from the API
    data = fetch_data()

    # If there is data, create the chart
    if data:
        df = prepare_data(data)

        # Bar chart
        fig, ax = plt.subplots()
        ax.bar(df['month'].dt.strftime('%Y-%m'), df['tokensConsumed'], color='skyblue')
        ax.set_xlabel("Month")
        ax.set_ylabel("Tokens Consumed")
        ax.set_title("Tokens Consumed per Month")

        st.pyplot(fig)
    else:
        st.write("No data found to display.")

else:
    st.title("Please log in to continue")
