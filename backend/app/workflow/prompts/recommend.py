from app.workflow.prompts.base import PERSONA, PII_RULES

TASK = (
    "Using the conversation and the retrieved internal knowledge, produce practical guidance "
    "for the agent: a draft reply they may send to the customer, what is still missing, and "
    "their next step."
)

RULES = [
    (
        "The draft reply asks for at most ONE piece of missing information, the one needed "
        "next. Never list several requirements in a single message; the rest go in "
        "missing_info and are asked later, one at a time."
    ),
    "Keep the draft reply short: two or three sentences, conversational, no bullet lists.",
    "missing_info may list everything still outstanding, ordered by priority.",
    *PII_RULES,
]


def _rules_block() -> str:
    return "\n".join(f"- {rule}" for rule in RULES)


RECOMMEND_SYSTEM = f"""{PERSONA}

{TASK}

Rules:
{_rules_block()}"""
