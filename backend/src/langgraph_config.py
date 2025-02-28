# this file contains the graph definitions and agent setup for the langgraph

from typing import TypedDict, Annotated, Sequence
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import State 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage


# the state of the agent; this is the state that will be used to store the state of the agent
class AgentState(State):
    explanation: str = "" # the explanation provided by the user as the prompt to be used by the agent
    max_attempts: int = 3 # the maximum number of attempts to allow the user to submit the code 
    user_attempts: int = 0 # the number of attempts the user has made 
    user_code: str = "" # stores the user's code after each attempt
    correct_code: str = "" # the correct code that the user needs to submit (should be dynamic, as the user's approach may be different so has to update based on the user's approach)
    best_code: str = "" # the best code that the model thinks is the correct code
    hints_given: str = "" # the hints that the model provides to the user to help them solve the problem
    summary: str = "" # the summary of the explanation
    boilerplate_code: str = "" # the boilerplate code that the model provides to the user to help them understand the explanation

graph = StateGraph(AgentState)

def summarize(state: AgentState) -> AgentState:
    llm = ChatGoogleGenerativeAI(
        model_name="gemini-1.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    summary_prompt = PromptTemplate.from_template(
        input_variables=["explanation"],
        template="Explain this in simple terms and provide the output in buller points: {explanation}"
    )
    
    summary_text = llm.invoke(summary_prompt.format(explanation=state.explanation))
    state.summary = summary_text # storing the summary in the state; what it means is that the summary is being stored in the state in a new key called summary
    return state # returning the state after the summary is stored; the state now contains the summary as well as the explanaton 

graph.add_node("summarize", summarize)

    
def generate_boilerplate(state: AgentState) -> AgentState:
    llm = ChatGoogleGenerativeAI(
        model_name="gemini-1.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    prompt = PromptTemplate.from_template(
        input_variables=["explanation"],
        template="Generate a boilerplate code with comments to help the user understand this explanation: {summary}"    
    )
    
    boilerplate_code = llm.invoke(prompt.format(summary=state.summary))
    state.boilerplate_code = boilerplate_code
    return state
    
graph.add_node("generate_boilerplate", generate_boilerplate)

def generate_correct_code(state:AgentState) -> AgentState:
    llm = ChatGoogleGenerativeAI(
        model_name="gemini-1.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    
    prompt = PromptTemplate.from_template(
        input_variables=["boilerplate_code"],
        template="Generate the correct code for the given boilerplate code: {boilerplate_code}"
    )
    
    correct_code = llm.invoke(prompt.format(boilerplate_code=state.boilerplate_code))
    state.correct_code = correct_code
    return state
    
graph.add_node("generate_correct_code", generate_correct_code)
    
    
