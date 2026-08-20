import datetime

import folium
import streamlit as st
from folium import plugins
from streamlit_folium import st_folium

from api_pipeline.pipe import pipe
from common import initialize_page


initialize_page()


def render_control_panel(col_left):
    profile = st.session_state["user_profile"]

    with col_left:
        st.markdown("### Travel Details")
        with st.expander(
            "Trip Preferences & Constraints", expanded=st.session_state["expander_open"]
        ):
            style = st.multiselect(
                "Style & Purpose",
                [
                    "History & Culture",
                    "Food & Cafe",
                    "Shopping",
                    "Nature & Relaxation",
                    "filming location",
                ],
                default=["History & Culture"],
            )

            comp_col1, comp_col2 = st.columns([2, 1])
            with comp_col1:
                companion = st.selectbox(
                    "Companions",
                    [
                        "Solo",
                        "Friends",
                        "Couple",
                        "Family w. parents",
                        "Family w. kids",
                    ],
                    key="companion_select",
                )
            with comp_col2:
                default_group_size = 1 if companion == "Solo" else 2
                group_size = st.number_input(
                    "Group Size",
                    min_value=1,
                    max_value=20,
                    value=default_group_size,
                    disabled=(companion == "Solo"),
                )

            with st.container(border=True):
                transport = st.radio(
                    "Transport Option",
                    [
                        "Love sightseeing by walking",
                        "Less walking, but not skip sightseeing",
                        "Moving must be ASAP",
                    ],
                    index=0,
                )

            st.markdown("**Trip Schedule**")
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                start_date = st.date_input("Start Date")
                start_time = st.time_input("Start Time", value=datetime.time(9, 0))
            with date_col2:
                end_date = st.date_input("End Date")
                end_time = st.time_input("End Time", value=datetime.time(21, 0))

            duration = 1
            if end_date < start_date:
                st.error(
                    "Error: End Date cannot be earlier than Start Date! or You must be a time traveler"
                )
            else:
                start_dt = datetime.datetime.combine(start_date, start_time)
                end_dt = datetime.datetime.combine(end_date, end_time)
                duration = (end_date - start_date).days + 1
                total_hours = round((end_dt - start_dt).total_seconds() / 3600, 1)
                st.caption(f"Total Duration: **{duration} Day(s)** ({total_hours} hrs)")

            extra_notes = st.text_area(
                "Specific Requests",
                placeholder="e.g. Hurt my leg, so minimize walking. Prefer indoor spots if rainy.",
            )

            generate_routes_btn = st.button(
                "Generate Top 5 Route Options", type="primary", width="stretch"
            )

            if generate_routes_btn:
                with st.spinner("AI is having a hard time"):
                    schedule_info = f"Arrival: {start_date} {start_time.strftime('%H:%M')}, Departure: {end_date} {end_time.strftime('%H:%M')}"
                    combined_interests = f"{', '.join(style)}; Companion: {companion} ({group_size} people), Transport: {transport}, Schedule: {schedule_info}, Notes: {extra_notes}"

                    result = pipe(
                        nationality=profile["nationality"],
                        age=f"{profile['age']}",
                        interests=combined_interests,
                        duration_total=schedule_info,
                        destination=profile["destination"],
                    )
                    st.session_state["expander_open"] = False
                    st.session_state["itinerary_routes"] = result
                    st.rerun()


def render_chat_assistant(col_left):
    with col_left:
        st.markdown("### Real-Time AI Assistant")
        with st.container(border=True):
            st.caption("Ask questions or adjust your itinerary dynamically.")
            st.write("**Quick Adjustments:**")
            chip1, chip2, chip3 = st.columns(3)
            with chip1:
                if st.button("📌 Reduce Walking", width="stretch"):
                    st.session_state["pending_chat_prompt"] = "Please adjust the itinerary to minimize walking distance."
            with chip2:
                if st.button("☕ Add Cafe Stop", width="stretch"):
                    st.session_state["pending_chat_prompt"] = "Can you add a famous local cafe stop between destinations?"
            with chip3:
                if st.button("☔ Switch Indoor", width="stretch"):
                    st.session_state["pending_chat_prompt"] = "In case of rain, please replace outdoor spots with indoor activities."

            chat_container = st.container(height=280)
            with chat_container:
                for message in st.session_state["chat_history"]:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])

            user_input = st.chat_input("Type your request here...")
            if not user_input and st.session_state["pending_chat_prompt"]:
                user_input = st.session_state["pending_chat_prompt"]
                st.session_state["pending_chat_prompt"] = ""

            if user_input:
                st.session_state["chat_history"].append(
                    {"role": "user", "content": user_input}
                )
                st.session_state["chat_history"].append(
                    {
                        "role": "assistant",
                        "content": f"Got it! Adjusting your route based on: '{user_input}'.",
                    }
                )
                st.rerun()


