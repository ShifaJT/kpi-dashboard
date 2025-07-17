import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# === CONFIG ===
SHEET_ID = "19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA"
MONTHLY_SHEET_NAME = "KPI Month"
DAILY_SHEET_NAME = "KPI Day"

# === Google Auth ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)

@st.cache_data

def load_data():
    monthly_df = pd.DataFrame(sheet.worksheet(MONTHLY_SHEET_NAME).get_all_records())
    daily_df = pd.DataFrame(sheet.worksheet(DAILY_SHEET_NAME).get_all_records())
    daily_df["Date"] = pd.to_datetime(daily_df["Date"], errors='coerce')
    daily_df["Week"] = daily_df["Date"].dt.isocalendar().week
    return monthly_df, daily_df

monthly_df, daily_df = load_data()

# === UI ===
st.title("📊 KPI Dashboard for Champs")
emp_id = st.text_input("Enter EMP ID (e.g., 1070)")
view_type = st.selectbox("Select View Type", ["Day", "Week", "Month"])

if emp_id:
    if view_type == "Day":
        selected_date = st.date_input("Select Date")
    elif view_type == "Week":
        week_list = sorted(daily_df["Week"].dropna().unique())
        selected_week = st.selectbox("Select Week Number", week_list)
    elif view_type == "Month":
        month_list = sorted(monthly_df["Month"].dropna().unique())
        selected_month = st.selectbox("Select Month", month_list)

    # Filter data based on selection
    if view_type == "Day" and selected_date:
        filtered = daily_df[(daily_df["EMP ID"].astype(str) == emp_id) & (daily_df["Date"] == pd.to_datetime(selected_date))]
    elif view_type == "Week" and 'selected_week' in locals():
        filtered = daily_df[(daily_df["EMP ID"].astype(str) == emp_id) & (daily_df["Week"] == selected_week)]
    elif view_type == "Month" and 'selected_month' in locals():
        filtered = monthly_df[(monthly_df["EMP ID"].astype(str) == emp_id) & (monthly_df["Month"] == selected_month)]
    else:
        filtered = pd.DataFrame()

    if filtered.empty:
        st.warning("No data found for selected options.")
    else:
        st.success(f"Showing data for EMP ID: {emp_id} | View: {view_type}")
        st.dataframe(filtered)
        # Optional: Add specialized formatting for performance and KPI sections here.
