import streamlit as st

from common import initialize_page

initialize_page(layout="centered")

with st.container():
    st.title("Easy plan, Cozy vacay")
    st.subheader("Optimize your travel plan with AI")

    with st.container():
        co1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with co1:
            st.markdown(
                """
                <div class="step-card">
                    <div class="step-number">1</div>
                    <div class="step-label">Profile</div>
                </div>
                """, unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                """
                <div class="step-card">
                    <div class="step-number">2</div>
                    <div class="step-label">Preferences</div>
                </div>
                """, unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                """
                <div class="step-card">
                    <div class="step-number">3</div>
                    <div class="step-label">Prototype</div>
                </div>
                """, unsafe_allow_html=True,
            )
        with col4:
            st.markdown(
                """
                <div class="step-card">
                    <div class="step-number">4</div>
                    <div class="step-label">Finalize</div>
                </div>
                """, unsafe_allow_html=True,
            )

    if st.button("Start Planning 👉", type="primary", use_container_width=True):
        st.switch_page("pages/2_Profile.py")
