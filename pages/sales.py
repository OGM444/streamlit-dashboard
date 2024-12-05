import os
from nav import make_sidebar
import pandas as pd
import streamlit as st
import altair as alt
import numpy as np
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

# Initialize GA4 client
ga4_credentials = service_account.Credentials.from_service_account_info(
    st.secrets["ga4_service_account"],
    scopes=["https://www.googleapis.com/auth/analytics.readonly"]
)
client = BetaAnalyticsDataClient(credentials=ga4_credentials)

# Streamlit Setup
st.logo("assets/whd_logo.png")
make_sidebar()
st.title("📊 Product Sales Dashboard")
st.divider()
st.sidebar.header("Select Date Range here👇")

# Google Analytics property ID
property_id = "389980673"

# Date range sidebar
start_date_current = st.sidebar.date_input("Start date of current month", pd.to_datetime("2024-01-18"))
end_date_current = st.sidebar.date_input("End date of current month", pd.to_datetime("today"))
start_date_compared = st.sidebar.date_input("Start date of month to compare", pd.to_datetime("2024-01-18"))
end_date_compared = st.sidebar.date_input("End date of month to compare", pd.to_datetime("today"))



# Date Sales data
def fetch_sales_data(date_range, date_label):
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="itemName"),
            Dimension(name="itemCategory")
        ],
        metrics=[
            Metric(name="itemsViewed"),
            Metric(name="itemsPurchased"),
            Metric(name="itemRevenue"),
            Metric(name="purchaseToViewRate")
        ],
        date_ranges=[date_range]
    )
    response = client.run_report(request)
    data = []
    for row in response.rows:
        data.append({
            'Date Range': date_label,
            'Product': row.dimension_values[0].value,
            'Category': row.dimension_values[1].value,
            'Views': int(row.metric_values[0].value),
            'Items Sold': int(row.metric_values[1].value),
            'Revenue': float(row.metric_values[2].value),
            'Conversion Rate': float(row.metric_values[3].value) * 100
        })
    return data

# Fetch and combine data
combined_data = fetch_sales_data(
    DateRange(start_date=start_date_current.strftime("%Y-%m-%d"), end_date=end_date_current.strftime("%Y-%m-%d")), 
    start_date_current.strftime('%B %Y')
)
combined_data += fetch_sales_data(
    DateRange(start_date=start_date_compared.strftime("%Y-%m-%d"), end_date=end_date_compared.strftime("%Y-%m-%d")), 
    start_date_compared.strftime('%B %Y')
)

# Create DataFrame for combined sales data
df_combined = pd.DataFrame(combined_data)

def fetch_sales_data(date_range, date_label):
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="itemName"),
            Dimension(name="itemCategory")
        ],
        metrics=[
            Metric(name="itemsViewed"),
            Metric(name="totalRevenue"),
            Metric(name="itemRevenue"),
            Metric(name="purchaseToViewRate")
        ],
        date_ranges=[date_range]
    )
    response = client.run_report(request)
    data = []
    for row in response.rows:
        data.append({
            'Date Range': date_label,
            'Product': row.dimension_values[0].value,
            'Category': row.dimension_values[1].value,
            'Views': int(row.metric_values[0].value),
            'Items Sold': int(row.metric_values[1].value),
            'Revenue': float(row.metric_values[2].value),
            'Conversion Rate': float(row.metric_values[3].value) * 100
        })
    return data


# Calculate and display summary metrics
current_month = df_combined[df_combined['Date Range'] == start_date_current.strftime('%B %Y')]
previous_month = df_combined[df_combined['Date Range'] == start_date_compared.strftime('%B %Y')]

metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
with metrics_col1:
    current_revenue = current_month['Revenue'].sum()
    previous_revenue = previous_month['Revenue'].sum()
    revenue_change = ((current_revenue - previous_revenue) / previous_revenue) * 100
    st.metric("Revenue", f"£{current_revenue:,.2f}", f"{revenue_change:,.1f}%")

with metrics_col2:
    current_units = current_month['Items Sold'].sum()
    previous_units = previous_month['Items Sold'].sum()
    units_change = ((current_units - previous_units) / previous_units) * 100
    st.metric("Items Sold", f"{current_units:,}", f"{units_change:,.1f}%")


