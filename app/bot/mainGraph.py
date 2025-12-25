import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from customTypes import State
from mainNodes import responder
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from langgraph.prebuilt import tools_condition
from mainTools import tools_node

load_dotenv()

DB_URI = os.environ.get("DATABASE_URL")
pool = ConnectionPool(conninfo=DB_URI, max_size=20, kwargs={"autocommit": True})
checkpointer = PostgresSaver(pool)
# checkpointer.setup() # Moved to scripts/init_langgraph_db.py to avoid transaction errors during startup

graph_builder = StateGraph(State)

graph_builder.add_node("responder", responder)
graph_builder.add_node("tools", tools_node)

graph_builder.add_edge(START, "responder")
graph_builder.add_conditional_edges("responder", tools_condition, {"tools": "tools", END: END})
graph_builder.add_edge("tools", "responder")
graph_builder.add_edge("responder", END)

graph = graph_builder.compile(checkpointer=checkpointer)