def render_map_and_routes(col_right):
    routes = st.session_state["itinerary_routes"]

    with col_right:
        st.markdown("### Interactive Route Map")
        with st.container(border=True):
            if not routes:
                st.info("Fill out the preferences on the left and click **'Generate Top 5 Route Options'**!")
                default_spots = [
                    {"name": "Error1", "lat": 37.5796, "lng": 126.9770},
                    {"name": "Error2", "lat": 37.5512, "lng": 126.9882},
                    {"name": "Error3", "lat": 37.5826, "lng": 126.9831},
                    {"name": "Error4", "lat": 37.5636, "lng": 126.9834},
                ]
                m = folium.Map(location=[37.5665, 126.9780], zoom_start=12)
                for spot in default_spots:
                    folium.Marker(
                        [spot["lat"], spot["lng"]],
                        popup=spot["name"],
                        tooltip=spot["name"],
                        icon=folium.Icon(color="blue", icon="star"),
                    ).add_to(m)
                st_folium(m, width="100%", height=380)
            else:
                map_locations = []
                count = []
                for day_info in routes.get("itinerary", []):
                    temp = 0
                    for place in day_info.get("places", []):
                        if place.get("lat") and place.get("lng"):
                            map_locations.append({"name": place.get("place_name"), "lat": place.get("lat"), "lng": place.get("lng")})
                            temp += 1
                    count.append(temp)

                if map_locations:
                    m = folium.Map(location=[map_locations[0]["lat"], map_locations[0]["lng"]], zoom_start=13)
                    day_colors = ["#FF5555", "#7F5CFF", "#5CFF64", "#FF4AB4", "#5CECFF"]
                    current_day_idx = 0
                    remaining_count = count[current_day_idx] if count else 0
                    current_color = day_colors[current_day_idx % len(day_colors)]
                    day_polylines = []
                    current_day_coords = []

                    for idx, loc in enumerate(map_locations, 1):
                        coord = [loc["lat"], loc["lng"]]
                        if remaining_count == 0 and current_day_idx < len(count) - 1:
                            if current_day_coords:
                                day_polylines.append({"coords": current_day_coords, "color": current_color})
                            current_day_coords = []
                            current_day_idx += 1
                            remaining_count = count[current_day_idx]
                            current_color = day_colors[current_day_idx % len(day_colors)]
                        current_day_coords.append(coord)
                        remaining_count -= 1
                        folium.Marker(
                            coord,
                            popup=f"{idx}. {loc['name']}",
                            tooltip=f"{idx}. {loc['name']}",
                            icon=plugins.BeautifyIcon(
                                number=idx,
                                border_color=current_color,
                                text_color="#000000",
                                icon_shape="marker",
                                inner_icon_style="margin-top:0; font-weight:bold;",
                            ),
                        ).add_to(m)

                    if len(current_day_coords) > 1:
                        day_polylines.append({"coords": current_day_coords, "color": current_color})
                    for poly in day_polylines:
                        if len(poly["coords"]) > 1:
                            folium.PolyLine(poly["coords"], color=poly["color"], weight=3, opacity=0.7).add_to(m)
                    st_folium(m, width="100%", height=380)

        st.markdown("### Recommended Route Options")
        tabs = st.tabs(["Best Match", "Minimal Walk", "Cultural", "Foodie", "Scenic"])
        for tab in tabs:
            with tab:
                if routes:
                    for day_info in routes.get("itinerary", []):
                        st.markdown(f"#### Day {day_info.get('day')}")
                        for p_idx, place in enumerate(day_info.get("places", []), 1):
                            with st.container(border=True):
                                img_col, info_col = st.columns([1, 4])
                                with img_col:
                                    img_url = place.get("image")
                                    if isinstance(img_url, str) and img_url.startswith(("http://", "https://")):
                                        try:
                                            st.image(img_url, width="stretch")
                                        except Exception:
                                            st.markdown("🚫", unsafe_allow_html=True)
                                    else:
                                        st.markdown("🚫", unsafe_allow_html=True)
                                with info_col:
                                    st.markdown(f"#### **{p_idx}. {place.get('place_name')}**")
                                    contact_num = place.get("contact", "0")
                                    contact_text = contact_num if contact_num and contact_num != "0" else "Contact unavailable"
                                    st.markdown(f"<div style='font-size: 15px; margin-top: -20px'>- Duration: {place.get('estimated_time')} &nbsp;|&nbsp; 📞 {contact_text}</div>", unsafe_allow_html=True)
                                    overview_text = place.get("overview", "")
                                    if overview_text:
                                        with st.expander("Overview", expanded=False):
                                            st.markdown(f"<div style='font-size: 0.85rem; color: #333;'>{overview_text}</div>", unsafe_allow_html=True)
                                st.markdown(f"<div style='font-size: 14px; color: gray; margin-top: -10px; margin-bottom: -10px;'>{place.get('address')} &nbsp;|&nbsp; <i>Estimated Time: {place.get('estimated_real_time')}</i></div>", unsafe_allow_html=True)
                                st.markdown(f"{place.get('reason')}")
                else:
                    st.caption("No route generated yet.")


def render():
    profile = st.session_state["user_profile"]
    st.title(f"{profile['nickname']} needs the best {profile['destination']} plan!")
    st.caption(f"Profile: {profile['nationality']}, {profile['age']} / Destination: {profile['destination']}")
    st.divider()
    col_left, col_right = st.columns([1, 1.5], gap="medium")
    render_control_panel(col_left)
    render_chat_assistant(col_left)
    render_map_and_routes(col_right)


if not st.session_state["user_profile"]:
    st.switch_page("pages/2_Profile.py")
else:
    render()
