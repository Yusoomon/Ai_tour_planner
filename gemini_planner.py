import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_tour_itinerary(nationality, age, interests, duration_days):
    """
    유저의 인적사항과 취향을 받아 Gemini로부터 규격화된 여행 일정(JSON)을 생성합니다.
    """
    prompt = f"""
    You are a travel guide for foreign tourists visiting Seoul, Korea.
    Generate a {duration_days}-day travel itinerary based on user profile.
    
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
                        "search_keyword": "Keyword for TourAPI search (e.g. Gyeongbokgung)",
                        "reason": "Brief reason for recommendation based on user interests",
                        "estimated_time": "e.g. 2 hours"
                    }}
                ]
            }}
        ]
    }}
    """

    try:
        chat = client.chats.create(model='gemini-3.6-flash')
        response = chat.send_message(prompt)
        
        # JSON 파싱
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        itinerary_data = json.loads(cleaned_text)
        return itinerary_data

    except Exception as e:
        print("❌ Error generating itinerary:", e)
        return None

# 테스트 실행
if __name__ == "__main__":
    # 라이언(Ryan) 미국인 대학생 시나리오 테스트
    result = generate_tour_itinerary(
        nationality="American", 
        age="20s", 
        interests="History, Palace, Walking minimalized", 
        duration_days=1
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))