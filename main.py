import os
import json
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Gemini API Configuration ---
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file.")
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    # You might want to exit or handle this more gracefully
    # For now, we'll let it raise an error if the API is called.

# --- FastAPI App Initialization ---
app = FastAPI(
    title="AI Learning Scheduler API",
    description="Backend for the AI Learning Scheduler application.",
)

# --- CORS (Cross-Origin Resource Sharing) Middleware ---
# This allows your frontend (running on a different origin) to communicate with this backend.
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    # Add other origins if needed, e.g., your local network IP for mobile testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For simplicity, allowing all origins. For production, restrict this to your domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for Data Validation ---
class ScheduleRequest(BaseModel):
    topic: str
    total_duration: str
    daily_commitment: str

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    """
    Serves the main index.html file as the application's homepage.
    """
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found. Make sure the file is in the same directory.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while reading the HTML file: {e}")


def create_prompt(request: ScheduleRequest) -> str:
    """
    Creates a detailed, structured prompt for the Gemini API to generate a learning schedule.
    """
    return f"""
You are an expert learning planner. Your task is to create a detailed, day-by-day study schedule based on the user's request.

The user wants to learn: "{request.topic}"
They want to complete it in: "{request.total_duration}"
They will study for: "{request.daily_commitment}" per day.

Break down the main topic into logical, sequential sub-topics. For each day, provide 3-5 specific, actionable to-do list items and one practical, hands-on exercise.

Your output MUST be a valid JSON array of objects. Do not include any text, explanations, or markdown formatting (like ```json) before or after the JSON array.

The JSON structure for each object in the array must be:
{{
  "day": <integer>,
  "topic_of_the_day": "<string>",
  "tasks": ["<string>", "<string>", ...],
  "exercise": "<string>"
}}
"""

@app.post("/generate-schedule")
async def generate_schedule(request: ScheduleRequest):
    """
    Receives user learning goals and generates a structured JSON schedule using the Gemini API.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = create_prompt(request)
        
        response = model.generate_content(prompt)
        
        # Clean up potential markdown formatting from the response text
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        # Parse the cleaned string into a Python list/dictionary
        schedule_data = json.loads(cleaned_text)
        
        return schedule_data
        
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from the Gemini API response.")
        print("Raw response:", response.text)
        raise HTTPException(status_code=500, detail="The AI response was not in a valid JSON format. Please try again.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # This will catch other potential errors, such as from the API call itself.
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")

