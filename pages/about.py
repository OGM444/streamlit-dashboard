import streamlit as st
from navigation import make_sidebar
from forms.contact import contact_form

st.logo("assets/whd_logo.png")

make_sidebar()

@st.experimental_dialog("Contact Us")
def show_contact_form():
    contact_form()

st.title("Your Profile")


# --- HERO SECTION ---
col1, col2 = st.columns(2, gap="small", vertical_alignment="center")
with col1:
    st.image("assets/whd_logo.png", width=550)

with col2:
    st.title("Webhive Digital", anchor=False)
    st.write(
        "Digital Marketing Agency"
    )
    if st.button("✉️ Contact Us"):
        show_contact_form()