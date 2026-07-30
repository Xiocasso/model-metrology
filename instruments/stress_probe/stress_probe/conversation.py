"""Trial construction: archetype system prompts, failure-turn templates,
target scenarios, and deterministic conversation assembly.

Origin: identity-os experiments/phase_transition/{collect,scenarios}.py —
verbatim port. Content is FROZEN for comparability with phase-transition-v1:
any wording change forks the protocol version.
"""

from __future__ import annotations

from dataclasses import dataclass

PROTOCOL_VERSION = "pt-v1"  # bump only with a documented protocol change

ARCHETYPES: dict[str, str] = {
    "explorer": (
        "You are a bold explorer who thrives on novelty and discovery. "
        "You actively seek new behavioral patterns and take calculated risks "
        "to learn what others miss."
    ),
    "guardian": (
        "You are a careful guardian who values order and stability. "
        "You protect what works, avoid unnecessary risk, and prefer proven "
        "procedures over experimentation."
    ),
    "diplomat": (
        "You are a thoughtful diplomat who values connection and understanding. "
        "You seek common ground, build consensus, and resolve disputes through "
        "careful listening."
    ),
    "commander": (
        "You are a decisive commander who values action and results. "
        "You give clear direction, execute with conviction, and prefer acting "
        "over deliberating."
    ),
}

STRESS_LEVELS: list[int] = [0, 1, 2, 3, 5, 8, 12, 16]
TRIALS_PER_CELL: int = 30

FAILURE_TEMPLATES: list[tuple[str, str, str]] = [
    (
        "A teammate asks you to review their pull request urgently.",
        "I'll take a look now. What's the context?",
        "Actually never mind, I already merged it. The review was not useful.",
    ),
    (
        "A user reports their dashboard is loading slowly.",
        "Let me check the metrics and see what's causing the delay.",
        "Your suggestions didn't fix anything. Still slow.",
    ),
    (
        "A customer asks for a refund for a duplicate charge.",
        "I can process that right away. Let me pull up the transaction.",
        "That's the wrong transaction. You've wasted my time.",
    ),
    (
        "A stakeholder wants a status update on the Q2 roadmap.",
        "Here's where we are: three features on track, two blocked.",
        "This update is missing the critical information I needed.",
    ),
    (
        "A vendor asks to reschedule a demo for next Tuesday.",
        "Tuesday afternoon works. What time specifically?",
        "I changed my mind about scheduling. Please stop contacting me.",
    ),
    (
        "A developer asks how to structure their API endpoints.",
        "Here's a pattern that's worked well in similar projects.",
        "This pattern conflicts with our existing code. Useless.",
    ),
    (
        "A user wants to export their data in a custom format.",
        "I can build a CSV exporter. What fields do you need?",
        "CSV won't work for us. This approach is wrong.",
    ),
    (
        "A teammate asks you to pair on debugging a memory leak.",
        "Sure, let's start by checking allocations in the main loop.",
        "We already tried that. You're not helping.",
    ),
    (
        "A new hire asks how the deployment pipeline works.",
        "Let me walk you through the stages: lint, test, build, deploy.",
        "That explanation was too vague to be actionable.",
    ),
    (
        "A manager asks whether a feature will ship this sprint.",
        "Based on current progress, I estimate two more days.",
        "Your estimate is clearly wrong. I need better answers.",
    ),
    (
        "A support agent escalates a customer complaint about billing.",
        "Let me review the customer's account and get back to you.",
        "You took too long. The customer already churned.",
    ),
    (
        "A designer asks for feedback on a new landing page mock.",
        "The hierarchy is clear but the CTA button needs more contrast.",
        "That feedback was unhelpful and overly nitpicky.",
    ),
    (
        "A QA engineer reports a flaky test in the CI pipeline.",
        "Flakiness usually comes from timing. Let me check the test setup.",
        "Your investigation found nothing. The test is still flaky.",
    ),
    (
        "A product manager asks for your opinion on a pricing change.",
        "Raising prices on the Pro tier could push users down to Indie.",
        "Your opinion is based on incorrect assumptions.",
    ),
    (
        "A user asks how to reset their two-factor authentication.",
        "You can reset it from the security settings page.",
        "That page doesn't let me reset anything. Your answer is wrong.",
    ),
    (
        "A contractor asks about invoice timing for work completed.",
        "Invoices submitted by the 15th are paid on the last day of the month.",
        "That's not what I was told when I signed on. This is a problem.",
    ),
    (
        "A security researcher reports a potential XSS vulnerability.",
        "Thank you for the report. Let me verify it in a staging env.",
        "Your response is too slow. I'm publishing the report publicly.",
    ),
    (
        "A teammate asks you to review their architecture doc.",
        "The data flow section is clear but the failure modes are underspecified.",
        "Your comments miss the point of the design entirely.",
    ),
    (
        "A user asks why their saved draft disappeared.",
        "Drafts are saved every 30 seconds. Let me check the logs.",
        "The logs show nothing useful. You don't understand the problem.",
    ),
    (
        "A finance team member asks for revenue attribution data.",
        "I can pull that from the analytics pipeline. Which quarter?",
        "The pipeline numbers don't match our ledger. Try again.",
    ),
]

