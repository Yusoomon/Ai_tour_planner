import streamlit as st


def initialize_page(layout="wide"):
    st.set_page_config(
        page_title="AI Travel Planner",
        page_icon="✈️",
        layout=layout,
        initial_sidebar_state="collapsed",
    )
    load_css()

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


def load_css():
    with open("assets/style.css", "r", encoding="UTF-8") as css_file:
        st.markdown(
            f"<style>{css_file.read()}</style>",
            unsafe_allow_html=True,
        )
