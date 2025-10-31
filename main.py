import os
import json
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
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
    # We'll let it raise an error if the API is called.

# --- FastAPI App Initialization ---
app = FastAPI(
    title="AI Learning Scheduler API",
    description="Backend for the AI Learning Scheduler application.",
)

# --- CORS (Cross-Origin Resource Sharing) Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For simplicity
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
        raise HTTPException(status_code=404, detail="index.html not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


def create_streaming_prompt(request: ScheduleRequest) -> str:
    """
    Creates a prompt that asks for JSON Lines (one JSON object per line).
    """
    return f"""
You are an expert learning planner. Your task is to generate a study schedule.

User request:
Topic: "{request.topic}"
Total Duration: "{request.total_duration}"
Daily Commitment: "{request.daily_commitment}"

Your output MUST be a series of valid JSON objects, one for each day, SEPARATED BY A NEWLINE.
DO NOT wrap the output in a JSON array (no [ ] brackets at the start or end).
DO NOT include any text, explanations, or markdown formatting before or after the JSON objects.

The JSON structure for EACH LINE must be:
{{"day": <integer>, "topic_of_the_day": "<string>", "tasks": ["<string>", ...], "exercise": "<string>"}}
"""

async def stream_json_objects(request: ScheduleRequest):
    """
    Calls Gemini with stream=True and yields one complete JSON object string (line) at a time.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = create_streaming_prompt(request)
        
        response = model.generate_content(prompt, stream=True)
        
        buffer = ""
        for chunk in response:
            if chunk.text:
                buffer += chunk.text
                
                # Check if we have one or more complete lines (JSON objects)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        yield line + '\n' # Send the complete JSON line
        
        # Send any remaining data in the buffer
        if buffer.strip():
            yield buffer + '\n'
            
    except Exception as e:
        print(f"Error during streaming: {e}")
        # Send a JSON error object as the last line
        yield json.dumps({"error": str(e)}) + '\n'

# REPLACED Endpoint: Now streams JSON Lines
@app.post("/generate-schedule")
async def generate_schedule_stream(request: ScheduleRequest):
    """
    Receives user learning goals and STREAMS a schedule as JSON Lines.
    """
    return StreamingResponse(
        stream_json_objects(request), 
        media_type="application/x-ndjson" # ndjson = newline-delimited json
    )