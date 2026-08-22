import streamlit as st
import datetime
import time
import requests
import json
import os
import folium
from folium import plugins

from google import genai
from google.genai import types
from dotenv import load_dotenv
from streamlit_folium import st_folium
from common import initialize_page

load_dotenv()
initialize_page(layout="centered")
st.session_state.setdefault("profile_step", 1)

def fetch_tourapi_places(keyword):
    api_key = os.environ.get("TOUR_API_KEY", "YOUR_TOUR_API_KEY")
    url = "http://apis.data.go.kr/B551011/EngService1/searchKeyword1"

    params = {
        "serviceKey": api_key,
        "numOfRows": 10,
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "AITourPlanner",
        "_type": "json",
        "keyword": keyword,
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            items = (
                data.get("response", {})
                .get("body", {})
                .get("items", {})
                .get("item", [])
            )
            return items if isinstance(items, list) else [items]
    except Exception as e:
        st.warning(f"TourAPI fetch warning: {e}")
    return []

def generate_routes_with_gemini(user_profile, tour_places_sample):
    # GEMINI api 호출 함수 및 프롬프트 (수정 중)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Check your .env file.")
    client = genai.Client(api_key=api_key)

    prompt = f"""
        You are an expert AI Travel Planner API for foreign tourists. Your task is to generate a highly optimized, geographically logical travel itinerary based on the user's profile and preferences. 

        ### CRITICAL REQUIREMENTS:

        1. **Language**: Both this prompt and your final output must be 100% in English.
        2. **Geographical Logic (Routing)**: You must calculate the actual spatial distance and routing. Places visited sequentially must flow naturally along a path (e.g., Station -> Nearby Gate -> Stadium). Avoid chaotic zig-zag paths or backtracking.
        3. **Realistic Infrastructure & Safety**: Do not blindly follow walking preferences if the infrastructure does not support it. For example, if the companion is a family of 4 and the route lacks proper sidewalks, strictly exclude purely pedestrian recommendations and explain why in the options.
        4. **Multi-Modal Transit Options**: For EVERY movement between two destinations, you must provide at least 2 distinct transit modes. Rank them by priority based on infrastructure, convenience, and user preference, and provide a clear, concise reason for the ranking.
        5. **Preference Trade-off & Web Browsing**: If user preferences conflict (e.g., dislikes walking but prefers sight-seeing), use your search tool capabilities to trace actual tourist behaviors and local data. Find the optimal compromise that actual travelers prefer.
        6. **API & Speed Constraint**: Output strictly in JSON format. Keep descriptions concise and straightforward to maximize performance and token speed. Do not include any markdown block text (like ```json) outside the pure JSON payload.

        ### INPUT FORMAT FROM USER:

        The user will provide input in the following JSON structure:
        {{
            "user_info": {{
            "age": "string",
            "nationality": "string",
            "purpose": "string",
            "destination": "string"
            }},
            "style": {{
            "travel_style": ["string"],
            "companions": {{"type": "string", "count": integer}},
            "transport_preference": "string",
            "duration_days": integer
            }}
        }} 

        ### USER DATA:
        {json.dumps(user_profile, ensure_ascii=True)}

        ### TOURISM API SAMPLE PLACES:
        {json.dumps(tour_places_sample, ensure_ascii=True)}

        ### OUTPUT JSON STRUCTURE (Strictly Follow This Schema):
        Generate exactly 3 route options.

        [
            {{
            "name": "string",
            "route_type": "Best Match | Minimal Walk | Cultural | Sightseeing | Convenient",
            "summary": "One short sentence introducing this route",
            "walking_distance_miles": 4.0,
            "itinerary": [
                {{
                    "day": 1,
                    "schedule": [
                        {{
                            "sequence": 1,
                            "place_name": "string",
                            "activity": "string",
                            "lat": 37.5796,
                            "lng": 126.9770
                        }},
                        {{
                            "sequence": 2,
                            "transit_from": "previous_place",
                            "transit_options": [
                                {{
                                    "rank": 1,
                                    "mode": "string",
                                    "reason": "string"
                                }},
                                {{
                                    "rank": 2,
                                    "mode": "string",
                                    "reason": "string"
                                }}
                            ]
                        }}
                    ]
                }}
            ]
            }}
        ]
    """

    response = client.models.generate_content(
        # 3.7 트래픽이 많아서 3.6 사용중
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )

    return json.loads(response.text)


def get_route_places(route, tour_places_sample):
    # 좌표 정보 매핑
    sample_by_title = {
        str(item.get("title", "")).strip().lower(): item
        for item in tour_places_sample
        if item.get("title")
    }
    places = []
    for day in route.get("itinerary", []):
        for schedule in day.get("schedule", []):
            place_name = schedule.get("place_name")
            if not place_name:
                continue
            sample = sample_by_title.get(str(place_name).strip().lower(), {})
            try:
                lat = float(schedule.get("lat") or sample.get("mapy"))
                lng = float(schedule.get("lng") or sample.get("mapx"))
            except (TypeError, ValueError):
                continue
            places.append(
                {
                    "name": place_name,
                    "lat": lat,
                    "lng": lng,
                    "day": day.get("day", 1),
                }
            )
    return places


def render_route_map(route, tour_places_sample, map_key):
    places = get_route_places(route, tour_places_sample)
    if not places:
        st.info("Map data is unavailable for this route.")
        return

    route_map = folium.Map(
        location=[places[0]["lat"], places[0]["lng"]],
        zoom_start=12,
        control_scale=True,
        attr=" ",
    )
    day_colors = ["#2f6e52", "#d97706", "#2563eb", "#c24174", "#7c3aed"]
    coordinates_by_day = {}
    for index, place in enumerate(places, 1):
        coordinate = [place["lat"], place["lng"]]
        day_number = place["day"]
        day_color = day_colors[(int(day_number) - 1) % len(day_colors)]
        coordinates_by_day.setdefault(day_number, []).append(coordinate)
        folium.Marker(
            coordinate,
            tooltip=f"{index}. {place['name']}",
            popup=place["name"],
            icon=plugins.BeautifyIcon(
                number=index,
                border_color=day_color,
                background_color=day_color,
                text_color="#ffffff",
                icon_shape="marker",
                inner_icon_style="font-size:12px; font-weight:bold;",
            ),
        ).add_to(route_map)
    for day_number, coordinates in coordinates_by_day.items():
        if len(coordinates) > 1:
            day_color = day_colors[(int(day_number) - 1) % len(day_colors)]
            folium.PolyLine(
                coordinates,
                color=day_color,
                weight=4,
                opacity=0.85,
                tooltip=f"Day {day_number}",
            ).add_to(route_map)
    st_folium(
        route_map,
        width="100%",
        height=180,
        returned_objects=[],
        key=map_key,
    )

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
        st.markdown(
            '<div class="profile-title">What kind of trip are you planning?</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="profile-copy">Choose your preferences and we will build the right route for you.</div>',
            unsafe_allow_html=True,
        )

        with st.form("preferences_form", border=False):
            st.markdown("**Style & Interests**")
            interest_options = [
                "History & Culture",
                "Food & Cafe",
                "Shopping",
                "Nature",
            ]
            interest_cols = st.columns([1.2, 0.9, 0.9, 0.7])
            interests = []
            for index, interest in enumerate(interest_options):
                with interest_cols[index]:
                    if st.checkbox(
                        interest, value=index == 0, key=f"interest_{index}"
                    ):
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
                start_date = st.date_input(
                    "**Start Date**", value=datetime.date.today()
                )
            with end_col:
                end_date = st.date_input(
                    "**End Date**",
                    value=datetime.date.today() + datetime.timedelta(days=3),
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
                            "group_size": (
                                1 if companion == "Solo" else max(group_size, 2)
                            ),
                            "transport": transport,
                            "start_date": str(start_date),
                            "end_date": str(end_date),
                        }
                    )

                    with st.spinner("Connecting to Korea Tourism API & Gemini AI..."):
                        try:
                            destination = st.session_state["user_profile"].get(
                                "destination", "Seoul"
                            )
                            # 공공데이터포털 조회
                            tour_places = fetch_tourapi_places(
                                destination or "Seoul"
                            )
                            sample_items = [
                                {
                                    "title": item.get("title"),
                                    "addr1": item.get("addr1"),
                                    "mapx": item.get("mapx"),
                                    "mapy": item.get("mapy"),
                                }
                                for item in tour_places[:5]
                            ]
                            st.session_state["route_map_places"] = sample_items

                            # Gemini API 호출 및 JSON 생성
                            generated_routes = generate_routes_with_gemini(
                                st.session_state["user_profile"], sample_items
                            )
                            if not isinstance(generated_routes, list):
                                raise ValueError(
                                    "Gemini returned a non-list route response: "
                                    f"{type(generated_routes).__name__}"
                                )
                            st.session_state["generated_routes"] = generated_routes
                            st.session_state.pop("route_generation_error", None)

                        except Exception as e:
                            st.session_state["route_generation_error"] = repr(e)
                            st.session_state["generated_routes"] = []

                    st.session_state["profile_step"] = 3
                    st.rerun()
    else:
        st.markdown(
            '<div class="route-page-marker"></div>', unsafe_allow_html=True
        )
        st.markdown(
            '<div class="profile-title">AI found a few routes for you</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="profile-copy">You are almost there!</div>',
            unsafe_allow_html=True,
        )

        # 실시간 API 생성 데이터 로드
        routes = st.session_state.get("generated_routes", [])
        route_map_places = st.session_state.get("route_map_places", [])
        route_error = st.session_state.get("route_generation_error")
        if route_error:
            st.error("Route generation failed. The exact error is shown below.")
            st.code(route_error)

        selected_route = st.session_state.get("selected_route")
        route_cols = st.columns(3, gap="medium")

        for index, route in enumerate(routes[:3]):
            route_name = route.get("name") or route.get("route_type", "Recommended Route")
            route_type = route.get("route_type") or route_name
            itinerary = route.get("itinerary", [])
            place_count = sum(
                1
                for day in itinerary
                for schedule in day.get("schedule", [])
                if schedule.get("place_name")
            )
            duration_days = len(itinerary)
            walking_distance = route.get("walking_distance_miles", "-")
            walking_text = (
                f"{walking_distance:g} mi" if isinstance(walking_distance, (int, float)) else str(walking_distance)
            )
            is_selected = selected_route == route_name
            with route_cols[index]:
                with st.container(border=True):
                    map_marker = '<div class="selected-route-marker"></div>' if is_selected else ""
                    st.markdown(map_marker, unsafe_allow_html=True)
                    with st.container():
                        render_route_map(route, route_map_places, f"route_map_{index}")
                    st.markdown(f'<div class="route-type">{route_type}</div>', unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="route-details">{duration_days} days / {place_count} places to see / {walking_text} walking distance</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="route-summary">{route.get("summary", "A route tailored to your travel preferences.")}</div>',
                        unsafe_allow_html=True,
                    )

                    if st.button(
                        "Selected route" if is_selected else "Use this route",
                        key=f"route_{index}",
                        type="primary" if is_selected else "secondary",
                        width="stretch",
                    ):
                        st.session_state["selected_route"] = route_name
                        st.session_state["chosen_route_data"] = route
                        st.rerun()

        if selected_route:
            if st.button(
                "Continue with selected route →",
                type="primary",
                width="stretch",
            ):
                st.switch_page("pages/3_Itinerary.py")

        if st.button(
            "← Back to preferences", key="back_to_preferences", type="secondary"
        ):
            st.session_state["profile_step"] = 2
            st.rerun()