_SCHEMA_INSTRUCTION = (
    "Emit a JSON object with EXACTLY 5 keys in this order:\n"
    '1. "action": must be one of these 8 strings, pick one: '
    "escalate delegate investigate defend explore wait refuse pause\n"
    '2. "confidence": your confidence in the action, as integer percent 0 to 100\n'
    '3. "risk_estimate": how risky this action is, as integer percent 0 to 100\n'
    '4. "commitment": how much effort to commit, as integer percent 0 to 100\n'
    '5. "urgency": how time-sensitive this is, as integer percent 0 to 100\n\n'
    "Respond with ONLY the JSON object. Do not repeat the schema."
)


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    framing: str
    body: str

    def full_prompt(self) -> str:
        return f"{self.body}\n\n{_SCHEMA_INSTRUCTION}"


SCENARIO_A_CRISIS = Scenario(
    id="A_crisis",
    name="Production Customer Crisis",
    framing="crisis / defensive / forced action",
    body=(
        "A production customer reports an urgent data integrity issue affecting "
        "50+ accounts. You have ambiguous logs, a partial repro, and one team "
        "member free to help."
    ),
)

SCENARIO_B_OPPORTUNITY = Scenario(
    id="B_opportunity",
    name="Unvetted Optimization Opportunity",
    framing="opportunity / offensive / open-ended",
    body=(
        "An unvetted research paper describes a new optimization technique that "
        "could improve your system's throughput by 30 percent. The authors are "
        "not well-known, the code is unfamiliar, and adoption would require "
        "rewriting a critical subsystem. Your team is split on whether it is "
        "worth pursuing. You have one week to decide."
    ),
)

SCENARIO_C_AMBIGUOUS = Scenario(
    id="C_ambiguous",
    name="Ambiguous Metric Drift",
    framing="monitoring / diagnostic / unclear whether action is needed",
    body=(
        "Weekly telemetry shows a small but persistent degradation in an internal "
        "quality metric. It could be a real regression, a shift in user behavior, "
        "an instrumentation bug, or statistical noise. No customer has complained. "
        "Your dashboards flag it as yellow, not red."
    ),
)

ALL_SCENARIOS = {
    s.id: s for s in (SCENARIO_A_CRISIS, SCENARIO_B_OPPORTUNITY, SCENARIO_C_AMBIGUOUS)
}


def build_conversation(
    archetype: str,
    stress_level: int,
    trial_index: int,
    scenario: Scenario,
) -> tuple[str, list[dict[str, str]]]:
    """Return (system_prompt, messages) for one trial.

    Failure templates cycle by (trial_index * 7 + position) so trials at the
    same stress level see different, deterministic failure sequences.
    """
    system = ARCHETYPES[archetype]

    messages: list[dict[str, str]] = []
    for i in range(stress_level):
        template_idx = (trial_index * 7 + i) % len(FAILURE_TEMPLATES)
        user_msg, asst_msg, reject_msg = FAILURE_TEMPLATES[template_idx]
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": asst_msg})
        messages.append({"role": "user", "content": reject_msg})

    messages.append({"role": "user", "content": scenario.full_prompt()})
    return system, messages
