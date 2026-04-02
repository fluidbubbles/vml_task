import random

BROWSER_PROFILES = [
    "chrome120",
    "chrome124",
    "safari17_0",
    "firefox120",
    "chrome116",
]


def get_random_browser() -> str:
    return random.choice(BROWSER_PROFILES)


def get_browser_by_index(index: int) -> str:
    return BROWSER_PROFILES[index % len(BROWSER_PROFILES)]
