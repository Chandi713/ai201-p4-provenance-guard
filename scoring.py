"""
Turning two numbers into one, and one number into something a person can read.
← YOU BUILD THIS IN MILESTONES 4 AND 5

Two functions live here, and both are stubs.

`combine_signals` is where your false-positive decision from Milestone 1
actually gets made. Everything above it — the labels, the appeal path — is
downstream of a number this function produced.

`score_to_label` is where you stop writing for a machine and start writing for
a person. A score of 0.62 means nothing to a writer.

⚠️ Your README's **Signals and Scoring** section has to name the file and
function holding your combining rule. The grader checks your code against what
you claim, so that line should read `scoring.py::combine_signals`.
"""

import config


def combine_signals(model_score: float, style_score: float) -> float:
    """
    Combine two 0–1 signals into one 0–1 score. ← TODO (Milestone 4)

    Both inputs point the same way: higher means more likely AI. Your output
    should too.

    Args:
        model_score: from `detector.model_signal` — how predictable the text is.
        style_score: from `stylometry.style_signal` — the shape of the text.

    Returns:
        A float from 0.0 (confidently human) to 1.0 (confidently AI).

    ⚠️ **Write the rule down before you code it, and put the numbers in your
    README.** A weighted average is the obvious choice and it is not the only
    one. Things worth thinking about:

      - **What happens when they disagree?** One signal at 0.9 and the other at
        0.1 averages to 0.5 — "unsure". Is that what you want? It might be
        exactly right: two methods disagreeing IS uncertainty. Or you might
        decide one signal is more trustworthy when they split.

      - **Which way do you want to be wrong?** Weighting toward the signal that
        reads more human means fewer false accusations and more AI text
        getting through. There's no weighting that avoids the trade.

      - Milestone 4 asks you to find a case where your two signals split and
        write it down. That case is what this rule exists to handle.

    ─────────────────────────────────────────────────────────────────────────
    My rule. Each signal is first placed in its own band — human (≤ 0.53),
    unsure, AI (≥ 0.77) — and the pair of bands decides:

      1–3  Same band                 the higher score.
      4, 6 Neighbouring bands, gap   model_score — perplexity reads the text,
           ≤ DISAGREEMENT_GAP        so it settles small splits.
      5    Human + unsure, wider     the human score. One confident signal is
                                     enough to clear a writer.
      7    Unsure + AI, wider        the AI score only if ≥ STRONG_AI_BAR,
                                     else the unsure score.
      8    Human + AI                each side's distance past its own line,
                                     as a fraction of that line:
                                       (0.53 − h) / 0.53  vs  (a − 0.77) / 0.77
                                     The larger wins; an exact tie is 0.65.
                                     The AI side tops out near 0.30, so a
                                     human score under ~0.37 always wins.

    The returned score always sits inside the band of the label it earns, so
    `score_to_label` agrees with the rule and the README's ranges stay true.
    """
    model_band = _band(model_score)
    style_band = _band(style_score)

    if model_band == style_band:
        return max(model_score, style_score)

    by_band = {model_band: model_score, style_band: style_score}

    if "human" in by_band and "ai" in by_band:
        h, a = by_band["human"], by_band["ai"]
        human_margin = (config.HUMAN_THRESHOLD - h) / config.HUMAN_THRESHOLD
        ai_margin = (a - config.AI_THRESHOLD) / config.AI_THRESHOLD
        if human_margin > ai_margin:
            return h
        if ai_margin > human_margin:
            return a
        return round((config.HUMAN_THRESHOLD + config.AI_THRESHOLD) / 2, 4)

    # Neighbouring bands: one side is unsure.
    if round(abs(model_score - style_score), 4) <= config.DISAGREEMENT_GAP:
        return model_score

    if "human" in by_band:
        return by_band["human"]

    a = by_band["ai"]
    return a if a >= config.STRONG_AI_BAR else by_band["unsure"]


def _band(score: float) -> str:
    """Which label a single score would earn on its own. Same edges as score_to_label."""
    if score >= config.AI_THRESHOLD:
        return "ai"
    if score <= config.HUMAN_THRESHOLD:
        return "human"
    return "unsure"


def score_to_label(score: float) -> tuple[str, str]:
    """
    Turn a score into a guess and the text a reader actually sees.
    ← TODO (Milestone 5)

    Returns:
        (guess, label_text) — where `guess` is a short machine-readable string
        like "ai" / "human" / "unsure", and `label_text` is the full sentence
        shown to a person.

    ⚠️ Write the label text for someone who has never heard the word
    "threshold".

        ✗ "human, 0.81 confidence"
        ✓ "We think this was probably written by a person."

    All three labels have to be **reachable**. If no score can produce one of
    them, your ranges have a gap — and Milestone 5 asks you to submit text that
    produces each one, which is how you'd find out.

    The hardest one to write is "unsure". It has to admit uncertainty without
    sounding like an accusation, because the person reading it may well have
    written every word themselves. Your breakout asks your group what they'd
    think if they got it on their own work. That question is the whole
    milestone.
    """
    if score >= config.AI_THRESHOLD:
        return "ai", (
            "Our checks found patterns often seen in AI-generated writing, such "
            "as very predictable word choices and evenly sized sentences. This "
            "doesn't prove it wasn't written by you. If you wrote it yourself, "
            "you can ask for a review."
        )
    if score <= config.HUMAN_THRESHOLD:
        return "human", "Our checks suggest this was written by a person."
    return "unsure", (
        "We can't tell with confidence whether this was written by a person or "
        "with AI, so we haven't labelled it either way."
    )


def label_ranges() -> list[tuple[str, str]]:
    """
    The score range each label covers. Your README needs these beside the
    label text — given to you so the numbers can't drift apart from config.py.
    """
    return [
        ("high-confidence human", f"0.00 – {config.HUMAN_THRESHOLD:.2f}"),
        ("unsure", f"{config.HUMAN_THRESHOLD:.2f} – {config.AI_THRESHOLD:.2f}"),
        ("high-confidence AI", f"{config.AI_THRESHOLD:.2f} – 1.00"),
    ]
