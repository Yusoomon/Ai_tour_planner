import streamlit as st
import datetime
import time

from common import initialize_page

initialize_page(layout="centered")
st.session_state.setdefault("profile_step", 1)

def render_progress(step):
    progress = min(step / 3 * 100, 100)
    st.markdown(
        f'<div class="profile-progress" style="--progress: {progress:.0f}%">STEP {step} / 3</div>',
        unsafe_allow_html=True,
    )


def render_navigation(step, submit_label, in_form=True):
    _, previous_col, next_col = st.columns([2, 1.25, 2.25])
    with previous_col:
        button = st.form_submit_button if in_form else st.button
        previous = button("← Previous", disabled=step == 1, key=f"previous_{step}")
    with next_col:
        submit = button(
            submit_label,
            type="primary",
            key=f"submit_{step}",
            width="stretch",
        )
    return previous, submit


render_progress(st.session_state["profile_step"])

profile_step = st.session_state["profile_step"]
_, content_area, _ = st.columns([0.35, 5, 0.35])

with content_area:
    if profile_step == 1:
        st.markdown('<div class="profile-title">Tell us about yourself</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="profile-copy">The more you tell us, the better AI results</div>',
            unsafe_allow_html=True,
        )

        with st.form("profile_form", border=False):
            profile = {}
            fields = {
                "nickname": ("Nickname", "Yusoomon"),
                "age": ("Age", 50),
                "nationality": ("Nationality", "Korean"),
                "visit_purpose": ("Visit Purpose", "Tourism"),
            }

            for left_field, right_field in (("nickname", "age"), ("nationality", "visit_purpose")):
                left_col, right_col = st.columns(2)
                for column, field_name in zip((left_col, right_col), (left_field, right_field)):
                    with column:
                        label, default = fields[field_name]
                        if field_name == "age":
                            profile[field_name] = st.number_input(
                                f"**{label}**", min_value=1, max_value=100, value=default
                            )
                        else:
                            profile[field_name] = st.text_input(
                                f"**{label}**", placeholder=default
                            )

            profile["destination"] = st.text_input(
                "**Destination**", placeholder="Seoul, South Korea"
            )
            _, submit_btn = render_navigation(1, "Next →")

            if submit_btn:
                if not profile["nickname"] or not profile["nationality"]:
                    st.error("Please enter your nickname and nationality.")
                else:
                    st.session_state["user_profile"] = profile
                    st.session_state["profile_step"] = 2
                    st.rerun()
    elif profile_step == 2:
        st.markdown('<div class="profile-title">What kind of trip are you planning?</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="profile-copy">Choose your preferences and we will build the right route for you.</div>',
            unsafe_allow_html=True,
        )

        with st.form("preferences_form", border=False):
            st.markdown("**Style & Interests**")
            interest_options = ["History & Culture", "Food & Cafe", "Shopping", "Nature"]
            interest_cols = st.columns([1.2, 0.9, 0.9, 0.7])
            interests = []
            for index, interest in enumerate(interest_options):
                with interest_cols[index]:
                    if st.checkbox(interest, value=index == 0, key=f"interest_{index}"):
                        interests.append(interest)

            companion_col, group_col, _ = st.columns([2, 0.8, 1.2])
            with companion_col:
                companion = st.selectbox(
                    "**Companions**",
                    ["Solo", "Friends", "Couple", "Family"],
                    key="profile_companion",
                )
            with group_col:
                group_size = st.number_input(
                    "**Group Size**",
                    min_value=1,
                    max_value=20,
                    value=1,
                    step=1,
                    format="%d",
                )

            st.markdown("**Transport Option**")
            transport = st.radio(
                "Transport Option",
                [
                    "Love sightseeing by walking",
                    "Less walking, but not skip sightseeing",
                    "Moving must be ASAP",
                ],
                label_visibility="collapsed",
            )
            start_col, end_col = st.columns(2)
            with start_col:
                start_date = st.date_input("**Start Date**", value=datetime.date.today())
            with end_col:
                end_date = st.date_input(
                    "**End Date**", value=datetime.date.today() + datetime.timedelta(days=3)
                )

            previous, submit_btn = render_navigation(2, "Build Routes →")

            if previous:
                st.session_state["profile_step"] = 1
                st.rerun()
            if submit_btn:
                if end_date < start_date:
                    st.error("You must be an alien")
                else:
                    st.session_state["user_profile"].update(
                        {
                            "interests": interests,
                            "companion": companion,
                            "group_size": 1 if companion == "Solo" else max(group_size, 2),
                            "transport": transport,
                            "start_date": start_date,
                            "end_date": end_date,
                        }
                    )
                    with st.spinner("Finding routes that fit your trip..."):
                        time.sleep(0.8)
                    st.session_state["profile_step"] = 3
                    st.rerun()
    else:
        st.markdown('<div class="route-page-marker"></div>', unsafe_allow_html=True)
        st.markdown('<div class="profile-title">AI found a few routes for you</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="profile-copy">You are almost there!</div>',
            unsafe_allow_html=True,
        )

        routes = [
            {
                "name": "Best Match",
                "summary": "A balanced route with culture, food, and relaxed pacing.",
                "details": "3 days · Moderate walking",
            },
            {
                "name": "Minimal Walk",
                "summary": "A comfortable plan focused on short distances and easy transfers.",
                "details": "3 days · Light walking",
            },
            {
                "name": "Cultural",
                "summary": "A deeper look at historic places, neighborhoods, and local stories.",
                "details": "3 days · More walking",
            },
        ]

        selected_route = st.session_state.get("selected_route")
        route_cols = st.columns(3, gap="medium")
        for index, route in enumerate(routes):
            is_selected = selected_route == route["name"]
            with route_cols[index]:
                with st.container(border=True):
                    if is_selected:
                        st.markdown('<div class="selected-route-marker"></div>', unsafe_allow_html=True)
                    st.markdown('<div class="route-image-placeholder"></div>', unsafe_allow_html=True)
                    st.markdown(f"### {route['name']}")
                    st.caption(route["details"])
                    st.write(route["summary"])
                    if st.button(
                        "Selected route" if is_selected else "Use this route",
                        key=f"route_{index}",
                        type="primary" if is_selected else "secondary",
                        width="stretch",
                    ):
                        st.session_state["selected_route"] = route["name"]
                        st.rerun()

        if selected_route:
            if st.button("Continue with selected route →", type="primary", width="stretch"):
                st.switch_page("pages/3_Itinerary.py")

        if st.button(
            "← Back to preferences", key="back_to_preferences", type="secondary"):
            st.session_state["profile_step"] = 2
            st.rerun()
