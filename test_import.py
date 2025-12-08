
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add the project root to sys.path
sys.path.append(os.getcwd())


try:
    print("Attempting to import bot_controller...")
    from app.controllers import bot_controller
    print("Successfully imported bot_controller.")
except Exception as e:
    print(f"Failed to import bot_controller: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Attempting to import graph from app.bot.mainGraph...")
    # This mimics what the controller does internally
    from app.bot.mainGraph import graph
    print("Successfully imported graph.")
except Exception as e:
    print(f"Failed to import graph: {e}")
    import traceback
    traceback.print_exc()
