# this file contains the graph definitions and agent setup for the langgraph

from typing import TypedDict, Annotated, Sequence
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import State 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from main import get_llm
import os  # Also needed for os.getenv
from dotenv import load_dotenv
# loading environment variables for security
load_dotenv()

llm = get_llm()


# the state of the agent; this is the state that will be used to store the state of the agent
class AgentState(State):
    explanation: str = "" # the explanation provided by the user as the prompt to be used by the agent
    max_attempts: int = 3 # the maximum number of attempts to allow the user to submit the code 
    user_attempts: int = 0 # the number of attempts the user has made 
    language: str = "Python" # the programming language that the user wants to use
    user_code: str = "" # stores the user's code after each attempt
    correct_output: str = "" # the correct output that the user needs to submit 
    hints_given: list[str] = [] # the hints that the model provides to the user to help them solve the problem
    summary: str = "" # the summary of the explanation
    boilerplate_code: str = "" # the boilerplate code that the model provides to the user to help them understand the explanation

graph = StateGraph(AgentState)

# this function summarizes, generates boilerplate code, and generates the correct output
def process_explanation(state:AgentState) -> AgentState:
    prompt = PromptTemplate.from_template(
        input_variables=["explanation", "language"],
        template="""
        Based on the following explanation, perform the following tasks:
        1. Summarize the explanation in simple terms using bullet points.
        2. Generate a boilerplate code with comment in this language: {language}
        3. Generate the expected correct output for the given boilerplate code.
        4. Return the summary, boilerplate code, and correct output in three separate lines.
        Explanation: {explanation}
        """
    )
    response = llm.invoke(prompt.format(explanation=state.explanation, language=state.language))
    summary, boilerplate_code, correct_output = response.split('\n')
    state.summary = summary.strip()
    state.boilerplate_code = boilerplate_code.strip()
    state.correct_output = correct_output.strip()
    return state

graph.add_node("process_explanation", process_explanation)

#this function checks user output and generates hints if incorrect
def check_and_hint(state:AgentState) -> AgentState:
    state.user_attempts += 1
    prompt = PromptTemplate.from_template(
        input_variables=["user_code", "correct_output"],
        template="""Analyze the user's code against the expected correct output
        - If the code is correct, return: "Correct"
        - If incorrect, return: "Incorrect" followed by bullet-point hints to guide the user in fixing it.
        
        User Code: {user_code}
        Correct Output: {correct_output}
        """
    )
    response = llm.invoke(prompt.format(user_code=state.user_code, correct_output=state.correct_output))
    if "Correct" in response:
        state.is_correct = True
    else:
        state.is_correct = False
        hints = response.split("Incorrect")[1].strip()
        state.hints_given.append(hints)
    return state
    

def corrected_code(state:AgentState) -> AgentState:
    prompt = PromptTemplate.from_template(
        input_variables=["user_code", "hints_given"],
        template="Generate the corrected code based on the hints given: {hints_given} and the user's code: {user_code}"
    )
    
    corrected_code = llm.invoke(prompt.format(user_code=state.user_code, hints_given=state.hints_given))
    state.user_code = corrected_code
    return state
    
graph.add_node("corrected_code", corrected_code)

# adding edges
# Main flow
graph.add_edge(START, "summarize")
graph.add_edge("summarize", "generate_boilerplate")
graph.add_edge("generate_boilerplate", "generate_correct_output")
graph.add_edge("generate_correct_output", "check_user_output")

# Loop back to check user output if attempts remaining and not correct
graph.add_edge("check_user_output", "check_user_output", condition=lambda x: not x.is_correct and x.user_attempts < x.max_attempts)

# Generate hints if incorrect
graph.add_edge("check_user_output", "generate_hints", condition=lambda x: not x.is_correct)

# If correct, end the flow
graph.add_edge("check_user_output", END, condition=lambda x: x.is_correct)

# After hints, loop back to check output if attempts remain
graph.add_edge("generate_hints", "check_user_output", condition=lambda x: x.user_attempts < x.max_attempts)

# If max attempts reached, correct the code and end
graph.add_edge("generate_hints", "corrected_code", condition=lambda x: x.user_attempts >= x.max_attempts)
graph.add_edge("corrected_code", END)