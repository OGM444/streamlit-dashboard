import os
from navigation import make_sidebar
import pandas as pd
import streamlit as st
import altair as alt
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Filter,
    FilterExpression,
    Dimension,
    Metric,
    RunReportRequest,
)

ga4_credentials = service_account.Credentials.from_service_account_info(
    st.secrets["ga4_service_account"],
    scopes=["https://www.googleapis.com/auth/analytics.readonly"]
)
client = BetaAnalyticsDataClient(credentials=ga4_credentials)

# Set up Streamlit
st.logo("assets/whd_logo.png")
make_sidebar()
st.title("📈 SEO Data Dashboard")
st.divider()
st.sidebar.header("Add your filters here👇")
# Define Google Analytics property ID
property_id = "312173280"
# Date range input
start_date_1 = st.sidebar.date_input("Start date of current month", pd.to_datetime("2024-01-18"))
end_date_1 = st.sidebar.date_input("End date of current month", pd.to_datetime("today"))
start_date_2 = st.sidebar.date_input("Start date of month to compare", pd.to_datetime("2024-01-18"))
end_date_2 = st.sidebar.date_input("End date of month to compare", pd.to_datetime("today"))

# Function to fetch report data
def fetch_ga_data(date_range, date_label):
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="newUsers"),
            Metric(name="engagedSessions"),
        ],
        date_ranges=[date_range],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="sessionDefaultChannelGroup",
                string_filter={"value": "Organic Search"},
            )
        ),
    )
    response = client.run_report(request)
    data = []
    for row in response.rows:
        data.append({
            'Date Range': date_label,
            'Channel': row.dimension_values[0].value,
            'Active Users': row.metric_values[0].value,
            'New Users': row.metric_values[1].value,
            'Engaged Sessions': row.metric_values[2].value
        })
    return data
# Fetch and combine data
combined_data = fetch_ga_data(
    DateRange(start_date=start_date_1.strftime("%Y-%m-%d"), end_date=end_date_1.strftime("%Y-%m-%d")), 
    start_date_1.strftime('%B %Y')
)
combined_data += fetch_ga_data(
    DateRange(start_date=start_date_2.strftime("%Y-%m-%d"), end_date=end_date_2.strftime("%Y-%m-%d")), 
    start_date_2.strftime('%B %Y')
)
# Create DataFrame for combined GA data
df_combined = pd.DataFrame(combined_data)
# Fetch top 10 landing pages data
request_landing_pages = RunReportRequest(
    property=f"properties/{property_id}",
    dimensions=[Dimension(name="landingPage")],
    metrics=[
        Metric(name="activeUsers"),
        Metric(name="newUsers"),
        Metric(name="engagedSessions"),
    ],
    date_ranges=[DateRange(start_date=start_date_1.strftime("%Y-%m-%d"), end_date=end_date_1.strftime("%Y-%m-%d"))],
)
response_landing_pages = client.run_report(request_landing_pages)
top_landing_pages_data = [
    {
        'Landing Page': row.dimension_values[0].value,
        'Active Users': row.metric_values[0].value,
        'New Users': row.metric_values[1].value,
        'Engaged Sessions': row.metric_values[2].value
    }
    for row in response_landing_pages.rows[:10]
]
df_top_landing_pages = pd.DataFrame(top_landing_pages_data)
# Display top 10 landing pages
st.subheader("Top 10 Landing Pages")
st.dataframe(df_top_landing_pages)
# Display combined GA data
st.subheader("Month on Month Data")
st.dataframe(df_combined)
# Chart creation functions
def create_bar_chart(df, y_metric, title):
    return alt.Chart(df).mark_bar().encode(
        x=alt.X('Date Range:N', title='Date Range'),
        y=alt.Y(f'{y_metric}:Q', title='Count'),
        color=alt.Color('Channel:N', title='Channel')
    ).properties(width=150, height=300, title=title)
def create_line_chart(df, y_metric, title):
    return alt.Chart(df).mark_line().encode(
        x='Date:T',
        y=alt.Y(f'{y_metric}:Q', title=y_metric),
        color='DateRange:N'
    ).properties(width=700, height=300, title=title)
# Display charts side by side
col1, col2 = st.columns(2)
with col1:
    st.subheader("Active Users MoM")
    st.altair_chart(create_bar_chart(df_combined, 'Active Users', "Active Users"), use_container_width=True)
with col2:
    st.subheader("New Users MoM")
    st.altair_chart(create_bar_chart(df_combined, 'New Users', "New Users"), use_container_width=True)
# Fetch GSC Data

gsc_credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gsc_service_account"]
)
gsc_service = build('searchconsole', 'v1', credentials=gsc_credentials)


def fetch_gsc_data(start_date, end_date):
    request = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['date'],
        'rowLimit': 1000
    }
    response = gsc_service.searchanalytics().query(
        siteUrl='https://linfieldconstruction.co.uk/', body=request
    ).execute()
    
    return pd.DataFrame([
        {
            'Date': row['keys'][0],
            'Clicks': row['clicks'],
            'Impressions': row['impressions'],
            'CTR': row['ctr'],
            'Position': row['position']
        } for row in response.get('rows', [])
    ])
# Fetch and display GSC data
df_gsc_1 = fetch_gsc_data(start_date_1.strftime("%Y-%m-%d"), end_date_1.strftime("%Y-%m-%d"))
df_gsc_2 = fetch_gsc_data(start_date_2.strftime("%Y-%m-%d"), end_date_2.strftime("%Y-%m-%d"))
df_GSC_combined = pd.concat([df_gsc_1.assign(DateRange="Current Month"), df_gsc_2.assign(DateRange="Comparison Month")])
st.markdown("<h2>Google Search Console Data<h2>", unsafe_allow_html=True)
st.subheader("Month on Month GSC Data")
st.dataframe(df_GSC_combined)
# Display GSC charts side by side
col1, col2 = st.columns(2)
with col1:
    st.subheader("Clicks Over Time")
    st.altair_chart(create_line_chart(df_GSC_combined, 'Clicks', "Clicks Over Time"), use_container_width=True)
with col2:
    st.subheader("Impressions Over Time")
    st.altair_chart(create_line_chart(df_GSC_combined, 'Impressions', "Impressions Over Time"), use_container_width=True)


    import os

if not os.path.exists("service_account.json"):
    st.error("service_account.json not found!")
if not os.path.exists("gscservice_account.json"):
    st.error("gscservice_account.json not found!")
