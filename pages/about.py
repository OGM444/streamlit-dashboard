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

# Google Analytics property ID
property_id = "389980673"

# Date range input
start_date_1 = st.sidebar.date_input("Start date of current month", pd.to_datetime("2024-01-18"))
end_date_1 = st.sidebar.date_input("End date of current month", pd.to_datetime("today"))
start_date_2 = st.sidebar.date_input("Start date of month to compare", pd.to_datetime("2024-01-18"))
end_date_2 = st.sidebar.date_input("End date of month to compare", pd.to_datetime("today"))

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
            'Units Sold': int(row.metric_values[1].value),
            'Revenue': float(row.metric_values[2].value),
            'Conversion Rate': float(row.metric_values[3].value) * 100
        })
    return data

# Fetch and combine data
combined_data = fetch_sales_data(
    DateRange(start_date=start_date_1.strftime("%Y-%m-%d"), end_date=end_date_1.strftime("%Y-%m-%d")), 
    start_date_1.strftime('%B %Y')
)
combined_data += fetch_sales_data(
    DateRange(start_date=start_date_2.strftime("%Y-%m-%d"), end_date=end_date_2.strftime("%Y-%m-%d")), 
    start_date_2.strftime('%B %Y')
)

# Create DataFrame for combined sales data
df_combined = pd.DataFrame(combined_data)


# Calculate and display summary metrics
current_month = df_combined[df_combined['Date Range'] == start_date_1.strftime('%B %Y')]
previous_month = df_combined[df_combined['Date Range'] == start_date_2.strftime('%B %Y')]

metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
with metrics_col1:
    current_revenue = current_month['Revenue'].sum()
    previous_revenue = previous_month['Revenue'].sum()
    revenue_change = ((current_revenue - previous_revenue) / previous_revenue) * 100
    st.metric("Total Revenue", f"${current_revenue:,.2f}", f"{revenue_change:,.1f}%")

with metrics_col2:
    current_units = current_month['Units Sold'].sum()
    previous_units = previous_month['Units Sold'].sum()
    units_change = ((current_units - previous_units) / previous_units) * 100
    st.metric("Total Units Sold", f"{current_units:,}", f"{units_change:,.1f}%")

with metrics_col3:
    current_conv = current_month['Conversion Rate'].mean()
    previous_conv = previous_month['Conversion Rate'].mean()
    conv_change = current_conv - previous_conv
    st.metric("Avg Conversion Rate", f"{current_conv:.1f}%", f"{conv_change:,.1f}%")

with metrics_col4:
    current_avg_order = current_revenue / current_units
    previous_avg_order = previous_revenue / previous_units
    avg_order_change = ((current_avg_order - previous_avg_order) / previous_avg_order) * 100
    st.metric("Avg Order Value", f"${current_avg_order:.2f}", f"{avg_order_change:,.1f}%")

# Fetch top selling products
def fetch_top_products(start_date, end_date):
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="itemName"),
            Dimension(name="itemCategory")
        ],
        metrics=[
            Metric(name="itemRevenue")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)]
    )
    response = client.run_report(request)
    data = [
        {
            'Product': row.dimension_values[0].value,
            'Category': row.dimension_values[1].value,
            'Revenue': float(row.metric_values[0].value)
        }
        for row in response.rows[:10]
    ]
    return pd.DataFrame(data).sort_values('Revenue', ascending=False)

# Display top selling products
df_top_products = fetch_top_products(
    start_date_1.strftime("%Y-%m-%d"),
    end_date_1.strftime("%Y-%m-%d")
)
st.subheader("Top 10 Products by Revenue")
st.dataframe(df_top_products)

# Chart creation functions
def create_revenue_chart(df):
    return alt.Chart(df).mark_bar().encode(
        x=alt.X('Date Range:N', title='Period'),
        y=alt.Y('sum(Revenue):Q', title='Revenue ($)'),
        color=alt.Color('Category:N', title='Product Category')
    ).properties(
        width=400,
        height=300,
        title="Revenue by Category"
    )

def create_units_chart(df):
    return alt.Chart(df).mark_bar().encode(
        x=alt.X('Date Range:N', title='Period'),
        y=alt.Y('sum(Units Sold):Q', title='Units Sold'),
        color=alt.Color('Category:N', title='Product Category')
    ).properties(
        width=400,
        height=300,
        title="Units Sold by Category"
    )

def create_conversion_chart(df):
    return alt.Chart(df).mark_line(point=True).encode(
        x='Product:N',
        y=alt.Y('mean(Conversion Rate):Q', title='Conversion Rate (%)'),
        color='Date Range:N'
    ).transform_filter(
        alt.FieldOneOfPredicate(field='Product', oneOf=df['Product'].unique()[:5].tolist())
    ).properties(
        width=800,
        height=300,
        title="Top 5 Products Conversion Rate Comparison"
    )

# Display charts
col1, col2 = st.columns(2)
with col1:
    st.altair_chart(create_revenue_chart(df_combined), use_container_width=True)
with col2:
    st.altair_chart(create_units_chart(df_combined), use_container_width=True)

st.subheader("Product Conversion Rates")
st.altair_chart(create_conversion_chart(df_combined), use_container_width=True)
