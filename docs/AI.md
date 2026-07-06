# RailYatra AI Platform Specification

This document details the multi-agent orchestration, predictive logic, and personalization memory system of **RailYatra**.

---

## 🤖 Multi-Agent Orchestrator Model
The AI Core operates as a state-based multi-agent system built using `LangGraph` in Python. Instead of passing all contexts to a single prompt, a **Master AI Orchestrator** delegates the request to the appropriate agent.

```
                  ┌────────────────────────┐
                  │  Master Orchestrator   │
                  └──────────┬─────────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Travel Agent │     │ Predictor    │     │ Optimizer    │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## 💬 Core Specialist Agents

1. **Travel Planner Agent:** Focuses on end-to-end journey itinerary creation.
2. **Prediction Agent:** Resolves waitlist confirmation and delay forecast models.
3. **Boarding Optimizer Agent:** Evaluates whether boarding from a nearby station increases booking confirmation.
4. **Destination Optimizer Agent:** Analyzes adjacent terminals to find better fares or schedules.
5. **Date Optimizer Agent:** Recommends alternative dates ($\pm 7$ days) with lower cancellation rates or costs.
6. **Fare Intelligence Agent:** Calculates cost savings using split-ticketing algorithms.

---

## 🧠 Memory & Personalization Architecture
- **Short-term Memory:** Session conversational contexts are stored in Redis using an sliding-window context structure.
- **Long-term Preferences:** Persistent settings (like preferred travel class, dietary needs, or accessibility requests) are stored in PostgreSQL with explicit consent flags.
- **Vector Base (RAG):** User travel history logs are vectorized and indexed in Qdrant for semantic contextualization.
- **Consent:** Under DPDP/GDPR rules, users have granular privacy buttons to inspect or delete stored contexts.
