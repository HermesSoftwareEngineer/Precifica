from customTypes import State
from llm import llm
from tools import toolsList
from prompts import prompt_avaliador_de_imoveis

def responder(state: State):

    prompt = prompt_avaliador_de_imoveis.invoke(state['messages'][-20:])
    response = llm.bind_tools(toolsList).invoke(prompt)
    return {'messages': response}