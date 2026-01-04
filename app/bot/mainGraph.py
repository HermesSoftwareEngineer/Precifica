import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from customTypes import State
from mainNodes import responder
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection
from psycopg.rows import dict_row
from langgraph.prebuilt import tools_condition
from mainTools import tools_node

load_dotenv()

DB_URI = os.environ.get("DATABASE_URL")
# Use a single Connection with prepare_threshold=None to avoid pool-related prepared-statement races
conn = Connection.connect(DB_URI, autocommit=True, prepare_threshold=None, row_factory=dict_row)
checkpointer = PostgresSaver(conn)
# checkpointer.setup() # Moved to scripts/init_langgraph_db.py to avoid transaction errors during startup

graph_builder = StateGraph(State)

graph_builder.add_node("responder", responder)
graph_builder.add_node("tools", tools_node)

graph_builder.add_edge(START, "responder")
graph_builder.add_conditional_edges("responder", tools_condition, {"tools": "tools", END: END})
graph_builder.add_edge("tools", "responder")
graph_builder.add_edge("responder", END)

graph = graph_builder.compile(checkpointer=checkpointer)