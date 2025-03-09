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

# Define the agent's state (use dictionary keys instead of object attributes)
class AgentState(TypedDict):
    explanation: str
    max_attempts: int
    user_attempts: int
    language: str
    user_code: str
    correct_output: str
    hints_given: List[str]
    summary: str
    boilerplate_code: str
    is_correct: bool
    level: str
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
@lru_cache(maxsize=50)  # ✅ Cache repeated incorrect user code
def get_hints(user_code: str, correct_output: str) -> str:
    prompt = f"""
    Analyze the user's code against the expected correct output.
    
    - If the code is correct, return: "Correct"
    - If incorrect, return: "Incorrect" followed by bullet-point hints.
    
    User Code: {user_code}
    Correct Output: {correct_output}
    """
    return llm.invoke(prompt)

def check_and_hint_user_output(state: dict) -> dict:
    state["user_attempts"] += 1
    
    # ✅ Ensure we extract text properly from AIMessage
    response = get_hints(state["user_code"], state["correct_output"])
    response_text = response.content if hasattr(response, "content") else str(response)

    if "Correct" in response_text:
        state["is_correct"] = True
    else:
        state["is_correct"] = False
        # ✅ Now response_text is a string, so we can safely use .replace()
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
    # Extract content from AIMessage
    corrected_code_text = corrected_code.content if hasattr(corrected_code, "content") else str(corrected_code)
    
    state["user_code"] = corrected_code_text.strip()
    return state

graph.add_node("generate_corrected_code", generate_corrected_code)

# Step 4: Verify Corrected Code
def verify_corrected_code(state: dict) -> dict:
    response = get_hints(state["user_code"], state["correct_output"])  # Reuse checking logic
    
    if "Correct" in response:
        state["is_correct"] = True
    else:
        state["is_correct"] = False  # This shouldn't happen often since LLM is correcting it.
    
    return state

graph.add_node("verify_corrected_code", verify_corrected_code)

# Step 5: Graph Flow with Correct Conditions
graph.add_edge(START, "process_explanation")
graph.add_edge("process_explanation", "check_and_hint")

# ✅ Fixed function for condition-based branching
def branch_fn(state: dict):
    if state["is_correct"]:
        return "end"
    elif state["user_attempts"] < state["max_attempts"]:
        return "retry"
    else:
        return "max_attempts"

graph.add_conditional_edges(
    "check_and_hint",
    branch_fn,
    {
        "end": END,
        "retry": "check_and_hint",
        "max_attempts": "generate_corrected_code"
    }
)

# After correction, verify and end
graph.add_edge("generate_corrected_code", "verify_corrected_code")
graph.add_edge("verify_corrected_code", END)

# ✅ Compile the Graph
compiled_graph = graph.compile()
