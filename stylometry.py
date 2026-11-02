"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics

# Each measure is mapped linearly onto 0–1 (1 = AI-like) between these
# cut-offs, clamped outside. Set from a 12-paragraph development set (6 AI,
# 6 human incl. plain writing), kept apart from the criteria test set:
#
#                        AI mean   human mean
#   spread                0.23       0.51      separates
#   avg word length       6.1        3.8       separates, no overlap
#   punctuation variety   0.00       0.03      ~always 0 at paragraph length
#   type-token ratio      0.88       0.72      points the WRONG way: plain
#                                              writers repeat words
SPREAD_AI, SPREAD_HUMAN = 0.15, 0.45      # stdev/mean of sentence length
WORDLEN_HUMAN, WORDLEN_AI = 4.0, 6.0      # average letters per word
PUNCT_HUMAN = 0.5                         # varied marks per sentence -> 0.0

# Averaging in a measure that doesn't separate AI from human drags every score
# toward 0.5 — my first version did exactly that and scored clearly-AI 0.49,
# clearly-human 0.46. So only the measures that separate carry real weight.
# Type-token ratio is still computed and printed, but weighted 0.
WEIGHT_SPREAD = 0.4
WEIGHT_WORDLEN = 0.4
WEIGHT_PUNCT = 0.2

# Semicolons, colons, brackets, ! and ?, em/en dashes, and a spaced or doubled
# hyphen. A hyphen inside a word ("well-known") is not punctuation variety.
_VARIED_PUNCT = re.compile(r"[;:!?()—–]|--|\s-\s")


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

def sentence_length_spread(text: str) -> float | None:
    """
    How much sentence length varies: stdev / mean of words per sentence.

    Returns:
        0.0 upward. Higher means lumpier sentences, which is more human.
        None when there are fewer than two sentences — one sentence has no
        spread to measure, and calling that "0.0, perfectly even" would read a
        single long sentence as machine-like. `style_signal` treats None as
        neutral.
    """
    lengths = [len(words(s)) for s in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return None
    return statistics.stdev(lengths) / statistics.mean(lengths)


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words.

    Returns:
        A float between 0 and 1. Higher means more varied vocabulary, which is
        more human.

    Known weakness: this falls as text gets longer, because common words
    repeat. A long human essay can score lower than a short AI paragraph.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def punctuation_density(text: str) -> float:
    """
    Varied punctuation marks per sentence.

    Counts semicolons, colons, brackets, ! and ?, and dashes — not commas or
    full stops, which every writer uses. Generated prose leans on commas and
    full stops; people reach for the rest unevenly.

    Returns:
        0.0 upward. Higher means more varied punctuation, which is more human.
    """
    count = len(sentences(text))
    if count == 0:
        return 0.0
    return len(_VARIED_PUNCT.findall(text)) / count


def average_word_length(text: str) -> float:
    """
    Average letters per word.

    Returns:
        0.0 upward. Higher means longer words, which is more AI-like: generated
        prose reaches for "enhance", "significantly", "stakeholders".

    Blind spot: formal or academic human writing uses long words too and
    reads as AI here. Signal one tends to read that same prose as human, so
    the two cover for each other.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    return sum(len(w) for w in tokens) / len(tokens)


def _clamp(value: float) -> float:
    return min(max(value, 0.0), 1.0)


# ── Combining them ───────────────────────────────────────────────────────────

def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.** ← TODO

    Combine your three measures into one number. Same direction as
    `detector.model_signal`, so that `scoring.combine_signals` can treat them
    the same way — if one of your signals runs backwards, everything above it
    is wrong in a way that's hard to see.

    Two things to decide and write down:

      1. Which direction each measure points. Low spread means more AI-ish, so
         it needs flipping. Work out which of your three need that.
      2. How to get each onto a comparable scale. A raw type-token ratio sits
         between 0 and 1; a raw punctuation count doesn't. Adding them
         unscaled means whichever has the bigger numbers wins by default.

    Test it on the four calibration inputs from Milestone 4 — clearly AI,
    clearly human, plain conventional human writing, lightly-edited AI — before
    you trust it. Plain and ordinary, not formal: formal prose reads as *human*
    to signal one, and it is plain writing that gets accused.

    My rule: each measure is mapped onto 0–1 (1 = AI-like) between the
    cut-offs at the top of this file — low spread, long words and no varied
    punctuation all count as AI-like — then weighted 0.4 / 0.4 / 0.2. A
    single-sentence text has no spread, so that measure counts as a neutral
    0.5 rather than as evidence either way.
    """
    spread = sentence_length_spread(text)
    spread_ai = 0.5 if spread is None else 1.0 - _clamp(
        (spread - SPREAD_AI) / (SPREAD_HUMAN - SPREAD_AI)
    )
    wordlen_ai = _clamp(
        (average_word_length(text) - WORDLEN_HUMAN) / (WORDLEN_AI - WORDLEN_HUMAN)
    )
    punct_ai = 1.0 - _clamp(punctuation_density(text) / PUNCT_HUMAN)

    score = (
        WEIGHT_SPREAD * spread_ai
        + WEIGHT_WORDLEN * wordlen_ai
        + WEIGHT_PUNCT * punct_ai
    )
    return round(score, 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}   (shown, weighted 0)")
    print(f"average_word_length      {average_word_length(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
