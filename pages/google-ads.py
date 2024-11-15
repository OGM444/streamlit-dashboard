import streamlit as st
from streamlit_echarts import st_echarts
import datetime
from navigation import make_sidebar

st.logo("assets/whd_logo.png")

make_sidebar()


st.write("Your Dashboard")

option = {
    "xAxis": {
        "type": "category",
        "data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    },
    "yAxis": {"type": "value"},
    "series": [{"data": [820, 932, 901, 934, 1290, 1330, 1320], "type": "line"}],
}
st_echarts(
    options=option, height="400px",
)