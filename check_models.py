import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure with your key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("--- Checking Available Models ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Found: {m.name}")
except Exception as e:
    print(f"Error: {e}")