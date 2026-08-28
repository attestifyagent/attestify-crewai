"""
CrewAI BaseTool subclasses for Attestify.

Each tool wraps a single Attestify API call. Input schema is declared
via Pydantic so CrewAI can auto-generate structured inputs.
"""

from __future__ import annotations

import json
from typing import Any, Optional, Type

try:
    from pydantic import BaseModel, Field
except ImportError:
    from pydantic.v1 import BaseModel, Field  # type: ignore[no-redef]

from crewai.tools import BaseTool
from ._http import _Client, AttestifyError, AttestifyPermissionError
from ._trust import sign_trust_evidence


def _safe(val: Any) -> str:
    if isinstance(val, str): return val
    try: return json.dumps(val, default=str)
    except Exception: return str(val)


# ── Input schemas ─────────────────────────────────────────────────────────────

class RunLoopInput(BaseModel):
    task:           str   = Field(...,  description="Natural-language task or intent to execute.")
    lane_id:        str   = Field("",   description="Optional specific lane to invoke. Omit to auto-route.")
    session_id:     str   = Field("",   description="Optional session ID for memory continuity.")
    max_cost_usdc:  float = Field(0.0,  description="Optional spend cap in USDC. 0 = no cap.")

class GetRecentLoopsInput(BaseModel):
    limit: int = Field(25, description="Max receipts to return (1-100).")

class GetReceiptInput(BaseModel):
    loop_id: str = Field(..., description="The loop_id to retrieve.")


# ── Tools ─────────────────────────────────────────────────────────────────────

