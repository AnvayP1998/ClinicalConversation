# Autonomous Clinical Conversation Agent (Portfolio Project)

A synthetic-data demonstration of an LLM-driven post-discharge medication check-in call
agent, built with an explicit safety-first architecture: a deterministic state machine,
hard-coded (non-LLM) escalation overrides, per-state scoped prompts, and an adversarial
evaluation harness used to measure and iterate on guardrail behavior.

See [SPEC.md](SPEC.md) for the full design, safety model, and non-goals.

**This is not a real clinical tool. It uses no real patient data and is not deployed to
real people.**

Full architecture, results, and iteration history will be documented here as the project
progresses through its build phases.
