import os
import json
import requests
from dotenv import load_dotenv
from google import genai

load_dotenv()

# 1. Gemini Client 및 TourAPI 설정
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
TOUR_API_KEY = os.getenv("TOUR_API_KEY")

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
        "keyword": keyword
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        
        if items:
            item = items[0] if isinstance(items, list) else items
            return {
                "address": item.get("addr1", "Address unavailable"),
                "lat": float(item.get("mapy")) if item.get("mapy") else None,
                "lng": float(item.get("mapx")) if item.get("mapx") else None,
                "image": item.get("firstimage", ""),
                "content_id": item.get("contentid", "")
            }
    except Exception as e:
        print(f"⚠️ TourAPI fetch failed for '{keyword}': {e}")

    # 검색 결과가 없을 경우 기본값 리턴
    return {"address": "Information unavailable", "lat": None, "lng": None, "image": "", "content_id": ""}


def pipe(nationality, age, interests, duration_days):
    """
    AI랑 투어DB 결합
    """
    print(f"AI를 통해 국적({nationality})과 나이({age})에 기반해 추천받는중...")
    
    prompt = f"""
    You are a travel guide for foreign tourists visiting Seoul, Korea.
    Generate a {duration_days}-day travel itinerary based on the user profile.
    
    [User Profile]
    - Nationality: {nationality}
    - Age Group: {age}
    - Interests/Preferences: {interests}
    
    [Output Requirement]
    Return ONLY a valid JSON object without markdown code blocks (do not use ```json).
    The JSON structure must strictly follow this format:
    {{
        "trip_title": "Title of the trip",
        "itinerary": [
            {{
                "day": 1,
                "places": [
                    {{
                        "place_name": "Official English name of the place",
                        "search_keyword": "Simple search keyword for TourAPI (e.g., Gyeongbokgung, Insadong)",
                        "reason": "Brief reason for recommendation based on user interests",
                        "estimated_time": "e.g., 2 hours"
                    }}
                ]
            }}
        ]
    }}
    """

    try:
        # 제미나이 실행
        chat = gemini_client.chats.create(model='gemini-3.6-flash')
        response = chat.send_message(prompt)
        
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        itinerary_data = json.loads(cleaned_text)

       # 데이터DB와 결합
        print("데이터 결합하는중...")
        for day in itinerary_data.get("itinerary", []):
            for place in day.get("places", []):
                keyword = place.get("search_keyword", place.get("place_name"))
                geo_info = fetch_tourapi_place_info(keyword)
                
                # TourAPI 정보 병합
                place["address"] = geo_info["address"]
                place["lat"] = geo_info["lat"]
                place["lng"] = geo_info["lng"]
                place["image"] = geo_info["image"]

        print("결합이 성공적으로 완료되었습니다!")
        return itinerary_data

    except Exception as e:
        print("❌ Pipeline failed:", e)
        return None


# 테스트
if __name__ == "__main__":
    # 미국인 대학생 Ryan (역사 관심, 최소한의 도보)
    final_result = pipe(
        nationality="American",
        age="24",
        interests="History, Royal Palaces, minimalized walking",
        duration_days=1
    )
    
    print("\n--- 결과 출력 ---")
    print(json.dumps(final_result, indent=2, ensure_ascii=False))