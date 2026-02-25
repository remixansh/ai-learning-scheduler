import os
import json
import re
from dotenv import load_dotenv

import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Tuple, AsyncGenerator
import httpx

# --- Application Setup ---

# Load environment variables from a .env file
load_dotenv()

# Configure the Gemini API
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"Error configuring Gemini API: {e}. The API will fail if called.")

# Initialize FastAPI app
app = FastAPI(
    title="AI Learning Scheduler API",
    description="Backend for the AI Learning Scheduler application.",
)

# Add CORS middleware to allow all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScheduleRequest(BaseModel):
    """Defines the expected request body for generating a schedule."""
    topic: str
    total_duration: str
    daily_commitment: str


def parse_duration_to_days(duration_str: str) -> int:
    """
    Parses a human-readable string (e.g., "30 days", "2 months")
    into an approximate number of days.
    """
    duration_str = duration_str.lower().strip()
    # Basic regex to find a number and a unit
    match = re.match(r"(\d+)\s*(\w+)", duration_str)
    
    if not match:
        # If no unit, try to parse as a raw number of days
        try:
            return int(duration_str)
        except ValueError:
            return 30  # Fallback to 30 days if unparseable

    num = int(match.group(1))
    unit = match.group(2)

    if "day" in unit:
        return num
    if "week" in unit:
        return num * 7
    if "month" in unit:
        return num * 30  
    if "year" in unit:
        return num * 365 
    
    return num  

def get_schedule_granularity(total_days: int) -> Tuple[str, str, str]:
    """
    Determines the prompt instructions and JSON structure based on the total days.
    
    Returns:
        A tuple: (period_instruction, json_day_field_type, json_example_value)
    """
    
    if total_days > 365:
        period_instruction = "Your schedule should be monthly (e.g., 'Month 1', 'Month 2')."
        json_day_field = '"day": "<string>"'
        json_example = '"day": "Month 1"'
        
    elif 180 < total_days <= 365:
        period_instruction = "Your schedule should be in 10-day blocks (e.g., '1-10', '11-20')."
        json_day_field = '"day": "<string>"'
        json_example = '"day": "1-10"'
        
    elif 60 < total_days <= 180:
        period_instruction = "Your schedule should be in 5-day blocks (e.g., '1-5', '6-10')."
        json_day_field = '"day": "<string>"'
        json_example = '"day": "1-5"'
        
    elif 30 < total_days <= 60:
        period_instruction = "Your schedule should be in 2-day blocks (e.g., '1-2', '3-4')."
        json_day_field = '"day": "<string>"'
        json_example = '"day": "1-2"'
        
    else: # <= 30 days
        period_instruction = "Your schedule should be daily (Day 1, Day 2...)."
        json_day_field = '"day": <integer>'
        json_example = '"day": 1'
    
    return period_instruction, json_day_field, json_example

def create_streaming_prompt(request: ScheduleRequest) -> str:
    """
    Creates the dynamic prompt for the Gemini model based on user input
    and calculated schedule granularity.
    """
    total_days = parse_duration_to_days(request.total_duration)
    
    period_instruction, json_day_field, json_example = get_schedule_granularity(
        total_days
    )

    return f"""
You are an expert learning planner. Your task is to generate a study schedule.

User request:
Topic: "{request.topic}"
Total Duration: "{request.total_duration}"
Daily Commitment: "{request.daily_commitment}"

**Important Instructions:**
1.  {period_instruction}
2.  Your output MUST be a series of valid JSON objects, one for each period, SEPARATED BY A NEWLINE.
3.  DO NOT wrap the output in a JSON array (no [ ] brackets at the start or end).
4.  DO NOT include any text, explanations, or markdown formatting before or after the JSON objects.

The JSON structure for EACH LINE must be:
{{{json_day_field}, "topic_of_the_day": "<string>", "tasks": ["<string>", ...], "exercise": "<string>"}}

Example of a single line of output:
{{{json_example}, "topic_of_the_day": "Example Topic for the Period", "tasks": ["Task 1", "Task 2"], "exercise": "Example exercise for the period"}}
"""

async def stream_json_objects(request: ScheduleRequest) -> AsyncGenerator[str, None]:
    """
    Calls the Gemini API with streaming enabled and yields one complete
    JSON object string (a single line) at a time.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = create_streaming_prompt(request)
        
        # Start the streaming generation
        response = model.generate_content(prompt, stream=True)
        
        buffer = ""
        for chunk in response:
            if chunk.text:
                buffer += chunk.text
                
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        yield line + '\n'
        
        if buffer.strip():
            yield buffer + '\n'
            
    except Exception as e:
        print(f"Error during streaming: {e}")
        error_payload = json.dumps({"error": f"An error occurred: {str(e)}"})
        yield error_payload + '\n'

# --- API Endpoints ---

@app.get("/get-videos")
async def get_videos(topic: str):
    """
    Fetches top 5 relevant videos from YouTube Data API based on the topic.
    """
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")
    if not youtube_api_key:
        raise HTTPException(status_code=500, detail="YOUTUBE_API_KEY not configured.")

    search_query = f"{topic} tutorial"
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "maxResults": 5,
        "q": search_query,
        "type": "video",
        "key": youtube_api_key
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            videos = []
            for item in data.get("items", []):
                snippet = item["snippet"]
                videos.append({
                    "title": snippet["title"],
                    "thumbnail": snippet["thumbnails"]["medium"]["url"],
                    "videoId": item["id"]["videoId"],
                    "channelTitle": snippet["channelTitle"]
                })
            return videos[:5]
        except httpx.HTTPStatusError as e:
            print(f"YouTube API Error: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch videos from YouTube.")
        except Exception as e:
            print(f"Unexpected Error: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    """
    Serves the main index.html file as the application's homepage.
    """
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.post("/generate-schedule")
async def generate_schedule_stream(request: ScheduleRequest):
    """
    Receives user learning goals and STREAMS a schedule as JSON Lines.
    The client will receive one JSON object per line.
    """
    return StreamingResponse(
        stream_json_objects(request), 
        # Use 'application/x-ndjson' (newline-delimited json)
        # This standard media type is perfect for streaming JSON objects.
        media_type="application/x-ndjson" 
    )