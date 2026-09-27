from datetime import datetime
from flask import request
from ._base import _id_card_query_times, ID_CARD_QUERY_LIMIT, ID_CARD_QUERY_WINDOW


def check_id_card_rate_limit(person_id: str) -> tuple:
    ip = request.remote_addr
    now = datetime.now()

    if ip in _id_card_query_times:
        _id_card_query_times[ip] = [
            (ts, pid) for ts, pid in _id_card_query_times[ip]
            if (now - ts).total_seconds() < ID_CARD_QUERY_WINDOW
        ]

    if ip not in _id_card_query_times:
        _id_card_query_times[ip] = []

    query_count = len(_id_card_query_times[ip])

    if query_count >= ID_CARD_QUERY_LIMIT:
        oldest = _id_card_query_times[ip][0][0]
        remaining = ID_CARD_QUERY_WINDOW - (now - oldest).total_seconds()
        return False, int(remaining)

    _id_card_query_times[ip].append((now, person_id))
    return True, 0
