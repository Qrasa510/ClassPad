import logging

import requests

from src.canvas_template import WINDOW_DATA
from src.http_client import create_retry_session
from src.models import PushTarget


logger = logging.getLogger(__name__)
API_URL_TEMPLATE = "https://dot.mindreset.tech/api/authV2/open/device/{device_id}/canvas"


class CanvasError(RuntimeError):
    pass


class CanvasAuthError(CanvasError):
    pass


class CanvasClient:
    def __init__(self, session=None):
        self._session = session or create_retry_session()

    def push(self, target: PushTarget, data: dict, timeout_seconds: int) -> None:
        payload = {
            "refreshNow": True,
            "data": data,
            "windowData": WINDOW_DATA,
            "layoutFull": {"tw": "p-[0px]"},
            "border": 1,
        }
        try:
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
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status in {401, 403}:
                raise CanvasAuthError(
                    f"设备 {target.device_id} 认证失败，请检查 token（HTTP {status}）"
                ) from exc
            raise CanvasError(
                f"设备 {target.device_id} 推送失败（HTTP {status or 'unknown'}）"
            ) from exc
        except requests.RequestException as exc:
            raise CanvasError(f"设备 {target.device_id} 网络请求失败: {exc}") from exc

        logger.info(
            "已经送达 · %s · %s · %s · 剩余 %s 分钟 · %s%%",
            target.device_id,
            data.get("course", ""),
            data.get("courseTime", ""),
            data.get("remaining", ""),
            data.get("progress", ""),
        )