with metrics_col3:
    current_avg_order = current_revenue / current_units
    previous_avg_order = previous_revenue / previous_units
    avg_order_change = ((current_avg_order - previous_avg_order) / previous_avg_order) * 100
    st.metric("Avg Order Value", f"£{current_avg_order:.2f}", f"{avg_order_change:,.1f}%")
              


# Function to fetch sales data from GA4
def fetch_sales_data(start_date, end_date):
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="purchaseRevenue")],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)]
    )
    response = client.run_report(request)
    
    sales_data = [
        {
            'Date': pd.to_datetime(row.dimension_values[0].value),
            'Sales': float(row.metric_values[0].value)
        }
        for row in response.rows
    ]
    return pd.DataFrame(sales_data)

# Fetch sales data for the selected date range
df_sales_current = fetch_sales_data(
    start_date_current.strftime("%Y-%m-%d"), end_date_current.strftime("%Y-%m-%d")
).assign(DateRange="Current Month")

df_sales_comparison = fetch_sales_data(
    start_date_compared.strftime("%Y-%m-%d"), end_date_compared.strftime("%Y-%m-%d")
).assign(DateRange="Comparison Month")

# Combine data for comparison
df_sales_combined = pd.concat([df_sales_current, df_sales_comparison])


# Sales over time chart
sales_line_chart = alt.Chart(df_sales_combined).mark_line().encode(
    x=alt.X('Date:T', title='Date'),
    y=alt.Y('Sales:Q', title='Sales (Revenue)'),
    color=alt.Color('DateRange:N', title='Date Range')
).properties(
    width=700, height=400
)

st.subheader("Sales Over Time")

# Display the chart
st.altair_chart(sales_line_chart, use_container_width=True)




# Fetch top selling products data
def fetch_top_products(start_date, end_date):
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="itemName"),
            Dimension(name="itemCategory")
        ],
        metrics=[
            Metric(name="itemsPurchased")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)]
    )
    response = client.run_report(request)
    data = [
        {
            'Product': row.dimension_values[0].value,
            'Category': row.dimension_values[1].value,
            'Sales': float(row.metric_values[0].value)
        }
        for row in response.rows[:10]
    ]
    return pd.DataFrame(data).sort_values('Sales', ascending=False)

# Display top selling products
df_top_products = fetch_top_products(
    start_date_current.strftime("%Y-%m-%d"),
    end_date_current.strftime("%Y-%m-%d")
)
st.subheader("Top 10 Products by Revenue")
st.dataframe(df_top_products)


# Revenue by Category Test

st.subheader("Revenue By Category")

def create_revenue_table(df):
    revenue_table = df.groupby('Category').agg(
        Revenue=('Revenue', 'sum')
    ).reset_index()
    revenue_table = revenue_table.dropna(subset=['Category'])
    revenue_table = revenue_table[revenue_table['Category'] != '']
    # Sort by Revenue in descending order
    revenue_table = revenue_table.sort_values('Revenue', ascending=False)
    return revenue_table

@st.cache_data(show_spinner=False)
def split_frame(input_df, rows):
    df_batches = [input_df.iloc[i:i + rows] for i in range(0, len(input_df), rows)]
    return df_batches

revenue_table = create_revenue_table(df_combined)

if "page_size" not in st.session_state:
    st.session_state.page_size = 10
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

batch_size = st.session_state.page_size
total_pages = len(revenue_table) // batch_size if len(revenue_table) % batch_size == 0 else (len(revenue_table) // batch_size) + 1
current_page = st.session_state.current_page

pages = split_frame(revenue_table, batch_size)
page_data = pages[current_page - 1]

# Modified indexing logic
page_data.index = range(1, len(page_data) + 1)

with st.container():
    st.dataframe(page_data, use_container_width=True)
    st.markdown(f"Page **{current_page}** of **{total_pages}**")
    pagination_col1, pagination_col2 = st.columns([3, 1])
    
    with pagination_col1:
        st.session_state.page_size = st.selectbox(
            "Page Size", options=[10, 25, 50, 100], index=[10, 25, 50, 100].index(batch_size)
        )
    
    with pagination_col2:
        st.session_state.current_page = st.number_input(
            "Page", min_value=1, max_value=total_pages, step=1, value=current_page
        )