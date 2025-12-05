from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from customTypes import State
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition
from nodes import responder
from tools import tools_node

load_dotenv()

# Iniciando o construtor do grafo
graph_builder = StateGraph(State)

# Definindo os nós
graph_builder.add_node("responder", responder)
graph_builder.add_node("tools", tools_node)

# Definindo as pontes
graph_builder.add_edge(START, "responder")
graph_builder.add_conditional_edges("responder", tools_condition, {"tools": "tools", END: END})
graph_builder.add_edge("tools", "responder")
graph_builder.add_edge("responder", END)

# Construindo o grafo com memória
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)