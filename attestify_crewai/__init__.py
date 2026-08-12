"""
attestify-crewai
================
CrewAI tool integration for Attestify — governed AI loop execution
with receipts, audit trails, and plan-gated enterprise features.

Quick start::

    from attestify_crewai import AttestifyToolset
    from crewai import Agent, Task, Crew
    import os

    toolset = AttestifyToolset(api_key=os.environ["ATTESTIFY_API_KEY"])
    tools   = toolset.tools()

    researcher = Agent(
        role="Research Analyst",
        goal="Answer questions using governed Attestify agents",
        backstory="You route tasks through Attestify for auditable execution.",
        tools=tools,
        verbose=True,
    )

    task = Task(
        description="Summarise the latest AI governance news",
        expected_output="A 3-paragraph summary with receipt ID",
        agent=researcher,
    )

    crew = Crew(agents=[researcher], tasks=[task])
    result = crew.kickoff()

Available tools (returned by ``toolset.tools()``):

  AttestifyRunLoop
      Submit a task to the Attestify loop router.
      Returns loop_id, status, cost, and a receipt URL.

  AttestifyGetDashboard
      Fetch run count, quota, plan tier, and recent receipts.

  AttestifyGetRecentLoops
      List recent loop receipts for the tenant.

  AttestifyGetReceipt
      Retrieve a single verified receipt by loop_id.

  AttestifyGetControlTower
      Enterprise-only: live governance data and cross-tenant visibility.
"""

from __future__ import annotations

from .toolset import AttestifyToolset
from .tools import (
    AttestifyRunLoop,
    AttestifyGetDashboard,
    AttestifyGetRecentLoops,
    AttestifyGetReceipt,
    AttestifyGetControlTower,
)

__version__ = "0.1.1"

__all__ = [
    "AttestifyToolset",
    "AttestifyRunLoop",
    "AttestifyGetDashboard",
    "AttestifyGetRecentLoops",
    "AttestifyGetReceipt",
    "AttestifyGetControlTower",
]
