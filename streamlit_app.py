import streamlit as st
from time import sleep
from navigation import make_sidebar

st.logo("assets/whd_logo.png")

make_sidebar()

st.title("Welcome to the Webhive Portal")

st.write("Please log in to continue (username `test`, password `test`).")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Log in", type="primary"):
    if username == "test" and password == "test":
        st.session_state.logged_in = True
        st.success("Logged in successfully!")
        sleep(0.5)
        st.switch_page("pages/about.py")
    else:
        st.error("Incorrect username or password")