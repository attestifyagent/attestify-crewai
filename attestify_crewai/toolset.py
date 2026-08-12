"""
AttestifyToolset — main entry point for the CrewAI integration.

Usage::

    toolset = AttestifyToolset(api_key=os.environ["ATTESTIFY_API_KEY"])
    tools   = toolset.tools()
    agent   = Agent(role="...", tools=tools)
"""

from __future__ import annotations

from typing import List
from ._http import _Client, DEFAULT_BASE_URL, DEFAULT_TIMEOUT, DEFAULT_RETRIES
from .tools import (
    AttestifyRunLoop, AttestifyGetDashboard, AttestifyGetRecentLoops,
    AttestifyGetReceipt, AttestifyGetControlTower,
)


class AttestifyToolset:
    """
    CrewAI toolset for Attestify.

    Args:
        api_key:               Your Attestify API key (``att_live_...``).
        base_url:              Override the default API base URL.
        timeout_s:             HTTP timeout in seconds. Default 60.
        max_retries:           Retries on 5xx errors. Default 2.
        include_control_tower: Include the Enterprise Control Tower tool.
    """

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL,
                 timeout_s: float = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_RETRIES,
                 include_control_tower: bool = True):
        self._client = _Client(api_key=api_key, base_url=base_url,
                               timeout_s=timeout_s, max_retries=max_retries)
        self._include_control_tower = include_control_tower

    def tools(self) -> List:
        """
        Return all Attestify tools as a list of CrewAI BaseTool instances.
        Pass directly to the ``tools`` argument of a CrewAI ``Agent``.
        """
        t = [
            AttestifyRunLoop(self._client),
            AttestifyGetDashboard(self._client),
            AttestifyGetRecentLoops(self._client),
            AttestifyGetReceipt(self._client),
        ]
        if self._include_control_tower:
            t.append(AttestifyGetControlTower(self._client))
        return t
