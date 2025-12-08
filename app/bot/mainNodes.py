from llms import llm_main
from customTypes import State
from mainTools import toolsList

def responder(state: State):
    response = llm_main.bind_tools(toolsList).invoke(state['messages'][-20:])
    return {'messages': response}