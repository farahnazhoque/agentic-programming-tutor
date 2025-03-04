from typing import TypedDict, Annotated, Sequence
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from utils import get_llm
import os  
from dotenv import load_dotenv
from functools import lru_cache

# Load environment variables
load_dotenv()

llm = get_llm()

# Define the agent's state
from typing import TypedDict

class AgentState(TypedDict):
    explanation: str
    max_attempts: int
    user_attempts: int
    language: str
    user_code: str
    correct_output: str
    hints_given: list[str]
    summary: str
    boilerplate_code: str
    is_correct: bool

graph = StateGraph(AgentState)

# Step 1: Process Explanation (Summarize, Generate Boilerplate, Get Correct Output)
def process_explanation(state: AgentState) -> AgentState:
    prompt = PromptTemplate.from_template(
        template="""
        Based on the following explanation, perform the following tasks:
        1. Summarize the explanation in simple terms using bullet points.
        2. Generate a boilerplate code with comments in {language}.
        3. Generate the expected correct output for the given boilerplate code.
        
        Return the summary, boilerplate code, and correct output in three separate lines.
        
        Explanation: {explanation}
        """
    )
    response = llm.invoke(prompt.format(explanation=state.explanation, language=state.language))
    summary, boilerplate_code, correct_output = response.split("\n")
    
    state.summary = summary.strip()
    state.boilerplate_code = boilerplate_code.strip()
    state.correct_output = correct_output.strip()
    return state

graph.add_node("process_explanation", process_explanation)

# Step 2: Check User Output & Provide Hints
@lru_cache(maxsize=50)  # ✅ Caches repeated incorrect user code
def get_hints(user_code: str, correct_output: str) -> str:
    prompt = f"""
    Analyze the user's code against the expected correct output.
    
    - If the code is correct, return: "Correct"
    - If incorrect, return: "Incorrect" followed by bullet-point hints.
    
    User Code: {user_code}
    Correct Output: {correct_output}
    """
    return llm.invoke(prompt)

def check_and_hint_user_output(state: AgentState) -> AgentState:
    state.user_attempts += 1
    
    response = get_hints(state.user_code, state.correct_output)  # Cached call

    if "Correct" in response:
        state.is_correct = True
    else:
        state.is_correct = False
        state.hints_given.append(response.replace("Incorrect", "").strip())  # Store hints
    
    return state

graph.add_node("check_and_hint", check_and_hint_user_output)

# Step 3: Generate Corrected Code If Max Attempts Reached
def generate_corrected_code(state: AgentState) -> AgentState:
    prompt = PromptTemplate.from_template(
        template="""
        Based on the user's incorrect code and the hints provided, generate the corrected code.
        
        Hints: {hints_given}
        User's Incorrect Code: {user_code}
        """
    )
    corrected_code = llm.invoke(prompt.format(user_code=state.user_code, hints_given=state.hints_given))
    
    state.user_code = corrected_code.strip()
    return state

graph.add_node("generate_corrected_code", generate_corrected_code)

# Step 4: Verify Corrected Code
def verify_corrected_code(state: AgentState) -> AgentState:
    response = get_hints(state.user_code, state.correct_output)  # Reuse checking logic
    
    if "Correct" in response:
        state.is_correct = True
    else:
        state.is_correct = False  # This shouldn't happen often since LLM is correcting it.
    
    return state

graph.add_node("verify_corrected_code", verify_corrected_code)

# Step 5: Graph Flow with Correct Conditions
graph.add_edge(START, "process_explanation")
graph.add_edge("process_explanation", "check_and_hint")

# If correct, terminate
graph.add_conditional_edges(
    "check_and_hint",
    lambda x: "is_correct" if x.is_correct else "retry",
    {
        "is_correct": END,
        "retry": lambda x: "check_and_hint" if x.user_attempts < x.max_attempts else "generate_corrected_code"
    }
)

# After correction, verify and end
graph.add_edge("generate_corrected_code", "verify_corrected_code")
graph.add_edge("verify_corrected_code", END)
