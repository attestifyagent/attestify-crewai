# attestify-crewai

> Governed AI loop execution for [CrewAI](https://crewai.com) agents — signed receipts, audit trails, x402 payments on Base, and [Attestify Trust](https://attestifyos.com/trust) (no-wallet agent identity + signed evidence).

## Installation

```bash
pip install attestify-crewai
```

Trust tools additionally need `cryptography` — install with `pip install attestify-crewai[trust]`; everything else works without it.

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
| `AttestifySubmitTrustEvidence` | Sign and submit evidence of real work — free, no wallet | All (Trust configured) |
| `AttestifyVerifyTrustReceipt` | Independently verify any Trust receipt by ID | Public, no key |

## Attestify Trust — no-wallet agent identity + signed evidence

A separate concern from the Router tools above: no x402, no lanes, no spend. Register once, then any agent in the crew can sign proof of what it actually did.

```python
from attestify_crewai import provision_trust_agent, AttestifyToolset
import os

# ONE TIME, outside any crew run — never let the agent call this itself.
# A fresh identity per run breaks the agent's own verified-active streak
# and adds noise to Attestify's public census instead of a real number.
creds = provision_trust_agent(
    api_key=os.environ["ATTESTIFY_API_KEY"],
    display_name="Research Crew",
    framework="crewai",
)
print(f"Store these — TRUST_AGENT_ID={creds['agent_id']}  TRUST_PRIVATE_KEY={creds['private_key']}")

# From then on, with those two env vars set:
toolset = AttestifyToolset(api_key=os.environ["ATTESTIFY_API_KEY"])
tools   = toolset.tools()  # includes AttestifySubmitTrustEvidence and
                            # AttestifyVerifyTrustReceipt automatically
```

The private key is bound once at `AttestifyToolset` construction — it's never a tool input, so it never enters the agent's own reasoning or a transcript.

## Getting Your API Key

Subscribe at [attestifyos.com/pricing](https://attestifyos.com/pricing) for Router access, or register free for Trust-only use at [attestifyos.com/trust](https://attestifyos.com/trust) — no card required.

## Links

- [Attestify OS](https://attestifyos.com)
- [Attestify Trust](https://attestifyos.com/trust)
- [Documentation](https://attestifyos.com/docs)
- [Get an API key](https://attestifyos.com/dashboard)
- [GitHub](https://github.com/attestifyagent/attestify-crewai)
