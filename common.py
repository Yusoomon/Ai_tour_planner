import streamlit as st

def initialize_page(layout="wide"):
    st.set_page_config(
        page_title="AI Travel Planner",
        page_icon="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/2708.png",
        layout=layout,
    )
    load_css()
    header()
    ui_hide()

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

def ui_hide():
    hide_all_ui = """
        <style>
        header, [data-testid="stHeader"] {
            visibility: hidden !important;
            height: 0px !important;
            padding: 0px !important;
        }
        
        [data-testid="stToolbar"] {
            display: none !important;
        }
        
        #MainMenu {
            visibility: hidden !important;
            display: none !important;
        }
        
        footer {
            visibility: hidden !important;
            display: none !important;
        }
        
        .block-container {
            padding-top: 2rem !important;
        }
        </style>
    """
    st.markdown(hide_all_ui, unsafe_allow_html=True)

def footer():
    st.markdown(
    """
    <div class="custom-footer">
        © 2026 Yusoomon, All rights reserved. Designed by Minhyuk
    </div>
    """, unsafe_allow_html=True)

def header():
    st.markdown(
        f"""
        <div class ="app-header" style="
            position: fixed;
            top: 0;
            left: 0;
            width:100%;
            padding: 6px 16px;
            display: flex;
            align-items: center;
            box-sizing: border-box;
            height: 3rem;
            z-index: 999999;
        ">
            <img src='app/static/images/KOMPASS_LOGO.png' alt='Logo' style='height: 2.5rem; margin-right: 10px;'>
            <span style='margin: 0 80px 0 auto; font-size: 13px; font-weight: 100;'>Free App</span>
        </div>
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
