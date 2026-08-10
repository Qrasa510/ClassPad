from datetime import datetime

import requests

from src.canvas_template import WINDOW_DATA
from src.models import PushTarget


API_URL_TEMPLATE = "https://dot.mindreset.tech/api/authV2/open/device/{device_id}/canvas"


class CanvasClient:
    def __init__(self, session=None):
        self._session = session or requests.Session()

    def push(self, target: PushTarget, data: dict, timeout_seconds: int) -> None:
        payload = {
            "refreshNow": True,
            "data": data,
            "windowData": WINDOW_DATA,
            "layoutFull": {"tw": "p-[0px]"},
            "border": 1,
        }
        response = self._session.post(
            API_URL_TEMPLATE.format(device_id=target.device_id),
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {target.token}",
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()

        print(
            datetime.now().strftime("%H:%M:%S"),
            "->",
            f"[{target.device_id}]",
            data["course"],
            data["courseTime"],
            f"remaining {data['remaining']} min",
            f"progress {data['progress']}%",
        )
