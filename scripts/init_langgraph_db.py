import os
import sys
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

DB_URI = os.environ.get("DATABASE_URL")

if not DB_URI:
    print("DATABASE_URL not found in environment variables.")
    sys.exit(1)

def init_db():
    print("Initializing LangGraph database tables...")
    # We need to ensure autocommit is used for setup if it does concurrent index creation
    # However, PostgresSaver.setup() usually handles what it needs. 
    # The error "CREATE INDEX CONCURRENTLY cannot run inside a transaction block" 
    # suggests we need to be careful about how the connection is used.
    
    # Let's try using a pool and running setup.
    # Disable server-side prepared statements to avoid duplicate prepared statement errors
    # when the pool shares connections across threads.
    with ConnectionPool(conninfo=DB_URI, kwargs={"autocommit": True, "prepare_threshold": None}) as pool:
        checkpointer = PostgresSaver(pool)
        checkpointer.setup()
    print("Done.")

if __name__ == "__main__":
    init_db()
