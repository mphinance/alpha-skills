---
name: mental-model-evaluator
description: >
  Applies multi-disciplinary cognitive frameworks (e.g., Inversion, First Principles,
  Second-Order Thinking) to user plans and system designs to stress-test decisions.
---

# Mental Model Evaluator

*"Measure twice, cut once."*

Before making major architectural decisions, writing a massive feature, or executing a high-stakes trade plan, this skill forces a pause and runs the proposed plan through established cognitive mental models. 

## Core Mental Models

1. **Inversion:** "How could this plan completely fail?" Works backwards to identify guaranteed failure states and ensures the plan mitigates them.
2. **First Principles Thinking:** Strips the plan down to fundamental truths. Are we building on an assumption, or an undeniable fact?
3. **Second-Order Effects:** "And then what?" Evaluates the downstream consequences of the decision beyond the immediate payoff.
4. **Buffett's Moat Analysis:** Does this feature/trade provide a sustainable, defensible advantage, or is it easily replicated noise?

## Usage

When activated (Trigger phrases: "Evaluate this model", "Run the mental models", "Stress test this idea"):
1. Read the user's proposed plan or idea.
2. Output a structured markdown report that addresses the plan through the lens of at least 3 of the mental models above.
3. Conclude with a final `PASS`, `REVISE`, or `REJECT` verdict.
