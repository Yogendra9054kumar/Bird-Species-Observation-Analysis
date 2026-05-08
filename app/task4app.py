import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Bird Dashboard", layout="wide")

# ---------------- THEME TOGGLE ----------------
st.sidebar.header("⚙️ Settings")

theme = st.sidebar.radio("Select Theme", ["Light", "Dark"])

if theme == "Dark":
    plotly_template = "plotly_dark"
    bg_color = "#0e1117"
    text_color = "white"
    card_color = "#1f2937"
else:
    plotly_template = "plotly"
    bg_color = "white"
    text_color = "black"
    card_color = "#f0f2f6"

st.markdown(f"""
<style>
.stApp {{
    background-color: {bg_color};
    color: {text_color};
}}

h1, h2, h3, h4, h5, h6, p, div, span, label {{
    color: {text_color} !important;
}}

section[data-testid="stSidebar"] {{
    background-color: {card_color};
}}

[data-testid="stMetric"] {{
    background-color: {card_color};
    padding: 10px;
    border-radius: 10px;
}}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.title("Bird Species Dashboard")
st.caption("Interactive Bird Biodiversity Analysis")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    return pd.read_csv("final_data.csv")

df = load_data()

if df.empty:
    st.error("No data found!")
    st.stop()

# ---------------- FILTERS ----------------
st.sidebar.header("Filters")

habitat = st.sidebar.multiselect(
    "Habitat",
    df['Location_Type'].dropna().unique(),
    default=df['Location_Type'].dropna().unique()
)

year = st.sidebar.multiselect(
    "Year",
    sorted(df['Year'].dropna().unique()),
    default=sorted(df['Year'].dropna().unique())
)

species = st.sidebar.multiselect(
    "Species",
    df['Common_Name'].dropna().unique()
)

if species:
    df = df[
        (df['Location_Type'].isin(habitat)) &
        (df['Year'].isin(year)) &
        (df['Common_Name'].isin(species))
    ]
else:
    df = df[
        (df['Location_Type'].isin(habitat)) &
        (df['Year'].isin(year))
    ]

# ---------------- KPIs ----------------
st.subheader("Key Metrics")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Observations", len(df))
col2.metric("Unique Species", df['Scientific_Name'].nunique())
col3.metric("Locations", df['Admin_Unit'].nunique())
col4.metric("Avg Temp", round(df['Temperature'].mean(), 2))

st.divider()

# ---------------- HABITAT ----------------
st.subheader("Habitat Distribution")

habitat_df = df['Location_Type'].value_counts().reset_index()
habitat_df.columns = ['Location_Type', 'Count']

fig = px.bar(habitat_df, x='Location_Type', y='Count',
             color='Location_Type', template=plotly_template)
st.plotly_chart(fig, use_container_width=True)

st.info("Forest areas show higher biodiversity compared to grasslands.")

st.divider()

# ---------------- SPECIES ----------------
st.subheader("Top Species")

species_df = df['Common_Name'].value_counts().head(10).reset_index()
species_df.columns = ['Common_Name', 'Count']

fig = px.bar(species_df, x='Common_Name', y='Count',
             color='Common_Name', template=plotly_template)
st.plotly_chart(fig, use_container_width=True)

st.info("Few species dominate observations, indicating uneven distribution.")

st.divider()

# ---------------- TEMPERATURE ----------------
st.subheader("Temperature Impact")

fig = px.scatter(
    df,
    x='Temperature',
    y='Initial_Three_Min_Cnt',
    color='Location_Type',
    template=plotly_template
)
st.plotly_chart(fig, use_container_width=True)

st.info("Temperature variations slightly affect bird activity levels.")

st.divider()

# ---------------- HUMIDITY ----------------
st.subheader("Humidity Impact")

fig = px.scatter(
    df,
    x='Humidity',
    y='Initial_Three_Min_Cnt',
    color='Location_Type',
    template=plotly_template
)
st.plotly_chart(fig, use_container_width=True)

st.info("Humidity has a moderate impact on bird visibility and movement.")

st.divider()

# ---------------- YEAR ----------------
st.subheader("📈 Year Analysis")

yearly = df.groupby('Year').size().reset_index(name='Count')

if len(yearly) > 1:
    fig = px.line(yearly, x='Year', y='Count',
                  markers=True, template=plotly_template)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Only one year available — trend not meaningful.")
    st.metric("Total Observations", yearly['Count'].values[0])

st.divider()

# ---------------- FLYOVER ----------------
st.subheader("Flyover Analysis")

fig = px.pie(df, names='Flyover_Observed', template=plotly_template)
st.plotly_chart(fig, use_container_width=True)

st.info("Flyover observations represent bird movement rather than stationary presence.")

st.divider()

# ---------------- GEOGRAPHIC ----------------
st.subheader("Geographic Analysis")

geo_df = df.groupby('Admin_Unit').size().reset_index(name='Count')

fig = px.bar(
    geo_df.sort_values(by='Count', ascending=False),
    x='Admin_Unit',
    y='Count',
    color='Admin_Unit',
    template=plotly_template
)
st.plotly_chart(fig, use_container_width=True)

st.info("📌 Certain locations act as biodiversity hotspots.")

st.divider()

# ---------------- CONSERVATION ----------------
st.subheader("Conservation Analysis")

fig = px.pie(df, names='PIF_Watchlist_Status', template=plotly_template)
st.plotly_chart(fig, use_container_width=True)

st.info("📌 Presence of watchlist species indicates conservation importance.")

st.divider()

# ---------------- SQL INTEGRATION ----------------
st.markdown("### SQL-Based Insights")
st.subheader("SQL Analysis")

conn = sqlite3.connect("bird_data.db")

df.to_sql("birds", conn, if_exists="replace", index=False)

# Habitat SQL
query1 = "SELECT Location_Type, COUNT(*) as Count FROM birds GROUP BY Location_Type"
result1 = pd.read_sql(query1, conn)

st.write("Habitat Count (SQL)")
st.dataframe(result1)

fig = px.bar(result1, x='Location_Type', y='Count',
             template=plotly_template)
st.plotly_chart(fig, use_container_width=True)

# Top species SQL
query2 = """
SELECT Common_Name, COUNT(*) as Count
FROM birds
GROUP BY Common_Name
ORDER BY Count DESC
LIMIT 10
"""
result2 = pd.read_sql(query2, conn)

st.write("Top Species (SQL)")
st.dataframe(result2)

# Avg temp SQL
query3 = "SELECT AVG(Temperature) as Avg_Temp FROM birds"
result3 = pd.read_sql(query3, conn)

st.write("Average Temperature")
st.dataframe(result3)



# Habitat vs Species Diversity
query4 = """
SELECT Location_Type, COUNT(DISTINCT Scientific_Name) as Species_Count
FROM birds
GROUP BY Location_Type
"""
result4 = pd.read_sql(query4, conn)

st.write("Species Diversity by Habitat")
st.dataframe(result4)

fig = px.bar(result4, x='Location_Type', y='Species_Count',
             template=plotly_template)
st.plotly_chart(fig, use_container_width=True)

# Observer Activity
query5 = """
SELECT Observer, COUNT(*) as Observations
FROM birds
GROUP BY Observer
ORDER BY Observations DESC
LIMIT 10
"""
result5 = pd.read_sql(query5, conn)

st.write("Top Observers")
st.dataframe(result5)

fig = px.bar(result5, x='Observer', y='Observations',
             template=plotly_template)
st.plotly_chart(fig, use_container_width=True)

# Distance Analysis
query6 = """
SELECT Distance, COUNT(*) as Count
FROM birds
GROUP BY Distance
"""
result6 = pd.read_sql(query6, conn)

st.write("Distance Distribution")
st.dataframe(result6)

fig = px.bar(result6, x='Distance', y='Count',
             template=plotly_template)
st.plotly_chart(fig, use_container_width=True)

# Weather Impact
query7 = """
SELECT Sky, COUNT(*) as Count
FROM birds
GROUP BY Sky
"""
result7 = pd.read_sql(query7, conn)

st.write("Weather Condition Distribution")
st.dataframe(result7)

fig = px.bar(result7, x='Sky', y='Count',
             template=plotly_template)
st.plotly_chart(fig, use_container_width=True)

# Habitat-wise Average Temperature
query8 = """
SELECT Location_Type, AVG(Temperature) as Avg_Temp
FROM birds
GROUP BY Location_Type
"""
result8 = pd.read_sql(query8, conn)

st.write("Avg Temperature by Habitat")
st.dataframe(result8)

fig = px.bar(result8, x='Location_Type', y='Avg_Temp',
             template=plotly_template)
st.plotly_chart(fig, use_container_width=True)

# Watchlist Species Count
query9 = """
SELECT PIF_Watchlist_Status, COUNT(*) as Count
FROM birds
GROUP BY PIF_Watchlist_Status
"""
result9 = pd.read_sql(query9, conn)

st.write("Watchlist Status Count")
st.dataframe(result9)

# Peak Observation Locations
query10 = """
SELECT Admin_Unit, COUNT(*) as Count
FROM birds
GROUP BY Admin_Unit
ORDER BY Count DESC
LIMIT 5
"""
result10 = pd.read_sql(query10, conn)

st.write("Top 5 Locations")
st.dataframe(result10)


conn.close()

st.divider()
# ---------------- DOWNLOAD ----------------
st.subheader("📥 Download Data")

csv = df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download Filtered Data",
    data=csv,
    file_name='filtered_data.csv',
    mime='text/csv'
)

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("🚀 Final Project | Yogendra Verma")