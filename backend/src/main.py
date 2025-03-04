from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage
from langchain_graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Annotated, Sequence
import os
from dotenv import load_dotenv

# loading environment variables for security
load_dotenv()

# initializing the FastAPI app; the purpose of this app is to provide a simple API for the frontend to interact with
app = FastAPI()

# adding CORS middleware); the purpose of this is to allow the frontend to interact with the backend
app.add_middleware(
    CORSMiddleware, # the middleware to add
    allow_origins=["*"], # allow all origins
    allow_credentials=True, # allow credentials
    allow_methods=["*"], # allow all methods
    allow_headers=["*"], # allow all headers
)

def get_llm():
    # initializing the Google Generative AI model
    llm = ChatGoogleGenerativeAI(
        model_name="gemini-1.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    return llm


# defining the endpoint for the frontend to start the agent
@app.post("/start_agent/")
async def start_agent(user_input: dict):
    # getting the user's explanation as the prompt for the agent
    explanation = user_input.get("explanation", "")
    
    # getting the max attempts from the user
    max_attempts = user_input.get("max_attempts", 3)
    # getting the language from the user
    language = user_input.get("language", "Python")
    # initializing the agent
    state = AgentState(
        explanation=explanation,
        max_attempts=max_attempts,
        language=language,
    )

    # running the agent and storing the output in result
    result = graph.invoke(state)

    # returning the result to the frontend
    return result