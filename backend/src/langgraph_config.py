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

def summarize(state: AgentState) -> AgentState:
    summary_prompt = PromptTemplate.from_template(
        input_variables=["explanation"],
        template="Explain this in simple terms and provide the output in buller points: {explanation}"
    )
    
    summary_text = llm.invoke(summary_prompt.format(explanation=state.explanation))
    state.summary = summary_text # storing the summary in the state; what it means is that the summary is being stored in the state in a new key called summary
    return state # returning the state after the summary is stored; the state now contains the summary as well as the explanaton 

graph.add_node("summarize", summarize)

    
def generate_boilerplate(state: AgentState) -> AgentState:
    prompt = PromptTemplate.from_template(
        input_variables=["explanation", "language"],
        template="Generate a boilerplate code with comments to help the user understand this explanation: {explanation} and the language is: {language}"    
    )
    
    boilerplate_code = llm.invoke(prompt.format(explanation=state.explanation))
    state.boilerplate_code = boilerplate_code
    return state
    
graph.add_node("generate_boilerplate", generate_boilerplate)

def generate_correct_output(state:AgentState) -> AgentState:    
    prompt = PromptTemplate.from_template(
        input_variables=["boilerplate_code", "language"],
        template="Generate the correct output for the given boilerplate code: {boilerplate_code} and the language is: {language}"
    )
    
    correct_output = llm.invoke(prompt.format(boilerplate_code=state.boilerplate_code))
    state.correct_output = correct_output
    return state
    
graph.add_node("generate_correct_output", generate_correct_output)
    
def check_user_output(state:AgentState) -> AgentState:
    state.user_attempts += 1
    prompt = PromptTemplate.from_template(
        input_variables=["user_code", "correct_output"],
        template="Compile the user's code and check if it is correct or not: {user_code} and the correct output is: {correct_output}"
    )
    
    is_correct = llm.invoke(prompt.format(user_code=state.user_code, correct_output=state.correct_output))
    state.is_correct = is_correct
    return state
    
graph.add_node("check_user_output", check_user_output)

def generate_hints(state:AgentState) -> AgentState:
    prompt = PromptTemplate.from_template(
        input_variables=["user_code", "is_correct"],
        template = "Generate a set of bullet points as hints to guide the user towards the right direction without giving away the answer. Make it based on the user's approach. Here is the user's code: {user_code}"
    )
    
    hints = llm.invoke(prompt.format(user_code=state.user_code))
    state.hints_given.append(hints)
    return state
    
graph.add_node("generate_hints", generate_hints)

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