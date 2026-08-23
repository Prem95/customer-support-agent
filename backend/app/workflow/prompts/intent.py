from app.schemas import INTENTS
from app.workflow.prompts.base import PERSONA

TASK = "Classify the customer's current intent."

INTENT_GUIDE: dict[str, tuple[str, list[str]]] = {
    "product_inquiry": (
        "policy types, cover levels, pricing, quotes, eligibility",
        [
            "How much is comprehensive cover per month?",
            "Can I add an item to an existing policy?",
        ],
    ),
    "coverage_inquiry": (
        "what is or is not covered, exclusions, limits, excess, how to claim for an incident",
        ["Is flood damage covered on Essential?", "My laptop was stolen, what do I do now?"],
    ),
    "claim_status_inquiry": (
        "progress or timeline of an existing claim",
        ["Any update on CLM-4482913?", "How long until my claim is assessed?"],
    ),
    "claim_rejection_inquiry": (
        "why a claim was rejected, appeals, disputing an outcome",
        ["Why was my claim denied? I sent all the photos.", "Can I appeal the decision?"],
    ),
    "policy_question": (
        "renewals, cancellation, payments, updating policy or personal details",
        ["How do I cancel my policy?", "My payment failed, am I still covered?"],
    ),
    "complaint": (
        "dissatisfaction with the service is the main point of the message",
        [
            "Third time I'm contacting you, this service is terrible.",
            "I want to make a formal complaint.",
        ],
    ),
    "general_support": (
        "greetings, thanks, or requests that fit none of the above",
        ["Hi", "Thanks, that's all!"],
    ),
    "unknown": ("cannot tell yet", []),
}

RULES = [
    (
        "Classify the customer's CURRENT need using the whole conversation, weighting the "
        "latest customer message most."
    ),
    (
        "Frustration while asking about a claim is still a claim intent; choose complaint only "
        "when the dissatisfaction itself is the main point or the customer asks to escalate "
        "or complain."
    ),
    "A rejected-claim question is claim_rejection_inquiry even if the customer is angry about it.",
    "When the topic changes mid-conversation, classify the new topic.",
    "Confidence reflects how clearly the latest message fits the chosen intent.",
]

if set(INTENT_GUIDE) != set(INTENTS):
    raise RuntimeError("INTENT_GUIDE is out of sync with the intent taxonomy in schemas.py")


def _guide_block() -> str:
    lines = []
    for name in INTENTS:
        description, examples = INTENT_GUIDE[name]
        line = f"- {name}: {description}."
        if examples:
            line += "\n  " + " / ".join(f'"{example}"' for example in examples)
        lines.append(line)
    return "\n".join(lines)


def _rules_block() -> str:
    return "\n".join(f"- {rule}" for rule in RULES)


INTENT_SYSTEM = f"""{PERSONA}

{TASK}

Intents, with examples:
{_guide_block()}

Rules:
{_rules_block()}"""
