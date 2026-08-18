import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import List
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

load_dotenv()

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
TOUR_API_KEY = os.getenv("TOUR_API_KEY")


class Activity(BaseModel):
    time: str = Field(description="활동 시간 (예: 10:00)")
    location: str = Field(description="장소 이름")
    description: str = Field(description="할 일 및 팁")
    cost: int = Field(description="예상 비용 (KRW)")


class DailyItinerary(BaseModel):
    day: int = Field(description="일차 (1, 2, 3...)")
    date: str = Field(description="날짜 (YYYY-MM-DD)")
    activities: List[Activity]


class TravelPlan(BaseModel):
    destination: str
    total_days: int
    itinerary: List[DailyItinerary]


def fetch_tourapi_overview(content_id):
    """콘텐츠 ID로 TourAPI 상세 설명을 조회합니다."""
    if not content_id:
        return ""

    url = "https://apis.data.go.kr/B551011/EngService2/detailCommon2"
    params = {
        "serviceKey": TOUR_API_KEY,
        "contentId": content_id,
        "MobileOS": "ETC",
        "MobileApp": "AiTourPlanner",
        "_type": "json",
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        item = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(item, list):
            item = item[0] if item else {}
        return item.get("overview", "") if isinstance(item, dict) else ""
    except Exception as e:
        print(f"TourAPI overview fetch failed for '{content_id}': {e}")
        return ""


def fetch_tourapi_contact(content_id, content_type_id):
    """장소 유형별 상세 소개 정보에서 연락처를 조회합니다."""
    if not content_id or not content_type_id:
        return ""

    url = "https://apis.data.go.kr/B551011/EngService2/detailIntro2"
    params = {
        "serviceKey": TOUR_API_KEY,
        "contentId": content_id,
        "contentTypeId": content_type_id,
        "MobileOS": "ETC",
        "MobileApp": "AiTourPlanner",
        "_type": "json",
    }
    contact_fields = (
        "infocenter",
        "infocenterculture",
        "infocenterleports",
        "infocenterlodging",
        "infocenterfood",
        "infocentershopping",
    )

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        item = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(item, list):
            item = item[0] if item else {}
        if isinstance(item, dict):
            for field in contact_fields:
                if item.get(field):
                    return item[field]
    except Exception as e:
        print(f"TourAPI contact fetch failed for '{content_id}': {e}")

    return ""


@lru_cache(maxsize=256)
def fetch_tourapi_place_info(keyword):
    """
    위도, 경도, 주소,
    """
    url = "https://apis.data.go.kr/B551011/EngService2/searchKeyword2"
    params = {
        "serviceKey": TOUR_API_KEY,
        "numOfRows": "1",
        "pageNo": "1",
        "MobileOS": "ETC",
        "MobileApp": "AiTourPlanner",
        "_type": "json",
        "keyword": keyword,
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if not isinstance(data, dict):
            print(f"Unexpected response format for '{keyword}': {data}")
            return {
                "address": "Information unavailable",
                "lat": None,
                "lng": None,
                "image": "",
                "content_id": "",
                "contact": "0",
                "overview": "",
            }
        items = (
            data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        )

        if items:
            item = items[0] if isinstance(items, list) else items
            content_id = item.get("contentid", "")
            content_type_id = item.get("contenttypeid", "")
            contact = item.get("tel", "") or fetch_tourapi_contact(
                content_id, content_type_id
            )
            return {
                "address": item.get("addr1", "Address unavailable"),
                "lat": float(item.get("mapy")) if item.get("mapy") else None,
                "lng": float(item.get("mapx")) if item.get("mapx") else None,
                "image": item.get("firstimage2") or item.get("firstimage", ""),
                "content_id": content_id,
                "contact": contact or "0",
                "overview": fetch_tourapi_overview(content_id),
            }
    except Exception as e:
        print(f"TourAPI fetch failed for '{keyword}': {e}")

    return {
        "address": "Information unavailable",
        "lat": None,
        "lng": None,
        "image": "",
        "content_id": "",
        "contact": "0",
        "overview": "Failed to fetch overview.",
    }


def pipe(nationality, age, interests, duration_total, destination):
    """
    AI랑 투어DB 결합
    """
    print(f"유저 정보: 국적={nationality}, 나이={age}, 관심사={interests}, 여행기간={duration_total}, 목적지={destination}")
    prompt = f"""
    You are a travel guide for foreign tourists visiting {destination}.
    Generate a travel itinerary between {duration_total} based on the user profile.
    
    [User Profile]
    - Nationality: {nationality}
    - Age Group: {age}
    - Interests/Preferences: {interests}
    - Schedule: {duration_total}
    
    Return a structured response matching the provided TravelPlan schema.
    Use the destination exactly as the requested destination and provide costs in KRW.
    """
    try:
        chat = gemini_client.chats.create(model="gemini-3.7-flash")
        response = chat.send_message(
            prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": TravelPlan,
            },
        )

        travel_plan = TravelPlan.model_validate_json(response.text)
        itinerary_data = {
            "destination": travel_plan.destination,
            "total_days": travel_plan.total_days,
            "itinerary": [],
        }

        for daily_plan in travel_plan.itinerary:
            places = []
            for activity in daily_plan.activities:
                places.append(
                    {
                        "place_name": activity.location,
                        "search_keyword": activity.location,
                        "reason": activity.description,
                        "estimated_time": activity.time,
                        "estimated_real_time": activity.time,
                        "cost": activity.cost,
                    }
                )
            itinerary_data["itinerary"].append(
                {"day": daily_plan.day, "date": daily_plan.date, "places": places}
            )

        print("데이터 결합하는중...")
        place_entries = []
        for day in itinerary_data.get("itinerary", []):
            for place in day.get("places", []):
                keyword = place.get("search_keyword") or place.get("place_name")
                place_entries.append((place, keyword))

        if place_entries:
            keywords = [keyword for _, keyword in place_entries]
            with ThreadPoolExecutor(max_workers=min(8, len(keywords))) as executor:
                geo_infos = executor.map(fetch_tourapi_place_info, keywords)
                for (place, _), geo_info in zip(place_entries, geo_infos):
                    place["address"] = geo_info["address"]
                    place["lat"] = geo_info["lat"]
                    place["lng"] = geo_info["lng"]
                    place["image"] = geo_info["image"]
                    place["content_id"] = geo_info["content_id"]
                    place["contact"] = geo_info["contact"]
                    place["overview"] = geo_info["overview"]

        print("결합이 성공적으로 완료되었습니다!")
        return itinerary_data

    except Exception as e:
        print("Pipeline failed:", e)
        return None


if __name__ == "__main__":
    final_result = pipe(
        nationality="Korean",
        age="24",
        interests="History, Shopping",
        duration_total=3,
        destination="Seoul",
    )

    print("\n--- 결과 출력 ---")
    print(json.dumps(final_result, indent=2, ensure_ascii=False))
