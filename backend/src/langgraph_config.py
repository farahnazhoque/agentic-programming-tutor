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

# Initialize the graph
graph = StateGraph(AgentState)

# Step 1: Process Explanation (Summarize, Generate Boilerplate, Get Correct Output)
def process_explanation(state: dict) -> dict:
    # Add input validation
    if not state.get("explanation") or state["explanation"].strip() == "":
        raise ValueError("Explanation cannot be empty")
    
    prompt = PromptTemplate.from_template(
        template="""
        Given this explanation about {language} programming, please provide:

        1. A clear bullet-point summary
        2.A step-by-step, beginner-friendly boilerplate code example in {language} with inline comments explaining each step, similar to Codecademy's learning style. If the explanation cannot be directly translated into code, create a related coding problem that helps reinforce the concept and provide a structured solution.
        3. The expected output of the code

        Format your response exactly like this:
        SUMMARY:
        • Point 1
        • Point 2

        CODE:
        // Step 1: Explain the first part of the code
        // Step 2: Introduce the next concept
        // Step 3: Implement the logic with clarity
        <boilerplate code here>


        OUTPUT:
        <expected output>

        Explanation: {explanation}
        """
    )

    response = llm.invoke(prompt.format(explanation=state["explanation"], language=state["language"]))
    response_text = response.content if hasattr(response, "content") else str(response)
    
    # Split by sections
    sections = response_text.split("\n\n")
    
    try:
        summary = sections[0].replace("SUMMARY:", "").strip()
        code = sections[1].replace("CODE:", "").strip()
        output = sections[2].replace("OUTPUT:", "").strip()
        
        state["summary"] = summary
        state["boilerplate_code"] = code
        state["correct_output"] = output
        
        # Debug logging
        print("Processed State:", {
            "summary": state["summary"],
            "code": state["boilerplate_code"],
            "output": state["correct_output"]
        })
        
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
    
    state["user_code"] = corrected_code.strip()
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
