import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    chat = client.chats.create(
        model='gemini-3.6-flash',
    )
    response = chat.send_message("서울 관광지 3개 추천해줘")
    print(response.text)

except Exception as e:
    print("❌ Gemini API Connection Failed:")
    print(e)