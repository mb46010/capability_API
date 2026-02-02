# Why We are Building the Capability API: The Trust Layer for HR AI

## The Big Picture
In most companies today, HR processes are fragmented. Employee data lives in complex systems like Workday, payroll runs in another, and requests for time off or onboarding are handled through a mix of emails, tickets, and spreadsheets. 

As we introduce **AI Agents** (like Claude or Gemini) to help employees and managers navigate these systems, we face a major challenge: **How do we let a robot handle sensitive data without risking a massive security breach?**

**We are building the Capability API: a single, secure gateway that acts as a "Trust Layer" between AI and our most sensitive human data.**

---

## The Five Pillars of Our Solution

To make AI safe for HR, we’ve built five integrated components that work together to ensure security, safety, and transparency.

### 1. The Capability API (The Orchestrator)
This is the "Universal Remote Control" for HR. Instead of letting every app or AI agent talk directly to our databases, they all talk to this API. It ensures that every action is performed consistently, regardless of whether a human or a robot triggered it.

### 2. The Workday Simulator (The Safety Playground)
We can't just "test" our AI on real employee salary data. Our **Simulator** is a high-fidelity, virtual copy of our HR system. it allows developers and AI to practice submitting time-off requests or viewing org charts in a 100% safe environment with synthetic data.

### 3. Okta Auth & Token Exchange (The Identity Guard)
We use industry-standard security (Okta) to verify exactly who is making a request. For AI agents, we use a specialized process called **Token Exchange**. This gives the AI a "temporary pass" that lasts only 5 minutes and is limited to very specific tasks, ensuring that even if an AI is compromised, the "blast radius" is tiny.

### 4. MCP Servers (The AI Bridge)
AI models need a way to "see" and "use" HR tools. Our **MCP (Model Context Protocol) Servers** act as the bridge. They translate the complex language of HR systems into simple "tools" that an AI can understand, while simultaneously enforcing our strict security rules—including full JWT signature verification—at the very edge where the AI operates.

### 5. Policy Verification (The Safety Net)
Security rules are written in a master file (Policy YAML). However, humans can make mistakes when writing these rules. Our **Policy Verification Framework** mathematically proves our security rules work as intended before they go live. It prevents "silent security holes" by automatically testing 100+ scenarios every time a rule is changed.

### 6. Backstage Governance (The Transparent Lens)
Governance is useless if it's invisible. Our **Backstage Integration** provides a browsable, human-friendly view of the entire platform. it allows non-technical stakeholders to see every capability, its sensitivity, and the exact policy that governs it, ensuring the "Trust Layer" is verifiable by everyone in the company.

---

## Why This Matters to the Business

1.  **Zero Trust Security**: We never assume an AI agent is safe. Every request is verified. If the policy doesn't explicitly say "Yes," the answer is "No."
2.  **Continuous Compliance**: We generate audit-ready reports that prove to regulators and security teams that we are enforcing least-privilege access at all times.
3.  **Audit Trail & Provenance**: We log everything. If an AI agent performs an action, our logs show exactly which AI did it, which user it was helping, and which security rule allowed it.
4.  **Agility with Safety**: We can launch new AI features in days instead of months because the "Trust Layer" handles the hard security work for us.

---

## What to Expect in a Demo

When you see a demo of this system, you are seeing **governance in action**:

*   **The AI Guardrail**: An AI assistant helps an employee check their PTO balance (Allowed), but is instantly blocked if it tries to peek at a colleague's payroll (Denied).
*   **Scoped AI Access**: You'll see the AI get a "short-term pass" to do its job, which automatically expires, leaving no permanent access behind.
*   **The Policy Safety Net**: You'll see a developer try to accidentally give an AI agent too much power, only to have the system **block the commit** and demand a correction.
*   **Transparent Reporting**: You'll see a clean report that proves our system is 100% compliant with our security requirements (SEC-001 through SEC-005).

## Summary
We aren't just writing code to move data; we are building the **trust infrastructure** that allows our company to safely use AI in the most sensitive area of our business: our people.