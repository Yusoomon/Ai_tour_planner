import streamlit as st

from common import initialize_page

initialize_page(layout="centered")
st.title("Ready for the travel?")
st.subheader("Share us some information to make your travel plan more personalized!")

_, col_center, _ = st.columns([1, 5, 1])
with col_center:
    with st.container(border=True):
        st.markdown("### Profile Setup")
        with st.form("onboarding_form", border=False):
            nickname = st.text_input("Nickname", placeholder="Yusoomon")
            age = st.number_input("Age", min_value=1, max_value=100, value=50)
            nationality = st.text_input("Nationality", placeholder="Korean")
            destination = st.text_input("Destination", placeholder="Incheon")

            submit_btn = st.form_submit_button(
                "Let's see what Ai thinks 👉", type="primary", width="stretch"
            )

            if submit_btn:
                if not nickname or not nationality:
                    st.error("Even the alien can't make the plans with this info..")
                    st.markdown("🧭🚦💬")
                else:
                    st.session_state["user_profile"] = {
                        "nickname": nickname,
                        "age": age,
                        "nationality": nationality,
                        "destination": destination,
                    }
                    st.switch_page("pages/3_Itinerary.py")
