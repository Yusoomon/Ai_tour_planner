# ✈️ KOMPASS (AI Tour Planner)
> **AI personalized tour Itinerary builder for the best-optimized routes

<p align="center">
    <img src="static/images/KOMPASS_LOGO.png" alt="LOGO" width="180"/>
</p>

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)


## Overview
**KOMPASS** was built by the tired developer who loves to tour but not to plan. It must be the best option if you are an eagle person to seek for the personalized best-fit route!


## Key Features
- **User Data Collection**: 
- **Prototype Suggestion before Finalization**: 
- **Straight forward UI**: 
- **API Integration**:


## Tech Stack

| **Type** | Stacks |</br>
| **Frontend / Web Framework** | Python, Streamlit, CSS |</br>
| **AI / API** | Google Gemini API, Korea Data Portal API |</br>
| **Data & Image** | Folium |</br>
| **Deployment** | Streamlit Community Cloud |</br>


## Directory Structure

```text
Ai_tour_planner/
├── .streamlit/
│   └── config.toml          # Streamlit background setting
├── assets/
│   └── style.css            # Main style
│   └── images/              # Images (Background)
│       └── .jpg/png
├── pages/                   # Initial/Pages
│   └── _init_.py
│   └── 2_Profile.py
│   └── 3_Itinerary.py
├── static/
│   └── images/
│       └── logo.png         # Logo
├── app.py                   # Main Launcher
├── common.py                # Common template (header, footer, etc)
├── README.md                # Overview
└── requirements.txt         # Required packages
