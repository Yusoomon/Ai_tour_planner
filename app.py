import streamlit as st
import folium
import datetime
import urllib.parse
from streamlit_folium import st_folium
from api_pipeline.pipe import pipe
from folium import plugins


# ============================================================
# 8단계 유저 플로우 (Layout A "맵 퍼스트" 팔레트 유지)
# 1 랜딩 → 2 메인화면 → 3 인적사항 입력 → 4 키워드·취향 입력
# → 5 초기 루트 추천 → 6 최종 루트 확정(지도) → 7 챗봇 상담(풀스크린)
#   → 8 예약·지도연동·리뷰(장소 상세)
# 7, 8은 6에서 갈라져 나가는 하위 화면이고, 다시 6으로 돌아온다.
# ============================================================
MAP_ROUTE_COLORS = ["#2F6E52", "#C9A227", "#3D6BFF", "#B34A3D", "#7A5FA8"]


def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.css');

        :root {
            --bg: #F3EEE3;
            --panel: rgba(255, 255, 255, 0.85);
            --border: #E1D9C6;
            --accent: #2F6E52;
            --accent-hover: #255A43;
            --accent-tint: #E4EEE9;
            --text: #1E2B24;
            --text-muted: #6F7C74;
        }

        html, body, [class*="css"] {
            font-family: 'Pretendard Variable', 'Pretendard', -apple-system, sans-serif;
        }

        .stApp, [data-testid="stAppViewContainer"] {
            background-color: var(--bg);
            color: var(--text);
        }
        [data-testid="stHeader"] { background-color: transparent; }
        [data-testid="stAppViewContainer"] .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }

        /* ================= 지도 풀블리드 배경 (STEP 6, 7) ================= */
        .st-key-map_layer {
            position: fixed !important;
            inset: 0;
            z-index: 0;
        }
        .st-key-map_layer iframe {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
        }

        /* ================= 지도 위 플로팅 글래스 패널 (STEP 6) ================= */
        .st-key-floating_panel, .st-key-route_panel {
            position: fixed !important;
            top: 66px;
            width: 380px;
            max-height: calc(100vh - 150px);
            overflow-y: auto;
            background: var(--panel);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 22px;
            box-shadow: 0 20px 50px rgba(30, 40, 35, 0.18);
            padding: 22px !important;
            z-index: 10;
        }
        .st-key-floating_panel { left: 28px; }
        .st-key-route_panel { right: 28px; }

        .st-key-day_bar {
            position: fixed !important;
            bottom: 26px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10;
            width: auto !important;
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(10px);
            border-radius: 999px;
            padding: 8px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        }
        .st-key-day_bar div[data-testid="stHorizontalBlock"] { gap: 6px; }

        .st-key-toast_banner {
            position: fixed !important;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 15;
            background: rgba(30, 40, 35, 0.92);
            border-radius: 999px;
            padding: 8px 20px;
            width: auto !important;
        }
        .st-key-toast_banner p {
            color: #FFFFFF !important;
            font-size: 12.5px;
            font-weight: 700;
            margin: 0 !important;
            text-align: center;
        }

        /* ================= 챗봇 풀스크린 모달 (STEP 7) ================= */
        .st-key-dim_overlay {
            position: fixed !important;
            inset: 0;
            background: rgba(243, 238, 227, 0.55);
            z-index: 5;
        }
        .st-key-chat_modal {
            position: fixed !important;
            top: 56px;
            left: 50%;
            transform: translateX(-50%);
            width: 640px;
            max-height: calc(100vh - 100px);
            overflow-y: auto;
            background: var(--panel);
            backdrop-filter: blur(16px);
            border-radius: 22px;
            box-shadow: 0 20px 50px rgba(30, 40, 35, 0.22);
            padding: 26px !important;
            z-index: 20;
        }

        /* ================= 그라데이션 배경 (STEP 1,2,3,4,5,8) ================= */
        .st-key-grad_bg {
            min-height: 100vh;
            background:
                radial-gradient(circle at 20% 25%, #EFE9DD 0%, transparent 45%),
                radial-gradient(circle at 78% 70%, #E4EEE9 0%, transparent 50%),
                var(--bg);
            padding: 56px 24px 70px;
        }

        .brand-logo { font-size: 15px; font-weight: 800; color: var(--text); margin-bottom: 30px; }
        .landing-title { text-align: center; font-size: 38px; font-weight: 800; color: var(--text); line-height: 1.3; margin-bottom: 12px; }
        .landing-dek { text-align: center; font-size: 15px; color: var(--text-muted); margin-bottom: 30px; }
        .feat-card {
            text-align: center; background: #FFFFFF; border: 1px solid var(--border); border-radius: 16px;
            padding: 16px 10px; font-size: 12.5px; font-weight: 700; color: var(--text);
            box-shadow: 0 6px 16px rgba(30,40,35,0.06);
        }
        .home-title { text-align: center; font-size: 28px; font-weight: 800; color: var(--text); margin-bottom: 6px; }
        .preview-step { text-align: center; background: #FFFFFF; border: 1px solid var(--border); border-radius: 14px; padding: 14px 6px; }
        .preview-num {
            width: 22px; height: 22px; border-radius: 50%; background: var(--accent-tint); color: var(--accent);
            font-size: 11px; font-weight: 800; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px;
        }
        .preview-step p { font-size: 11.5px; font-weight: 700; color: var(--text); }

        .step-caption { text-align: center; font-size: 11.5px; font-weight: 700; color: var(--accent); letter-spacing: 0.08em; margin-bottom: 8px; }
        .step-bar { display: flex; gap: 6px; justify-content: center; margin-bottom: 26px; }
        .step-dot { width: 40px; height: 5px; border-radius: 999px; background: var(--border); }
        .step-dot.done, .step-dot.active { background: var(--accent); }

        .review-title { text-align: center; font-size: 24px; font-weight: 800; color: var(--text); margin-bottom: 4px; }
        .review-sub { text-align: center; font-size: 13.5px; color: var(--text-muted); margin-bottom: 24px; }

        .detail-hero {
            background: linear-gradient(135deg, var(--accent), #6FAE8E);
            color: white; font-size: 22px; font-weight: 800;
            padding: 50px 22px 18px; border-radius: 14px; margin-bottom: 14px;
        }

        .chip-row-ro { display: flex; gap: 6px; flex-wrap: wrap; margin: 6px 0 14px; }
        .ro-chip { background: var(--accent-tint); color: var(--accent); font-size: 11.5px; font-weight: 700; padding: 5px 11px; border-radius: 999px; }

        /* ================= 글래스 카드형 폼 (STEP 3,4,5,8) ================= */
        .st-key-form_card div[data-testid="stVerticalBlockBorderWrapper"],
        .st-key-route_card div[data-testid="stVerticalBlockBorderWrapper"],
        .st-key-detail_card div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--panel) !important;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 22px !important;
            box-shadow: 0 20px 50px rgba(30, 40, 35, 0.16);
            border: 1px solid var(--border) !important;
            padding: 12px 8px;
        }

        /* ================= 공통 컴포넌트 톤 ================= */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px !important;
            border: 1px solid var(--border) !important;
            background-color: #FFFFFF;
        }
        div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button, div[data-testid="stLinkButton"] a {
            border-radius: 999px !important;
            font-weight: 700;
            transition: all 0.15s ease-in-out;
        }
        div[data-testid="stButton"] button[kind="primary"],
        div[data-testid="stFormSubmitButton"] button[kind="primary"],
        div[data-testid="stLinkButton"] a[kind="primary"] {
            background-color: var(--accent);
            border: none;
        }
        div[data-testid="stButton"] button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
            background-color: var(--accent-hover);
        }
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stTimeInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
            border-radius: 10px !important;
            border-color: var(--border) !important;
        }
        span[data-baseweb="tag"] {
            background-color: var(--accent-tint) !important;
            color: var(--accent) !important;
            border-radius: 999px !important;
        }
        input[type="radio"] { accent-color: var(--accent); }
        div[data-testid="stTabs"] button[data-baseweb="tab"] { border-radius: 999px; padding: 4px 16px; }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            background-color: var(--accent-tint);
            color: var(--accent);
        }
        div[data-testid="stChatMessage"] { border-radius: 14px; padding: 4px 6px; }
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
            background-color: var(--text) !important;
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) p {
            color: #FFFFFF !important;
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
            background-color: #EEF2EF;
        }
        div[data-testid="stAlert"] { border-radius: 14px; }
        div[data-testid="stExpander"] summary { border-radius: 12px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_app():
    st.set_page_config(page_title="AI Travel Planner", page_icon="✈️", layout="wide")
    inject_custom_css()

    defaults = {
        "step": 1,
        "user_profile": {},
        "preferences": {},
        "itinerary_routes": None,
        "route_confirmed": False,
        "selected_day": None,
        "detail_place": None,
        "chat_history": [],
        "pending_chat_prompt": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_step_bar(active_step, total=4):
    dots = ""
    for i in range(1, total + 1):
        cls = "active" if i == active_step else ("done" if i < active_step else "")
        dots += f'<div class="step-dot {cls}"></div>'
    st.markdown(f'<div class="step-bar">{dots}</div>', unsafe_allow_html=True)


# ============================================================
# STEP 1 — 랜딩 페이지
# ============================================================
def render_landing():
    with st.container(key="grad_bg"):
        st.markdown('<div class="brand-logo">🌿 Easy Plan</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="landing-title">Easy plan, Cozy vacay ✈️<br>서울 여행, AI 가이드와 함께</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="landing-dek">언어 걱정 없이, 나만의 서울 코스를 AI가 짜드려요</div>',
            unsafe_allow_html=True,
        )

        _, c1, c2, c3, _ = st.columns([1.2, 1, 1, 1, 1.2])
        with c1:
            st.markdown('<div class="feat-card">🧭 AI 맞춤 루트</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="feat-card">🚦 실시간 교통·날씨 반영</div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="feat-card">💬 24/7 여행 챗봇</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

        _, mid, _ = st.columns([2, 1.2, 2])
        with mid:
            if st.button("여행 계획 시작하기 →", type="primary", width="stretch", key="landing_cta"):
                st.session_state["step"] = 2
                st.rerun()


# ============================================================
# STEP 2 — 메인화면
# ============================================================
def render_main_home():
    with st.container(key="grad_bg"):
        st.markdown('<div class="brand-logo">🌿 Easy Plan</div>', unsafe_allow_html=True)
        st.markdown('<div class="home-title">환영해요, 여행자님 👋</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="landing-dek">몇 가지만 알려주시면 서울 맞춤 코스를 만들어드릴게요</div>',
            unsafe_allow_html=True,
        )

        _, mid, _ = st.columns([2, 1.2, 2])
        with mid:
            if st.button("새 여행 계획하기 →", type="primary", width="stretch", key="home_cta"):
                st.session_state["step"] = 3
                st.rerun()

        st.markdown("<div style='height:36px;'></div>", unsafe_allow_html=True)

        _, p1, p2, p3, p4, _ = st.columns([1.2, 1, 1, 1, 1, 1.2])
        labels = ["정보 입력", "취향 선택", "루트 추천", "최종 확정"]
        for i, (col, label) in enumerate(zip([p1, p2, p3, p4], labels), start=1):
            with col:
                st.markdown(
                    f'<div class="preview-step"><div class="preview-num">{i}</div><p>{label}</p></div>',
                    unsafe_allow_html=True,
                )


# ============================================================
# STEP 3 — 인적사항 입력
# ============================================================
def render_personal_info():
    with st.container(key="grad_bg"):
        st.markdown('<div class="step-caption">STEP 1 / 4</div>', unsafe_allow_html=True)
        render_step_bar(1)

        _, mid, _ = st.columns([1, 2.2, 1])
        with mid:
            with st.container(key="form_card", border=True):
                st.markdown("### 여행자 정보를 알려주세요")
                st.caption("국적과 방문 목적에 맞춰 추천이 더 정확해져요")

                with st.form("personal_info_form", border=False):
                    c1, c2 = st.columns(2)
                    with c1:
                        nickname = st.text_input("Nickname", placeholder="Yusoomon")
                    with c2:
                        age = st.number_input("Age", min_value=1, max_value=100, value=28)

                    c3, c4 = st.columns(2)
                    with c3:
                        nationality = st.text_input("Nationality", placeholder="American")
                    with c4:
                        visit_purpose = st.selectbox(
                            "Visit Purpose",
                            ["Tourism", "Business", "Study", "Family Visit", "Other"],
                        )

                    destination = st.text_input(
                        "Destination", placeholder="Seoul, Korea", value="Seoul, Korea"
                    )

                    submitted = st.form_submit_button(
                        "다음 →", type="primary", width="stretch"
                    )

                    if submitted:
                        if not nickname or not nationality:
                            st.error("Even the alien can't make the plans with this info..")
                        else:
                            st.session_state["user_profile"] = {
                                "nickname": nickname,
                                "age": age,
                                "nationality": nationality,
                                "visit_purpose": visit_purpose,
                                "destination": destination,
                            }
                            st.session_state["step"] = 4
                            st.rerun()

                if st.button("← 이전", key="back_to_landing"):
                    st.session_state["step"] = 2
                    st.rerun()


# ============================================================
# STEP 4 — 키워드·취향 입력
# ============================================================
def render_preferences():
    with st.container(key="grad_bg"):
        st.markdown('<div class="step-caption">STEP 2 / 4</div>', unsafe_allow_html=True)
        render_step_bar(2)

        _, mid, _ = st.columns([1, 2.2, 1])
        with mid:
            with st.container(key="form_card", border=True):
                st.markdown("### 어떤 여행을 원하세요?")
                st.caption("관심사와 이동 조건을 알려주시면 코스에 반영할게요")

                with st.form("preferences_form", border=False):
                    style = st.multiselect(
                        "Style & Interests",
                        [
                            "History & Culture",
                            "Food & Cafe",
                            "Shopping",
                            "Nature & Relaxation",
                            "filming location",
                        ],
                        default=["History & Culture"],
                    )

                    c1, c2 = st.columns(2)
                    with c1:
                        companion = st.selectbox(
                            "Companions",
                            ["Solo", "Friends", "Couple", "Family w. parents", "Family w. kids"],
                        )
                    with c2:
                        default_group_size = 1 if companion == "Solo" else 2
                        group_size = st.number_input(
                            "Group Size",
                            min_value=1,
                            max_value=20,
                            value=default_group_size,
                            disabled=(companion == "Solo"),
                        )

                    transport = st.radio(
                        "Transport Option",
                        [
                            "Love sightseeing by walking",
                            "Less walking, but not skip sightseeing",
                            "Moving must be ASAP",
                        ],
                        index=0,
                    )

                    d1, d2 = st.columns(2)
                    with d1:
                        start_date = st.date_input("Start Date")
                        start_time = st.time_input("Start Time", value=datetime.time(9, 0))
                    with d2:
                        end_date = st.date_input("End Date")
                        end_time = st.time_input("End Time", value=datetime.time(21, 0))

                    notes = st.text_area(
                        "Specific Requests",
                        placeholder="e.g. Hurt my leg, so minimize walking. Prefer indoor spots if rainy.",
                    )

                    submitted = st.form_submit_button(
                        "루트 추천받기 →", type="primary", width="stretch"
                    )

                    if submitted:
                        if end_date < start_date:
                            st.error(
                                "Error: End Date cannot be earlier than Start Date! or You must be a time traveler"
                            )
                        else:
                            st.session_state["preferences"] = {
                                "style": style,
                                "companion": companion,
                                "group_size": group_size,
                                "transport": transport,
                                "start_date": start_date,
                                "start_time": start_time,
                                "end_date": end_date,
                                "end_time": end_time,
                                "notes": notes,
                            }
                            st.session_state["itinerary_routes"] = None
                            st.session_state["route_confirmed"] = False
                            st.session_state["selected_day"] = None
                            st.session_state["step"] = 5
                            st.rerun()

                if st.button("← 이전", key="back_to_personal"):
                    st.session_state["step"] = 3
                    st.rerun()


# ============================================================
# STEP 5 — 초기 루트 추천
# ============================================================
def render_route_review():
    with st.container(key="grad_bg"):
        st.markdown('<div class="step-caption">STEP 3 / 4</div>', unsafe_allow_html=True)
        render_step_bar(3)

        if st.session_state["itinerary_routes"] is None:
            with st.spinner("AI가 서울 코스를 짜고 있어요..."):
                profile = st.session_state["user_profile"]
                prefs = st.session_state["preferences"]
                schedule_info = (
                    f"Arrival: {prefs['start_date']} {prefs['start_time'].strftime('%H:%M')}, "
                    f"Departure: {prefs['end_date']} {prefs['end_time'].strftime('%H:%M')}"
                )
                combined_interests = (
                    f"{', '.join(prefs['style'])}; Companion: {prefs['companion']} "
                    f"({prefs['group_size']} people), Transport: {prefs['transport']}, "
                    f"Schedule: {schedule_info}, Notes: {prefs['notes']}, "
                    f"Visit Purpose: {profile.get('visit_purpose', '')}"
                )
                result = pipe(
                    nationality=profile["nationality"],
                    age=f"{profile['age']}",
                    interests=combined_interests,
                    duration_total=schedule_info,
                    destination=profile["destination"],
                )
                st.session_state["itinerary_routes"] = result

        routes = st.session_state["itinerary_routes"]

        _, mid, _ = st.columns([1, 2.4, 1])
        with mid:
            st.markdown('<div class="review-title">AI가 찾은 맞춤 루트예요</div>', unsafe_allow_html=True)

            if not routes:
                st.markdown(
                    '<div class="review-sub">루트를 만들지 못했어요. 조건을 조정하고 다시 시도해주세요.</div>',
                    unsafe_allow_html=True,
                )
            else:
                itinerary = routes.get("itinerary", [])
                day_count = len(itinerary)
                place_count = sum(len(d.get("places", [])) for d in itinerary)
                st.markdown(
                    f'<div class="review-sub">{day_count}일 · {place_count}곳 추천 '
                    f'· 조건에 맞춰 AI가 실시간으로 생성했어요</div>',
                    unsafe_allow_html=True,
                )

                with st.container(key="route_card", border=True):
                    st.markdown(f"#### {routes.get('trip_title', 'AI 추천 루트')}")
                    for day_info in itinerary:
                        names = ", ".join(
                            p.get("place_name", "") for p in day_info.get("places", [])
                        )
                        st.caption(f"Day {day_info.get('day')}: {names}")

                st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("다시 추천받기", width="stretch", key="regen_route"):
                        st.session_state["itinerary_routes"] = None
                        st.rerun()
                with c2:
                    if st.button(
                        "이 루트로 진행하기 →", type="primary", width="stretch", key="confirm_route"
                    ):
                        st.session_state["step"] = 6
                        st.rerun()

            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            if st.button("← 이전", key="back_to_prefs"):
                st.session_state["itinerary_routes"] = None
                st.session_state["step"] = 4
                st.rerun()


# ============================================================
# STEP 6 — 최종 루트 확정 (지도 풀블리드 + 플로팅 패널)
# ============================================================
def render_map_layer():
    """화면 전체를 채우는 지도 레이어 (배경)."""
    routes = st.session_state["itinerary_routes"]
    selected_day = st.session_state.get("selected_day")

    if not routes:
        default_spots = [
            {"name": "Gyeongbokgung", "lat": 37.5796, "lng": 126.9770},
            {"name": "Namsan Tower", "lat": 37.5512, "lng": 126.9882},
            {"name": "Insadong", "lat": 37.5826, "lng": 126.9831},
            {"name": "Myeongdong", "lat": 37.5636, "lng": 126.9834},
        ]
        m = folium.Map(location=[37.5665, 126.9780], zoom_start=13, tiles="CartoDB positron")
        for spot in default_spots:
            folium.Marker(
                [spot["lat"], spot["lng"]],
                popup=spot["name"],
                tooltip=spot["name"],
                icon=folium.Icon(color="darkgreen", icon="star"),
            ).add_to(m)
        st_folium(m, width=1600, height=900, key="map_default")
        return

    map_locations = []
    count = []
    for day_info in routes.get("itinerary", []):
        temp = 0
        for place in day_info.get("places", []):
            if place.get("lat") and place.get("lng"):
                map_locations.append(
                    {
                        "name": place.get("place_name"),
                        "lat": place.get("lat"),
                        "lng": place.get("lng"),
                        "day": day_info.get("day"),
                    }
                )
                temp += 1
        count.append(temp)

    if not map_locations:
        st.info("표시할 위치 정보가 없어요.")
        return

    if selected_day is not None:
        day_locs = [loc for loc in map_locations if loc.get("day") == selected_day]
        center_loc = day_locs[0] if day_locs else map_locations[0]
        zoom = 14
    else:
        center_loc = map_locations[0]
        zoom = 13

    m = folium.Map(location=[center_loc["lat"], center_loc["lng"]], zoom_start=zoom, tiles="CartoDB positron")

    current_day_idx = 0
    remaining_count = count[current_day_idx] if count else 0
    current_color = MAP_ROUTE_COLORS[current_day_idx % len(MAP_ROUTE_COLORS)]
    current_day_number = routes["itinerary"][current_day_idx].get("day") if routes.get("itinerary") else None

    day_polylines = []
    current_day_coords = []

    for idx, loc in enumerate(map_locations, 1):
        coord = [loc["lat"], loc["lng"]]

        if remaining_count == 0 and current_day_idx < len(count) - 1:
            if current_day_coords:
                day_polylines.append(
                    {"coords": current_day_coords, "color": current_color, "day": current_day_number}
                )
            current_day_coords = []
            current_day_idx += 1
            remaining_count = count[current_day_idx]
            current_color = MAP_ROUTE_COLORS[current_day_idx % len(MAP_ROUTE_COLORS)]
            current_day_number = routes["itinerary"][current_day_idx].get("day")

        current_day_coords.append(coord)
        remaining_count -= 1

        if selected_day is not None and loc.get("day") != selected_day:
            continue

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

    if current_day_coords:
        day_polylines.append(
            {"coords": current_day_coords, "color": current_color, "day": current_day_number}
        )

    for poly in day_polylines:
        if selected_day is not None and poly["day"] != selected_day:
            continue
        if len(poly["coords"]) > 1:
            folium.PolyLine(poly["coords"], color=poly["color"], weight=4, opacity=0.8).add_to(m)

    st_folium(m, width=1600, height=900, key="map_routes")


def render_floating_panel(container):
    """좌측 글래스 패널: 프로필 요약 + 확정/재설정 + 실시간 챗봇 미니뷰."""
    profile = st.session_state["user_profile"]
    prefs = st.session_state.get("preferences", {})

    with container:
        st.markdown(f"#### {profile.get('nickname', '')}의 서울 여행 ✈️")
        st.caption(
            f"{profile.get('nationality', '')} · {profile.get('age', '')} · {profile.get('destination', '')}"
        )

        if prefs.get("style"):
            chip_html = "".join(f'<span class="ro-chip">{s}</span>' for s in prefs["style"])
            st.markdown(f'<div class="chip-row-ro">{chip_html}</div>', unsafe_allow_html=True)

        if st.session_state.get("route_confirmed"):
            st.success("일정이 확정됐어요!")
        else:
            if st.button("일정 확정하기", type="primary", width="stretch", key="confirm_itinerary"):
                st.session_state["route_confirmed"] = True
                st.rerun()

        if st.button("설정 다시 열기", width="stretch", key="reopen_prefs"):
            st.session_state["itinerary_routes"] = None
            st.session_state["route_confirmed"] = False
            st.session_state["step"] = 4
            st.rerun()

        st.divider()
        st.markdown("**Real-Time AI Assistant**")
        st.caption("Ask questions or adjust your itinerary dynamically.")

        chip1, chip2, chip3 = st.columns(3)
        with chip1:
            if st.button("📌 Reduce Walking", width="stretch", key="chip_walk"):
                st.session_state["pending_chat_prompt"] = (
                    "Please adjust the itinerary to minimize walking distance."
                )
        with chip2:
            if st.button("☕ Add Cafe Stop", width="stretch", key="chip_cafe"):
                st.session_state["pending_chat_prompt"] = (
                    "Can you add a famous local cafe stop between destinations?"
                )
        with chip3:
            if st.button("☔ Switch Indoor", width="stretch", key="chip_rain"):
                st.session_state["pending_chat_prompt"] = (
                    "In case of rain, please replace outdoor spots with indoor activities."
                )

        chat_box = st.container(height=200)
        with chat_box:
            for message in st.session_state["chat_history"][-6:]:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
            user_input = st.chat_input("Type your request here...", key="mini_chat_input")

        if not user_input and st.session_state["pending_chat_prompt"]:
            user_input = st.session_state["pending_chat_prompt"]
            st.session_state["pending_chat_prompt"] = ""

        if user_input:
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            ai_reply = f"Got it! Adjusting your route based on: '{user_input}'."
            st.session_state["chat_history"].append({"role": "assistant", "content": ai_reply})
            st.rerun()

        if st.button("💬 전체화면으로 물어보기", width="stretch", key="open_chat_fullscreen"):
            st.session_state["step"] = 7
            st.rerun()


def render_route_panel(container):
    """우측 글래스 패널: 루트 옵션 탭 + 장소 카드 목록 (상세보기 진입점)."""
    routes = st.session_state["itinerary_routes"]

    with container:
        st.markdown("#### Recommended Route Options")

        if not routes:
            st.info(
                "왼쪽 패널에서 조건을 확인하고 다시 루트를 만들어보세요!"
            )
            return

        tabs = st.tabs(["Best Match", "Minimal Walk", "Cultural", "Foodie", "Scenic"])
        selected_day = st.session_state.get("selected_day")

        for tab_idx, tab in enumerate(tabs):
            with tab:
                for day_info in routes.get("itinerary", []):
                    if selected_day is not None and day_info.get("day") != selected_day:
                        continue

                    st.markdown(f"##### Day {day_info.get('day')}")
                    for p_idx, place in enumerate(day_info.get("places", []), 1):
                        with st.container(border=True):
                            img_col, info_col = st.columns([1, 3])

                            with img_col:
                                img_url = place.get("image")
                                if isinstance(img_url, str) and img_url.startswith(
                                    ("http://", "https://")
                                ):
                                    try:
                                        st.image(img_url, width="stretch")
                                    except Exception:
                                        st.markdown("🚫")
                                else:
                                    st.markdown("🚫")

                            with info_col:
                                st.markdown(f"**{p_idx}. {place.get('place_name')}**")
                                contact_num = place.get("contact", "0")
                                contact_text = (
                                    contact_num
                                    if contact_num and contact_num != "0"
                                    else "Contact unavailable"
                                )
                                st.caption(f"⏱ {place.get('estimated_time')} · 📞 {contact_text}")

                            st.caption(f"{place.get('address')} · {place.get('reason')}")

                            if st.button(
                                "자세히 보기",
                                width="stretch",
                                key=f"detail_{tab_idx}_{day_info.get('day')}_{p_idx}",
                            ):
                                st.session_state["detail_place"] = place
                                st.session_state["step"] = 8
                                st.rerun()


def render_day_bar(container):
    """하단 플로팅 바: Day별로 지도/목록을 필터링."""
    routes = st.session_state["itinerary_routes"]
    if not routes:
        return

    days = [d.get("day") for d in routes.get("itinerary", [])]
    with container:
        cols = st.columns(len(days) + 1)
        with cols[0]:
            if st.button(
                "전체",
                type=("primary" if st.session_state.get("selected_day") is None else "secondary"),
                key="day_all",
            ):
                st.session_state["selected_day"] = None
                st.rerun()
        for i, d in enumerate(days):
            with cols[i + 1]:
                is_active = st.session_state.get("selected_day") == d
                if st.button(
                    f"Day {d}",
                    type=("primary" if is_active else "secondary"),
                    key=f"day_{d}",
                ):
                    st.session_state["selected_day"] = d
                    st.rerun()


def render_map_dashboard():
    map_layer = st.container(key="map_layer")
    with map_layer:
        render_map_layer()

    if st.session_state.get("itinerary_routes"):
        toast = st.container(key="toast_banner")
        with toast:
            st.markdown("🚦 실시간 교통·날씨가 반영된 최종 루트예요")

    floating_panel = st.container(key="floating_panel")
    render_floating_panel(floating_panel)

    route_panel = st.container(key="route_panel")
    render_route_panel(route_panel)

    day_bar = st.container(key="day_bar")
    render_day_bar(day_bar)


# ============================================================
# STEP 7 — 챗봇 상담 (여행중, 풀스크린 모달)
# ============================================================
def render_chat_fullscreen():
    map_layer = st.container(key="map_layer")
    with map_layer:
        render_map_layer()

    st.container(key="dim_overlay")

    modal = st.container(key="chat_modal")
    with modal:
        if st.button("지도로 돌아가기 ✕", key="close_chat_modal"):
            st.session_state["step"] = 6
            st.rerun()

        st.markdown("#### 여행 중 궁금한 점을 물어보세요")
        st.caption("지금 위치와 일정을 참고해서 답해드려요")

        quick_qs = ["🚻 근처 화장실 어디예요?", "☔ 우천시 대안 코스", "⏱ 다음 장소까지 얼마나?"]
        qc1, qc2, qc3 = st.columns(3)
        for col, q in zip([qc1, qc2, qc3], quick_qs):
            with col:
                if st.button(q, width="stretch", key=f"quick_{q}"):
                    st.session_state["pending_chat_prompt"] = q

        chat_box = st.container(height=380)
        with chat_box:
            for message in st.session_state["chat_history"]:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
            user_input = st.chat_input("메시지를 입력하세요...", key="fullscreen_chat_input")

        if not user_input and st.session_state["pending_chat_prompt"]:
            user_input = st.session_state["pending_chat_prompt"]
            st.session_state["pending_chat_prompt"] = ""

        if user_input:
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            ai_reply = f"Got it! Adjusting your route based on: '{user_input}'."
            st.session_state["chat_history"].append({"role": "assistant", "content": ai_reply})
            st.rerun()


# ============================================================
# STEP 8 — 예약, 지도 연동 및 리뷰 (장소 상세)
# ============================================================
def render_place_detail():
    place = st.session_state.get("detail_place")

    with st.container(key="grad_bg"):
        _, mid, _ = st.columns([1, 2.6, 1])
        with mid:
            if not place:
                st.info("선택된 장소가 없어요. 목록에서 장소를 먼저 골라주세요.")
            else:
                with st.container(key="detail_card", border=True):
                    st.markdown(
                        f'<div class="detail-hero">{place.get("place_name", "")}</div>',
                        unsafe_allow_html=True,
                    )

                    contact = place.get("contact", "0")
                    contact_text = contact if contact and contact != "0" else "Contact unavailable"
                    st.caption(f"{place.get('address', '주소 정보 없음')} · 📞 {contact_text}")

                    st.markdown("**소개**")
                    st.write(place.get("overview") or "아직 소개 정보가 없어요.")

                    st.markdown("**지도**")
                    if place.get("lat") and place.get("lng"):
                        detail_map = folium.Map(
                            location=[place["lat"], place["lng"]],
                            zoom_start=16,
                            tiles="CartoDB positron",
                        )
                        folium.Marker(
                            [place["lat"], place["lng"]],
                            icon=folium.Icon(color="darkgreen"),
                        ).add_to(detail_map)
                        st_folium(detail_map, width=620, height=200, key="detail_map")
                    else:
                        st.caption("위치 정보가 없어요.")

                    naver_url = (
                        "https://map.naver.com/v5/search/"
                        + urllib.parse.quote(place.get("place_name", ""))
                    )
                    st.link_button("지도에서 길찾기", naver_url, type="primary")
                    st.caption("예약 연동은 추후 지원 예정이에요.")

            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            if st.button("← 목록으로 돌아가기", key="back_to_dashboard"):
                st.session_state["step"] = 6
                st.rerun()


def main():
    init_app()
    step = st.session_state["step"]

    if step == 1:
        render_landing()
    elif step == 2:
        render_main_home()
    elif step == 3:
        render_personal_info()
    elif step == 4:
        render_preferences()
    elif step == 5:
        render_route_review()
    elif step == 6:
        render_map_dashboard()
    elif step == 7:
        render_chat_fullscreen()
    elif step == 8:
        render_place_detail()


if __name__ == "__main__":
    main()