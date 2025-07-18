import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe

# Google Sheets setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID = "19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA"

# Load credentials from uploaded file or local file
try:
    credentials = Credentials.from_service_account_file("creds.json", scopes=SCOPES)
except FileNotFoundError:
    st.error("❌ 'creds.json' file not found. Please upload it to the app directory or on Streamlit Cloud.")
    st.stop()

client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID)

# Title
st.title("📊 KPI Dashboard")

# Load all sheet names
sheet_names = [ws.title for ws in sheet.worksheets()]
selected_sheet = st.sidebar.selectbox("Choose a Sheet to View", sheet_names)

# Load and display data
worksheet = sheet.worksheet(selected_sheet)
df = get_as_dataframe(worksheet, evaluate_formulas=True)
df = df.dropna(how='all')

st.write(f"### Data from '{selected_sheet}'")
st.dataframe(df)
