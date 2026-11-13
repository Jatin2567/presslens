"""Deterministic fictional publisher sessions. These are not publisher records."""

from datetime import date, timedelta
from random import Random

CATEGORIES = ("Markets", "Economy", "Technology", "Personal Finance", "Business", "Policy")
CHANNELS = ("Search", "Direct", "Social", "Newsletter", "Referral")
DEVICES = ("Desktop", "Mobile", "Tablet")
START_DATE = date(2026, 8, 1)
END_DATE = date(2026, 10, 29)
SESSION_FIELDS = (
    "session_id", "date", "article_id", "channel", "device", "engaged_seconds",
    "scroll_depth", "engaged", "newsletter_signup", "subscribed",
)
ARTICLE_FIELDS = ("article_id", "title", "category")


def articles() -> list[dict]:
    topics = {
        "Markets": ["Reading a market rally", "What moves bond yields", "Earnings season explained", "The long view on volatility"],
        "Economy": ["The inflation basket", "Understanding growth indicators", "Inside a rate decision", "What exports tell us"],
        "Technology": ["AI in the workplace", "The economics of cloud computing", "Building digital infrastructure", "How chips reach the market"],
        "Personal Finance": ["A guide to emergency funds", "Understanding investment fees", "Planning a monthly budget", "The basics of diversification"],
        "Business": ["Following a company's cash flow", "How small businesses grow", "A closer look at supply chains", "Understanding unit economics"],
        "Policy": ["Reading the budget", "How trade rules work", "The infrastructure investment cycle", "Making sense of regulation"],
    }
    return [
        {"article_id": f"A{i:03d}", "title": f"{title} — a simulated briefing", "category": category}
        for i, (category, title) in enumerate(
            ((category, title) for category in CATEGORIES for title in topics[category]), 1
        )
    ]


def generate_sessions(count: int = 6000, seed: int = 42, *, include_defects: bool = True) -> list[dict]:
    if count < 1 or count > 1_000_000:
        raise ValueError("Session count must be between 1 and 1,000,000.")
    random = Random(seed)
    catalog = articles()
    result = []
    days = (END_DATE - START_DATE).days + 1
    for index in range(count):
        article = random.choice(catalog)
        channel = random.choices(CHANNELS, weights=[33, 24, 21, 15, 7], k=1)[0]
        device = random.choices(DEVICES, weights=[32, 63, 5], k=1)[0]
        # Deliberately encoded demo patterns, not discoveries about real readers.
        attention = {"Search": 75, "Direct": 110, "Social": 35, "Newsletter": 160, "Referral": 85}[channel]
        seconds = min(1800, max(0, round(random.expovariate(1 / attention))))
        scroll = min(100, max(0, round(seconds / 2.2 + random.gauss(12, 20))))
        engaged = int(seconds >= 30 and scroll >= 50)
        signup = int(bool(engaged) and random.random() < (0.16 if channel == "Newsletter" else 0.07))
        probability = 0.075 if channel == "Newsletter" else 0.032
        if article["category"] == "Personal Finance":
            probability += 0.015
        subscribed = int(bool(engaged) and random.random() < probability)
        result.append({
            "session_id": f"S{index + 1:07d}",
            "date": (START_DATE + timedelta(days=random.randrange(days))).isoformat(),
            "article_id": article["article_id"], "channel": channel, "device": device,
            "engaged_seconds": seconds, "scroll_depth": scroll, "engaged": engaged,
            "newsletter_signup": signup, "subscribed": subscribed,
        })
    if include_defects:
        # Add known defects without changing the 6,000 accepted-session population.
        result.extend(dict(row) for row in result[: min(30, count)])
        for suffix, changes in enumerate([
            {"date": "2026-02-30"}, {"article_id": "UNKNOWN"},
            {"engaged_seconds": -1}, {"scroll_depth": 101},
            {"engaged": 0, "subscribed": 1},
        ], 1):
            result.append({**result[0], "session_id": f"INVALID{suffix}", **changes})
    return result
