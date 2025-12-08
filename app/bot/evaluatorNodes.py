from llms import llm_main
from prompts import prompt_avaliador_de_imoveis
from customTypes import State
from evaluatorTools import toolsList

def responder(state: State):
    prompt = prompt_avaliador_de_imoveis.invoke(state['messages'][-20:])
    response = llm_main.bind_tools(toolsList).invoke(prompt)
    return {'messages': response}