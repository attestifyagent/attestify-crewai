"""
Internal HTTP helper — identical contract to attestify_langchain._http
but with no langchain-core dependency.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Optional

DEFAULT_BASE_URL = "https://attestifyos.com"
DEFAULT_TIMEOUT  = 60.0
DEFAULT_RETRIES  = 2


class AttestifyError(Exception):
    def __init__(self, message: str, status: Optional[int] = None, body: Any = None):
        super().__init__(message)
        self.status = status
        self.body   = body

class AttestifyAuthError(AttestifyError): pass
class AttestifyPaymentError(AttestifyError): pass
class AttestifyPermissionError(AttestifyError): pass


class _Client:
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL,
                 timeout_s: float = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_RETRIES):
        if not api_key:
            raise ValueError("AttestifyToolset: api_key is required.")
        self._api_key     = api_key
        self._base_url    = base_url.rstrip("/")
        self._timeout_s   = timeout_s
        self._max_retries = max_retries

    def _headers(self) -> dict:
        return {"Content-Type": "application/json", "X-API-Key": self._api_key}

    def get(self, path: str) -> dict:
        req = urllib.request.Request(f"{self._base_url}{path}", headers=self._headers(), method="GET")
        return self._send(req, path)

    def post(self, path: str, payload: dict) -> dict:
        data = json.dumps(payload).encode()
        req  = urllib.request.Request(f"{self._base_url}{path}", data=data, headers=self._headers(), method="POST")
        return self._send(req, path)

    def _send(self, req, path: str) -> dict:
        last_exc = None
        for _ in range(self._max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as exc:
                body = None
                try: body = json.loads(exc.read())
                except Exception: pass
                msg = (body.get("error") or str(body)) if isinstance(body, dict) else str(exc)
                if exc.code == 401: raise AttestifyAuthError(f"401 Unauthorized ({path})", 401, body) from exc
                if exc.code == 402: raise AttestifyPaymentError(f"402 Payment required ({path})", 402, body) from exc
                if exc.code == 403: raise AttestifyPermissionError(f"403 Plan gate — {msg} ({path})", 403, body) from exc
                if exc.code < 500:  raise AttestifyError(f"{exc.code} {msg} ({path})", exc.code, body) from exc
                last_exc = AttestifyError(f"{exc.code} server error ({path})", exc.code, body)
            except urllib.error.URLError as exc:
                last_exc = AttestifyError(f"Network error: {exc.reason} ({path})")
        raise last_exc
