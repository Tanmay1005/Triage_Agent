import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL = "gemini-2.0-flash"
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
