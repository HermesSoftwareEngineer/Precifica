from mainGraph import graph
from dotenv import load_dotenv

load_dotenv()

config = {"configurable": {"thread_id": "123"}}

def stream_graph_update(user_input: str):
    response = graph.invoke({"messages": user_input}, config)
    print("Agent IA: ", response['messages'][-1].content)

while True:
    user_input = input("Usuário: ")
    if user_input.lower in ['quit', 'sair', 'q']:
        break
    stream_graph_update(user_input)