import streamlit as st
import folium
import datetime
from streamlit_folium import st_folium
from pipe import pipe

# 페이지 기본 레이아웃
def init_app():
    st.set_page_config(page_title="AI Travel Planner", page_icon="✈️", layout="wide")
    
    defaults = {
        "step": 1,
        "user_profile": {},
        "itinerary_routes": None,
        "chat_history": [],
        "pending_chat_prompt": "",
        "expander_open": True
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# 첫화면
def render_onboarding():
    st.title("Easy plan, Cozy vacay")
    st.subheader("Welcome! Tell us just a little bit about you")

    _, col_center, _ = st.columns([1, 5, 1])
    with col_center:
        with st.container(border=True):
            st.markdown("### Profile Setup")
            # 인적사항 입력
            with st.form("onboarding_form", border=False):
                nickname = st.text_input("Nickname", placeholder="Yusoomon")
                age = st.number_input("Age", min_value=1, max_value=100, value=50)
                nationality = st.text_input("Nationality", placeholder="Korean")
                destination = st.text_input("Destination", placeholder="Incheon")
                
                submit_btn = st.form_submit_button("Start Planning", type="primary", use_container_width=True)

                if submit_btn:
                    if not nickname or not nationality:
                        st.error("Even the alien can't make the plans with this info..")
                    else:
                        st.session_state["user_profile"] = {
                            "nickname": nickname,
                            "age": age,
                            "nationality": nationality,
                            "destination": destination
                        }
                        # 기본 인적사항 저장 및 이동
                        st.session_state["step"] = 2
                        st.rerun()

# 메인 화면
def render_control_panel(col_left):
    profile = st.session_state["user_profile"]
    
    with col_left:
        # 추가할 디테일들, 열거형
        st.markdown("### Travel Details")
        with st.expander("Trip Preferences & Constraints", expanded=st.session_state["expander_open"]):
            # 스타일, 선택형
            style = st.multiselect(
                "Style & Purpose",
                ["History & Culture", "Food & Cafe", "Shopping", "Nature & Relaxation", "filming location"],
                default=["History & Culture"]
            )

            # 동행인, 선택+숫자형
            comp_col1, comp_col2 = st.columns([2, 1])
            with comp_col1:
                companion = st.selectbox(
                    "Companions", 
                    ["Solo", "Friends", "Couple", "Family w. parents", "Family w. kids"],
                    key="companion_select"
                )
            # 숫자 부분, 솔로시 1명 고정, 최대 20
            with comp_col2:
                default_group_size = 1 if companion == "Solo" else 2
                group_size = st.number_input(
                    "Group Size", min_value=1, max_value=20, 
                    value=default_group_size, disabled=(companion == "Solo")
                )

            # 이동 수단 선택형, 중복금지
            with st.container(border=True):
                transport = st.radio(
                    "Transport Option",
                    ["Love Sightseeing by walking", "The less walk, the better", "Moving must be ASAP"],
                    index=0
                )
            
            # 여행 기간, 시간 단위 입력 > 최종 시간 계산, 최적화 해야됨
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
                st.error("Error: End Date cannot be earlier than Start Date!")
            else:
                start_dt = datetime.datetime.combine(start_date, start_time)
                end_dt = datetime.datetime.combine(end_date, end_time)
                duration = (end_date - start_date).days + 1
                total_hours = round((end_dt - start_dt).total_seconds() / 3600, 1)
                st.caption(f"Total Duration: **{duration} Day(s)** ({total_hours} hrs)")
            
            # 부가적 요소 추가
            extra_notes = st.text_area("Specific Requests", placeholder="e.g. Hurt my leg, so minimize walking. Prefer indoor spots if rainy.")
            
            generate_routes_btn = st.button("Generate Top 5 Route Options", type="primary", use_container_width=True)

            # 파이프 가동, 가동 시 익스펜더 닫음 (예외 처리 대비)
            if generate_routes_btn:
                with st.spinner("AI evaluating weather, mobility, and preferences..."):
                    schedule_info = f"Arrival: {start_date} {start_time.strftime('%H:%M')}, Departure: {end_date} {end_time.strftime('%H:%M')}"
                    combined_interests = f"Style: {', '.join(style)}, Companion: {companion} ({group_size} people), Transport: {transport}, Schedule: {schedule_info}, Notes: {extra_notes}"
                    
                    result = pipe(
                        nationality=profile["nationality"],
                        age=f"{profile['age']}",
                        interests=combined_interests,
                        duration_days=duration
                    )
                    st.session_state["expander_open"] = False
                    st.session_state["itinerary_routes"] = result
                    st.rerun()

# 실시간 채팅, 거의 미구현
def render_chat_assistant(col_left):
    with col_left:
        st.markdown("### Real-Time AI Assistant")
        with st.container(border=True):
            st.caption("Ask questions or adjust your itinerary dynamically.")

            st.write("**Quick Adjustments:**")
            chip1, chip2, chip3 = st.columns(3)
            with chip1:
                if st.button("📌 Reduce Walking", use_container_width=True):
                    st.session_state["pending_chat_prompt"] = "Please adjust the itinerary to minimize walking distance."
            with chip2:
                if st.button("☕ Add Cafe Stop", use_container_width=True):
                    st.session_state["pending_chat_prompt"] = "Can you add a famous local cafe stop between destinations?"
            with chip3:
                if st.button("☔ Switch Indoor", use_container_width=True):
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
                st.session_state["chat_history"].append({"role": "user", "content": user_input})
                ai_reply = f"Got it! Adjusting your route based on: '{user_input}'."
                st.session_state["chat_history"].append({"role": "assistant", "content": ai_reply})
                st.rerun()

# 실시간 지도 표시, folium
def render_map_and_routes(col_right):
    routes = st.session_state["itinerary_routes"]
    
    with col_right:
        st.markdown("### Interactive Route Map")
        with st.container(border=True):
            if not routes:
                st.info("Fill out the preferences on the left and click **'Generate Top 5 Route Options'**!")
                # 임시 기본 스팟 지정용
                default_spots = [
                    {"name": "Gyeongbokgung Palace", "lat": 37.5796, "lng": 126.9770},
                    {"name": "N Seoul Tower", "lat": 37.5512, "lng": 126.9882},
                    {"name": "Bukchon Hanok Village", "lat": 37.5826, "lng": 126.9831},
                    {"name": "Myeongdong", "lat": 37.5636, "lng": 126.9834}
                ]
                # 스팟 내용을 folium에 전달 (위, 경도, 확대정도)
                m = folium.Map(location=[37.5665, 126.9780], zoom_start=12)
                for spot in default_spots:
                    folium.Marker([spot["lat"], spot["lng"]], popup=spot["name"], tooltip=spot["name"], icon=folium.Icon(color="blue", icon="star")).add_to(m)
                st_folium(m, width="100%", height=380)
            else:
                map_locations = []
                for day_info in routes.get("itinerary", []):
                    for place in day_info.get("places", []):
                        if place.get("lat") and place.get("lng"):
                            map_locations.append({"name": place.get("place_name"), "lat": place.get("lat"), "lng": place.get("lng")})

                if map_locations:
                    m = folium.Map(location=[map_locations[0]["lat"], map_locations[0]["lng"]], zoom_start=13)
                    coords = [[loc["lat"], loc["lng"]] for loc in map_locations]
                    
                    for idx, loc in enumerate(map_locations, 1):
                        folium.Marker(
                            [loc["lat"], loc["lng"]], 
                            popup=f"{idx}. {loc['name']}", 
                            tooltip=f"{idx}. {loc['name']}", 
                            icon=folium.Icon(color="red", icon="info-sign")
                        ).add_to(m)
                        
                    if len(coords) > 1:
                        folium.PolyLine(coords, color="#0066CC", weight=4, opacity=0.8).add_to(m)
                    st_folium(m, width="100%", height=380)

        # 결과 루트 창
        st.markdown("### Recommended Route Options")
        tabs = st.tabs(["Best Match", "Minimal Walk", "Cultural", "Foodie", "Scenic"])
        
        for idx, tab in enumerate(tabs):
            with tab:
                if routes:
                    for day_info in routes.get("itinerary", []):
                        st.markdown(f"#### Day {day_info.get('day')}")
                        for p_idx, place in enumerate(day_info.get("places", []), 1):
                            with st.container(border=True):
                                st.write(f"**{p_idx}. {place.get('place_name')}** ({place.get('estimated_time')})")
                                st.caption(f"{place.get('address')}")
                                st.markdown(f"*{place.get('reason')}*")
                else:
                    st.caption("No route generated yet.")

# 메인 실행 함수
def main():
    init_app()
    
    if st.session_state["step"] == 1:
        render_onboarding()
        
    elif st.session_state["step"] == 2:
        profile = st.session_state["user_profile"]
        
        st.title(f"{profile['nickname']} needs the best {profile['destination']} plan!")
        st.caption(f"Profile: {profile['nationality']}, {profile['age']} / Destination: {profile['destination']}")
        st.divider()

        col_left, col_right = st.columns([1, 0.8], gap="medium")
        
        render_control_panel(col_left)
        render_chat_assistant(col_left)
        render_map_and_routes(col_right)

if __name__ == "__main__":
    main()