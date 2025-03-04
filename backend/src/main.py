from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END  # ✅ No 'State' import
from typing import TypedDict
import os
from dotenv import load_dotenv
from functools import lru_cache
from langgraph_config import AgentState, graph
from utils import get_llm  # Updated import
# loading environment variables for security
load_dotenv()

# initializing the Flask app; the purpose of this app is to provide a simple API for the frontend to interact with
app = Flask(__name__)

# adding CORS support; the purpose of this is to allow the frontend to interact with the backend
CORS(app)

# defining the endpoint for the frontend to start the agent
@app.route("/start_agent/", methods=["POST"])
def start_agent():
    # getting the request data
    user_input = request.get_json()
    
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
    return jsonify(result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5015, debug=True)