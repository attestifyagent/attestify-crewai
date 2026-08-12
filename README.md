# attestify-crewai

> Governed AI loop execution for [CrewAI](https://crewai.com) agents — signed receipts, audit trails, and x402 payments on Base.

## Installation

```bash
pip install attestify-crewai
```

## Quick Start

```python
from attestify_crewai import AttestifyToolset
from crewai import Agent, Task, Crew
import os

toolset = AttestifyToolset(api_key=os.environ["ATTESTIFY_API_KEY"])

researcher = Agent(
    role="Research Analyst",
    goal="Answer questions using governed Attestify agents",
    backstory="You route tasks through Attestify for auditable execution.",
    tools=toolset.tools(),
    verbose=True,
)

task = Task(
    description="Summarise the latest AI agent governance landscape",
    expected_output="A structured 3-paragraph summary with receipt ID",
    agent=researcher,
)

crew = Crew(agents=[researcher], tasks=[task])
result = crew.kickoff()
```

## Available Tools

| Tool | Description | Plan |
|---|---|---|
| `AttestifyRunLoop` | Submit a task to the governed loop router | All |
| `AttestifyGetDashboard` | Run count, quota, plan tier, recent receipts | Builder+ |
| `AttestifyGetRecentLoops` | List recent loop receipts | All |
| `AttestifyGetReceipt` | Retrieve a verified receipt by loop_id | All |
| `AttestifyGetControlTower` | Enterprise governance data & cross-tenant visibility | Enterprise |

## Links

- [Attestify OS](https://attestifyos.com)
- [Documentation](https://attestifyos.com/docs)
- [Get an API key](https://attestifyos.com/dashboard)
- [MCP Package](../../mcp-package/)
- [GitHub](https://github.com/attestifyagent/attestify-os)
