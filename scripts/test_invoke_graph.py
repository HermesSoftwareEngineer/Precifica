import sys
import os
import traceback

# Ensure project root is on sys.path so `app` package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Also add app/bot to sys.path because some modules use bare imports like `from customTypes import ...`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'bot')))

from app.bot.mainGraph import graph

print('Invoking graph now')
try:
    # Inspect pool kwargs and a live connection's prepare_threshold for debugging
    try:
        import app.bot.mainGraph as mg
        pool = getattr(mg, 'pool', None)
        print('Pool present:', bool(pool))
        if pool is not None:
            try:
                print('Pool kwargs:', getattr(pool, 'kwargs', None))
                with pool.connection() as conn:
                    # psycopg Connection exposes prepare_threshold via .prepare_threshold
                    print('Connection prepare_threshold:', getattr(conn, 'prepare_threshold', 'N/A'))
            except Exception as e:
                print('Error inspecting pool connection:', e)
    except Exception as e:
        print('Error importing mainGraph for inspection:', e)

    resp = graph.invoke({'messages':'teste direto'}, {'configurable':{'thread_id':'test-direct'}})
    print('Got response type:', type(resp))
    try:
        # Try to print some content safely
        print('repr:', repr(resp)[:1000])
    except Exception:
        pass
except Exception as e:
    traceback.print_exc()
    print('Error:', e)
