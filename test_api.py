"""
Quick test: is Gemini API working?
Run: python test_api.py
This does NOT touch the database. It just asks Gemini to say hello.
If this hangs too, the problem is the API key / internet / model, not our SQL code.
Never print the full key - only its first 4 characters.
"""
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
if not key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    print("Check: file name is exactly .env, not .env.txt")
    raise SystemExit(1)

print("Key found: Yes")
print("Key starts with:", key[:4])
print("Key length:", len(key))
print("Calling Gemini, please wait 10-30 seconds...")

from google import genai

client = genai.Client(api_key=key)
response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents="Say hello in one word.",
)
print("Gemini replied:")
print(response.text)
print("Done - API is working.")
