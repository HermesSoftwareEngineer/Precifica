import json
import time
from queue import Queue, Empty
from threading import Lock

_listeners = {}
_lock = Lock()


def register_listener(channel_key):
    queue = Queue()
    with _lock:
        listeners = _listeners.get(channel_key)
        if listeners is None:
            listeners = set()
            _listeners[channel_key] = listeners
        listeners.add(queue)
    return queue


def remove_listener(channel_key, queue):
    with _lock:
        listeners = _listeners.get(channel_key)
        if not listeners:
            return
        listeners.discard(queue)
        if not listeners:
            _listeners.pop(channel_key, None)


def publish_event(channel_key, event, data):
    payload = {
        "event": event,
        "data": data,
        "ts": int(time.time())
    }
    with _lock:
        listeners = list(_listeners.get(channel_key, []))
    for queue in listeners:
        queue.put(payload)


def format_sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=True)}\n\n"
