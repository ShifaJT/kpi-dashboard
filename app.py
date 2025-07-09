import streamlit as st
import pandas as pd

# Google Sheet CSV export link
sheet_url = "https://docs.google.com/spreadsheets/d/19aDfELEExMn0loj_w6D69ngGG4haEm6lsgqpxJC1OAA/export?format=csv"

# Load data
@st.cache_data(ttl=600)
def load_data():
    return pd.read_csv(sheet_url)

df = load_data()

st.title("📊 KPI Dashboard for Champs")
st.markdown("Enter your **EMP ID** and **Month** to view your performance.")

# Inputs
emp_id = st.text_input("Enter EMP ID (e.g. 1070)")
month = st.selectbox("Select Month", sorted(df['Month'].unique()))

if emp_id and month:
    emp_id = int(emp_id)
    filtered = df[(df["EMP ID"] == emp_id) & (df["Month"] == month)]

    if not filtered.empty:
        champ = filtered.iloc[0]
        st.subheader(f"🎯 Performance for {champ['NAME'].title()} ({month})")

        with st.expander("📌 Performance Metrics"):
            perf_cols = ["Hold", "Wrap", "Auto-On", "Schedule Adherence", "Resolution CSAT", 
                         "Agent Behaviour", "Quality", "PKT", "SL + UPL", "LOGINS"]
            st.table(champ[perf_cols].to_frame(name="Value"))

        with st.expander("🏆 KPI Scores"):
            kpi_cols = [col for col in df.columns if "KPI Score" in col] + ["Grand Total"]
            st.table(champ[kpi_cols].to_frame(name="Score"))
    else:
        st.warning("No data found for this EMP ID and Month.")
