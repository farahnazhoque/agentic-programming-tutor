from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from functools import lru_cache
import os
from dotenv import load_dotenv
from utils import get_llm

# Load environment variables
load_dotenv()

# Initialize LLM
llm = get_llm()

# Define the agent's state (we add a new key "ai_chat_response" for the chat feedback)
class AgentState(TypedDict):
    explanation: str
    max_attempts: int
    user_attempts: int
    language: str
    user_code: str
    correct_output: str
    hints_given: List[str]
    boilerplate_code: str
    is_correct: bool
    level: str
    ai_chat_response: str  # New field for AI chat feedback

# Initialize the graph
graph = StateGraph(AgentState)

# Step 1: Process Explanation (Summarize, Generate Boilerplate, Get Correct Output)
def process_explanation(state: dict) -> dict:
    if not state.get("explanation") or state["explanation"].strip() == "":
        raise ValueError("Explanation cannot be empty")
    
    prompt = f"""
    You are an AI that provides structured programming explanations.
    Create a step by step curriculum for learning {state["explanation"]} at {state["level"]} level.
    Return ONLY valid JSON without any markdown code blocks or additional text.
    The JSON should follow this structure:
    {{
      "title": "Course title",
      "description": "Course description",
      "steps": [
        {{
          "id": "unique-id",
          "type": "explanation/exercise/challenge",
          "content": "Step content in HTML format",
          "code": "Initial code (if applicable)",
          "hints": ["hint1", "hint2"],
          "expectedOutput": "Expected output (if applicable)"
        }}
      ]
    }}
    """
    
    try:
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)
        
        # Debug print the raw response
        print("Raw response:", response_text)
        
        # Remove markdown code block markers if present
        text = response_text.replace("```json", "").replace("```", "")
        
        import json
        parsed_json = json.loads(text)
        state.update(parsed_json)
        return state
        
    except Exception as e:
        print("Error parsing LLM response:", response_text)
        raise ValueError(f"Failed to parse LLM response: {str(e)}")

graph.add_node("process_explanation", process_explanation)

# Step 2: Check User Output & Provide Hints
@lru_cache(maxsize=50)
def get_hints(user_code: str, exercise: str) -> str:
    prompt = f"""
    You are a helpful programming tutor. Given this code:
    {user_code}
    
    And this exercise/task:
    {exercise}

    Provide a short, helpful hint that:
    1. Identifies what might be wrong or missing
    2. Guides the student in the right direction
    3. Does NOT give away the complete solution
    4. Uses encouraging, supportive language
    5. Is specific to their code

    Keep the hint under 2-3 sentences.
    """
    try:
        result = llm.invoke(prompt)
        response = result.content if hasattr(result, "content") else str(result)
        text = response.replace("```json", "").replace("```", "")
            
        # Validate JSON before returning
        try:
            import json
            parsed_json = json.loads(text)
            return parsed_json
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response from the AI")
    except Exception as e:
        raise ValueError(f"Failed to generate hints: {str(e)}")

graph.add_node("get_hints", get_hints)

def check_and_hint_user_output(state: dict) -> dict:
    state["user_attempts"] += 1
    
    # Get hints using the user's current code and expected output
    response = get_hints(state["user_code"], state["correct_output"])
    response_text = response.content if hasattr(response, "content") else str(response)

    if "Correct" in response_text:
        state["is_correct"] = True
    else:
        state["is_correct"] = False
        state["hints_given"].append(response_text.replace("Incorrect", "").strip())  

    return state

graph.add_node("check_and_hint", check_and_hint_user_output)

# Step 3: Generate Corrected Code If Max Attempts Reached
def generate_corrected_code(state: dict) -> dict:
    prompt = PromptTemplate.from_template(
        template="""
        Based on the user's incorrect code and the hints provided, generate the corrected code.
        
        Hints: {hints_given}
        User's Incorrect Code: {user_code}
        """
    )
    corrected_code = llm.invoke(prompt.format(user_code=state["user_code"], hints_given=state["hints_given"]))
    corrected_code_text = corrected_code.content if hasattr(corrected_code, "content") else str(corrected_code)
    
    state["user_code"] = corrected_code_text.strip()
    return state

graph.add_node("generate_corrected_code", generate_corrected_code)

# Step 4: Verify Corrected Code
def verify_corrected_code(state: dict) -> dict:
    response = get_hints(state["user_code"], state["correct_output"])
    if "Correct" in response:
        state["is_correct"] = True
    else:
        state["is_correct"] = False
    return state

graph.add_node("verify_corrected_code", verify_corrected_code)

# New Function: AI Chat to Provide Guidance Based on Current Code
def ai_chat(state: dict) -> dict:
    prompt = f"""
    You are a coding assistant. Please review the user's current code in the editor and provide guidance or suggestions on what to do next.
    Do not wait for a code submission; simply provide helpful feedback based on the current code.
    
    Current code:
    {state["user_code"]}
    """
    response = llm.invoke(prompt)
    chat_feedback = response.content if hasattr(response, "content") else str(response)
    state["ai_chat_response"] = chat_feedback.strip()
    return state

graph.add_node("ai_chat", ai_chat)

# You can choose to integrate the ai_chat node into your main flow.
# For example, you might run it right after the explanation is processed:
graph.add_edge(START, "process_explanation")
graph.add_edge("process_explanation", "ai_chat")
graph.add_edge("ai_chat", "check_and_hint")

# Branching based on the outcome of check_and_hint
def branch_fn(state: dict):
    if state["is_correct"]:
        return "end"
    elif state["user_attempts"] < state["max_attempts"]:
        return "check_and_hint"
    else:
        return "generate_corrected_code"

graph.add_conditional_edges(
    "check_and_hint",
    branch_fn,
    {
        "end": END,
        "check_and_hint": "check_and_hint",
        "generate_corrected_code": "generate_corrected_code"
    }
)

# After correction, verify and end
graph.add_edge("generate_corrected_code", "verify_corrected_code")
graph.add_edge("verify_corrected_code", END)

# Compile the Graph
compiled_graph = graph.compile()
