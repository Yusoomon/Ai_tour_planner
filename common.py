import streamlit as st


def initialize_page(layout="wide"):
    st.set_page_config(
        page_title="AI Travel Planner",
        page_icon="✈️",
        layout=layout,
    )
    load_css()
    header()

    defaults = {
        "user_profile": {},
        "itinerary_routes": None,
        "chat_history": [],
        "pending_chat_prompt": "",
        "expander_open": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def header():
    st.markdown(
        """
        <div class="app-header" style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            box-sizing: border-box;
            z-index: 999999;
        ">
            <a href="app.py" target="_self" class="brand">
            <img src='https://cdn-icons-png.flaticon.com/512/201/201623.png' alt='Logo' style='height: 40px; margin-right: 15px;'>
            <h1 style='margin: 0; font-size: 24px;'>AI Tour Planner</h1>
            </a>
            <span style='margin: 0 75px 0 auto; font-size: 15px; font-weight: 100;'>Free App</span>
        </div>
        <div style="margin-top: 60px;"></div>
        """, unsafe_allow_html=True,
    )

    if st.button("Login", key="header_login", type="tertiary"):
        login_dialog()


@st.dialog("Login")
def login_dialog():
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Sign in", type="primary", width="stretch"):
        if email and password:
            st.success("Login successful")
            st.session_state["user_profile"]["email"] = email
            st.rerun()
        else:
            st.error("Enter your email and password.")

def load_css():
    with open("assets/style.css", "r", encoding="UTF-8") as css_file:
        st.markdown(
            f"<style>{css_file.read()}</style>",
            unsafe_allow_html=True,
        )
