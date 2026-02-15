from threading import Lock

_canceled_evaluations = set()
_lock = Lock()


def cancel_evaluation(evaluation_id):
    with _lock:
        _canceled_evaluations.add(evaluation_id)


def clear_evaluation_cancel(evaluation_id):
    with _lock:
        _canceled_evaluations.discard(evaluation_id)


def is_evaluation_canceled(evaluation_id):
    with _lock:
        return evaluation_id in _canceled_evaluations
