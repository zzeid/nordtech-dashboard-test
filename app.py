import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Executive Dashboard - Business Health", layout="wide")

# Mēģinām ielādēt datus
@st.cache_data
def load_data():
    try:
        return pd.read_csv("enriched_data.csv")
    except FileNotFoundError:
        st.error("Datu fails 'enriched_data.csv' nav atrasts. Lūdzu palaidiet Colab failu, lai to izveidotu.")
        return pd.DataFrame() # Atgriežam tukšu df, ja nav atrasts

df = load_data()

st.title("Executive Dashboard: Pārdošanas un Sūdzību Analīze")

if df.empty:
    st.warning("Gaidu uz 'enriched_data.csv'. Lūdzu ģenerējiet to Colab bloknotā.")
    st.stop()

# Datumu konversija tikai gadījumam
df['Date_Clean'] = pd.to_datetime(df['Date_Clean'])

# --- SIDEBAR ---
st.sidebar.header("Filtri")
categories = ["Visas"] + list(df['Product_Category'].dropna().unique())
selected_category = st.sidebar.selectbox("Produktu Kategorija", categories)

min_date = df['Date_Clean'].min()
max_date = df['Date_Clean'].max()
start_date, end_date = st.sidebar.date_input("Laika periods", [min_date, max_date])

# Pielietojam filtrus
df_filtered = df.copy()
if selected_category != "Visas":
    df_filtered = df_filtered[df_filtered['Product_Category'] == selected_category]
    
df_filtered = df_filtered[(df_filtered['Date_Clean'].dt.date >= start_date) & 
                          (df_filtered['Date_Clean'].dt.date <= end_date)]

# --- KPI RINDA ---
st.markdown("### Galvenie Rādītāji (KPIs)")
col1, col2, col3, col4 = st.columns(4)

total_revenue = df_filtered[df_filtered['Payment_Status'] == 'Paid']['Price_Clean'].sum()
total_returns = df_filtered['Returned'].sum()
return_rate = (total_returns / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
total_complaints = df_filtered[df_filtered['Complaint_Count'] > 0]['Complaint_Count'].sum()

col1.metric("Kopējie Ieņēmumi", f"€{total_revenue:,.2f}")
col2.metric("Pārdotas Preces", len(df_filtered[df_filtered['Payment_Status'] == 'Paid']))
col3.metric("Atgriezto Preču %", f"{return_rate:.1f}%")
col4.metric("Kopējās Sūdzības", int(total_complaints))

st.markdown("---")

# --- VIZUĀĻI ---
col_v1, col_v2 = st.columns(2)

with col_v1:
    st.subheader("Atgrieztās preces pa kategorijām")
    returns_by_cat = df_filtered[df_filtered['Returned'] == True]['Product_Category'].value_counts()
    if not returns_by_cat.empty:
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        sns.barplot(x=returns_by_cat.index, y=returns_by_cat.values, ax=ax1, palette='Reds_r')
        plt.xticks(rotation=45)
        st.pyplot(fig1)
    else:
        st.info("Nav datu par atgriešanām izvēlētajai kategorijai/laikam.")

with col_v2:
    st.subheader("Biežākās Sūdzību Tēmas")
    complaints_data = df_filtered[df_filtered['Complaint_Count'] > 0]['Complaint_Category'].value_counts()
    if not complaints_data.empty:
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        plt.pie(complaints_data.values, labels=complaints_data.index, autopct='%1.1f%%', colors=sns.color_palette('pastel'))
        st.pyplot(fig2)
    else:
        st.info("Nav datu par sūdzībām izvēlētajam periodam.")
        

# --- DATU TABULA ---
st.subheader("Top problēmu gadījumi (Atgriezti un ar sūdzību)")
problem_cases = df_filtered[(df_filtered['Returned'] == True) & (df_filtered['Complaint_Count'] > 0)]
if not problem_cases.empty:
    cols_to_show = ['Transaction_ID', 'Date_Clean', 'Product_Name', 'Complaint_Category', 'Sentiment']
    st.dataframe(problem_cases[cols_to_show], use_container_width=True)
else:
    st.success("Neviens produkts nav gan atgriezts, gan saņēmis biļeti izvēlētajā rāmī.")