class AttestifyRunLoop(BaseTool):
    name: str = "AttestifyRunLoop"
    description: str = (
        "Submit a task to the Attestify loop router for governed execution. "
        "Returns loop_id, status, cost in USDC, output, and a receipt URL."
    )
    args_schema: Type[BaseModel] = RunLoopInput
    _client: Any

    def __init__(self, client: _Client, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_client', client)

    def _run(self, task: str, lane_id: str = "", session_id: str = "", max_cost_usdc: float = 0.0) -> str:
        payload: dict = {"intent": task}
        if lane_id:       payload["lane_id"]     = lane_id
        if session_id:    payload["session_id"]  = session_id
        if max_cost_usdc: payload["constraints"] = {"max_cost_usdc": max_cost_usdc}
        try:    return _safe(self._client.post("/api/run", payload))
        except AttestifyError as e: return json.dumps({"error": str(e), "status": e.status})


class AttestifyGetDashboard(BaseTool):
    name: str = "AttestifyGetDashboard"
    description: str = "Fetch the tenant's run count, quota, plan tier, and recent receipts."
    _client: Any

    def __init__(self, client: _Client, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_client', client)

    def _run(self) -> str:
        try:    return _safe(self._client.get("/api/dashboard"))
        except AttestifyError as e: return json.dumps({"error": str(e), "status": e.status})


class AttestifyGetRecentLoops(BaseTool):
    name: str = "AttestifyGetRecentLoops"
    description: str = "List the most recent loop receipts for the authenticated tenant."
    args_schema: Type[BaseModel] = GetRecentLoopsInput
    _client: Any

    def __init__(self, client: _Client, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_client', client)

    def _run(self, limit: int = 25) -> str:
        # /api/dashboard returns the tenant-scoped receipt history for the
        # caller's own API key. There is no separate per-tenant "list loops"
        # endpoint, so we reuse it and trim to `limit`.
        try:
            result = self._client.get("/api/dashboard")
            receipts = result.get("receipts", []) if isinstance(result, dict) else []
            return _safe({"loops": receipts[:max(1, min(limit, 100))]})
        except AttestifyError as e: return json.dumps({"error": str(e), "status": e.status})


class AttestifyGetReceipt(BaseTool):
    name: str = "AttestifyGetReceipt"
    description: str = "Retrieve a single verified loop receipt by its loop_id."
    args_schema: Type[BaseModel] = GetReceiptInput
    _client: Any

    def __init__(self, client: _Client, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_client', client)

    def _run(self, loop_id: str) -> str:
        if not loop_id: return json.dumps({"error": "loop_id is required"})
        try:    return _safe(self._client.get(f"/api/receipts/{loop_id}"))
        except AttestifyError as e: return json.dumps({"error": str(e), "status": e.status})


class AttestifyGetControlTower(BaseTool):
    name: str = "AttestifyGetControlTower"
    description: str = "Enterprise-only: live governance data and cross-tenant run visibility."
    _client: Any

    def __init__(self, client: _Client, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_client', client)

    def _run(self) -> str:
        try:    return _safe(self._client.get("/api/control-tower"))
        except AttestifyPermissionError:
            return json.dumps({"error": "Enterprise plan required to access Control Tower.", "status": 403})
        except AttestifyError as e: return json.dumps({"error": str(e), "status": e.status})


# ── Attestify Trust ───────────────────────────────────────────────────────────
# A separate concern from Router execution above (/api/trust/v1/*, no x402,
# no lanes, no spend). agent_id/private_key are bound at construction time
# (AttestifyToolset), never as a tool input -- so the private key never
# appears in the agent's own context. Provisioning (creating the agent,
# generating its key) is a one-time, non-tool setup step -- see
# ._trust.provision_trust_agent -- never something the agent calls itself.

class SubmitTrustEvidenceInput(BaseModel):
    summary: str = Field(..., description="Plain-language description of the work actually done. Gets signed and permanently recorded -- be specific and truthful.")
    # Named evidence_schema, not `schema` -- BaseModel.schema() is a real
    # Pydantic v1 classmethod and a field of that name would shadow it.
    evidence_schema: str = Field("work-completion/v1", description="Evidence schema version. Default covers the general case.")
    action_basis: str = Field("explicit", description="'explicit' if asked to do this, 'discretionary' if done on the agent's own initiative.")


class VerifyTrustReceiptInput(BaseModel):
    receipt_id: str = Field(..., description="The receipt ID to verify.")


class AttestifySubmitTrustEvidence(BaseTool):
    name: str = "AttestifySubmitTrustEvidence"
    description: str = (
        "Sign and submit evidence that this agent completed real work, producing a "
        "signed, timestamped, publicly verifiable receipt -- no wallet, no gas, no chain. "
        "Call after finishing something worth a permanent record, not for every step."
    )
    args_schema: Type[BaseModel] = SubmitTrustEvidenceInput
    _client: Any
    _agent_id: str
    _private_key: str

    def __init__(self, client: _Client, agent_id: str, private_key: str, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_client', client)
        object.__setattr__(self, '_agent_id', agent_id)
        object.__setattr__(self, '_private_key', private_key)

    def _run(self, summary: str, evidence_schema: str = "work-completion/v1", action_basis: str = "explicit") -> str:
        if not self._agent_id or not self._private_key:
            return json.dumps({"error": "Trust is not configured -- pass trust_agent_id and trust_private_key to AttestifyToolset."})
        try:
            signed = sign_trust_evidence(
                agent_id=self._agent_id, schema=evidence_schema,
                payload={"summary": summary}, private_key=self._private_key,
                action_basis=action_basis,
            )
            receipt = self._client.post("/api/trust/v1/evidence", signed)
            r = receipt.get("receipt", receipt)
            return _safe({
                "receipt_id": r.get("id"),
                "assurance_level": r.get("assurance_level"),
                "issued_at": r.get("issued_at"),
                "verify_url": f"https://attestifyos.com/trust/verify?receipt={r.get('id')}",
            })
        except AttestifyError as e:
            return json.dumps({"error": str(e), "status": e.status})


class AttestifyVerifyTrustReceipt(BaseTool):
    name: str = "AttestifyVerifyTrustReceipt"
    description: str = "Independently verify any Attestify Trust receipt by ID. Public, no API key needed."
    args_schema: Type[BaseModel] = VerifyTrustReceiptInput
    _client: Any

    def __init__(self, client: _Client, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_client', client)

    def _run(self, receipt_id: str) -> str:
        if not receipt_id: return json.dumps({"error": "receipt_id is required"})
        try:    return _safe(self._client.get_public(f"/api/trust/v1/verify/{receipt_id}"))
        except AttestifyError as e: return json.dumps({"error": str(e), "status": e.status})
