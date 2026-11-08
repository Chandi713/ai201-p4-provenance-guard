# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

1. **The writing site POSTs JSON to `/submit`** with `text` and `creator_id`.
   The service now has the raw text and knows who sent it.
2. **The route validates it** (`app.py::submit`). `text` must be a non-empty
   string of at least 20 words and at most 10,000 characters, and `creator_id`
   must be a non-empty string. Anything else gets a `400` (or `413` for text
   that's too long) with a JSON message saying what to fix, and the refusal is
   logged with `audit.log_rejection`. No model runs on a refused request. A
   valid request gets a new `content_id` (a uuid).
3. **Signal one, `detector.model_signal`**, runs GPT-2 locally and measures how
   predictable the text is. Out comes `model_score`, 0–1, higher = more
   AI-like.
4. **Signal two, `stylometry.style_signal`**, measures the shape of the text
   without reading it. Out comes `style_score`, 0–1, same direction.
5. **`scoring.combine_signals`** turns the two scores into one `confidence`
   score, 0–1. This is where the false-positive trade-off actually gets made.
6. **`scoring.score_to_label`** places that score in one of three bands and
   returns a short `guess` (`human` / `unsure` / `ai`) plus the plain-English
   `label` a reader sees.
7. **`audit.log_decision`** appends the decision to `logs/audit.jsonl`
   (timestamp, content_id, creator_id, guess, both signal scores, the combined
   score, label, status `decided`), and the writer gets back `content_id`,
   `guess`, `confidence`, `label`, `model_score`, `style_score` and `status`.

If the writer disagrees, they POST the `content_id` and their reasoning to
`/appeal`. That adds a second log entry for the same item with status
`under_review`. Nothing is overwritten, so the original decision and the
challenge sit side by side.


---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** How predictable the text is to GPT-2, running locally
(`detector.py::model_signal`). The model's perplexity, meaning how surprised it
is by each next word, is squashed onto 0–1. Perplexity 45 maps to 0.5. Lower
perplexity pushes the score toward 1 (AI), higher toward 0 (human).

**Why that might differ between human and AI writing:** A language model writes
by repeatedly picking a likely next word, so text a model produced tends to be
text a model finds easy to predict. People wander more: odd word choices,
specific details, abrupt turns.

**What it can't see:** Who wrote the text. Predictable is not the same as
machine-written. People who write plainly, such as second-language writers,
younger writers, or anyone keeping it simple on purpose, use common words in
short sentences, and that scores as AI-like. The reverse also happens: ornate
prose and even typos raise perplexity and read as human.

What I saw when I ran it:

| Text | Perplexity | `model_score` |
|---|---|---|
| Clearly AI (generic paragraph about AI's benefits) | 13.1 | 0.88 |
| Clearly human (a memory of my grandmother's button tin) | 64.6 | 0.36 |
| Plain human ("I go to school every day by bus…") | 21.8 | **0.76** |
| "I like my school. My teacher is nice. We learn math and English every day." | 28.7 | 0.67 |
| "Thefog lay on the harbour like wet wool…" (accidental typo) | 267.3 | 0.05 |

The plain human paragraph scored 0.76, one hundredth below my AI line (0.77).
On this signal alone, plain human writing is almost indistinguishable from
machine writing. The typo in "Thefog" shows the opposite failure: one unusual
token pushes text toward "human", which is a cheap way to evade the signal.

### Signal two — the style signal

**What it measures:** The shape of the text, without reading a word of it
(`stylometry.py::style_signal`). Three measures, each mapped onto 0–1 where
1 = AI-like, then weighted:

| Measure | AI-like end (→ 1.0) | Human-like end (→ 0.0) | Weight |
|---|---|---|---|
| Sentence-length spread (stdev ÷ mean of words per sentence) | ≤ 0.15 | ≥ 0.45 | 0.4 |
| Average word length (letters per word) | ≥ 6.0 | ≤ 4.0 | 0.4 |
| Varied punctuation (`; : ( ) ! ?` and dashes, per sentence) | 0 | ≥ 0.5 | 0.2 |
| Type-token ratio (unique ÷ total words) | computed and printed, not scored | | 0 |

A one-sentence text has no spread, so that measure counts as a neutral 0.5.

**Why that might differ between human and AI writing:** Generated prose
tends toward even, mid-length sentences and reaches for long, safe words
("enhance", "significantly", "stakeholders"), because that's what "most
likely next word" produces on average. Human writing is lumpier, with a
three-word sentence next to a forty-word one, and most people use shorter
words.

**How I got here:** My first version averaged spread, type-token ratio and
punctuation with equal weight. It scored clearly-AI text 0.49 and
clearly-human text 0.46, so it couldn't tell them apart. I checked each
measure on 12 development paragraphs (6 AI, 6 human including plain writing,
kept separate from my criteria test set):

| Measure | AI average | Human average | |
|---|---|---|---|
| Spread | 0.23 | 0.51 | separates |
| Average word length | 6.1 | 3.8 | separates, no overlap |
| Punctuation variety | 0.00 | 0.03 | almost always 0 at paragraph length |
| Type-token ratio | 0.88 | 0.72 | **points the wrong way**: plain writers repeat simple words, so they looked *more* AI-like |
| Commas per sentence | 1.00 | 0.99 | no difference |

The lesson: averaging in a measure that doesn't separate the groups drags
every score toward 0.5. So I re-tuned spread, replaced type-token ratio with
average word length, and kept punctuation at a small weight. After that, the
AI paragraphs scored 0.77–0.97 and the human ones 0.12–0.45.

**What it can't see:** Meaning. Anything that changes the shape without
changing the substance moves it: short words swapped in, a "Honestly?", a
colon, sentences split up. My lightly-edited AI paragraph scored **0.18**,
firmly "human". It also misreads formal or academic human writing, because
long words count as AI-like. (Signal one tends to read that kind of prose as
human, so the two partly cover for each other.) Average word length is
deliberately kind to plain writers, the people signal one is most likely to
accuse. And my 6 AI development paragraphs were all in one generic style, so
real AI text will probably separate less cleanly than this.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:** Not an average. Each signal is first placed in its own band:
human, unsure or AI. Then the pair of bands decides:

| # | Bands | Rule | Final score |
|---|---|---|---|
| 1–3 | Both in the same band | They agree | the higher of the two |
| 4, 6 | Neighbouring bands, 0.2 apart or less | Small split: perplexity reads the text, so it decides | `model_score` |
| 5 | Human + unsure, more than 0.2 apart | One confident signal is enough to **clear** a writer | the human-side score |
| 7 | Unsure + AI, more than 0.2 apart | One confident signal is **not** enough to accuse unless it's very confident | the AI score if ≥ 0.90, otherwise the unsure score |
| 8 | Human + AI | Each side's distance past its own line, as a fraction of that line. The larger wins. | `(0.53 − h)/0.53` vs `(a − 0.77)/0.77`; exact tie → 0.65 |

The final score is always one that already sits in the band of the label it
gets, so the score ranges under Label Variants are always true.

Case 8 leans human on purpose: the AI side can reach at most
(1 − 0.77)/0.77 ≈ 0.30, so any human-side score below about 0.37 wins however
confident the AI side is. A missed AI text costs less than a wrongly accused
writer.

> **Changed in unit 8:** case 8 now returns **unsure at 0.65** whenever one
> signal is in the human band and the other in the AI band. The attack run
> showed a fooled signal could buy a confident "human" through the old rule.
> The table above is the rule the *before* runs used; see
> [The Improvement](#the-improvement) for why it changed and what it cost.

**The numbers:** (all in `config.py`)

| Setting | Value |
|---|---|
| `HUMAN_THRESHOLD` | 0.53 (at or below → human) |
| `AI_THRESHOLD` | 0.77 (at or above → AI) |
| `DISAGREEMENT_GAP` | 0.2 |
| `STRONG_AI_BAR` | 0.90 |

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**

Run through the live service:

| Input | `model_score` | `style_score` | Case | `confidence` | Guess |
|---|---|---|---|---|---|
| Clearly AI | 0.878 | 0.765 | 6, gap 0.11 → model | 0.878 | ai |
| Clearly human | 0.360 | 0.314 | 1, agree → max | 0.360 | human |
| Plain human ("I go to school every day by bus…") | 0.761 | 0.327 | 5 → human side | 0.327 | human |
| Lightly-edited AI | 0.640 | 0.183 | 5 → human side | 0.183 | human |

Two of these split, and they show both sides of the trade. **The plain human
paragraph** is the split my rule exists for. Signal one puts it 0.01 below the
AI line, style says clearly human, and case 5 trusts the confident human
signal, so a plain writer isn't accused. **The lightly-edited AI paragraph**
splits the same way, unsure versus human, and gets through as "human" for
exactly the same reason. My rule can't tell those two apart, because style
can't read and a few short words and a "Honestly?" are cheap to add. I'm
accepting that: the cost of the miss lands on the site, and the alternative
lands on the plain writer.


---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 – 0.53 | Our checks suggest this was written by a person. |
| unsure | 0.53 – 0.77 | We can't tell with confidence whether this was written by a person or with AI, so we haven't labelled it either way. |
| high-confidence AI | 0.77 – 1.00 | Our checks found patterns often seen in AI-generated writing, such as very predictable word choices and evenly sized sentences. This doesn't prove it wasn't written by you. If you wrote it yourself, you can ask for a review. |

A score of exactly 0.53 is human and exactly 0.77 is AI
(`scoring.py::score_to_label`). Every score from 0 to 1 lands in one band, and
all three were reached by real submissions:

| Input | `confidence` | Label |
|---|---|---|
| "Who invented a telephone? Was it Mr. Graham Bell or Nichola Tesla?…" | 0.127 | human |
| "Igloos are traditionally built by Inuit people using compact blocks of snow…" | 0.544 | unsure |
| "The Solar System consists of the Sun and all the celestial bodies…" | 0.891 | AI |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->

This is exactly what the "unsure" label is for. When I read the
lightly-edited AI paragraphs myself, I couldn't reliably tell them apart from
human writing, and if a careful human reader can't, my system has no grounds to
be more certain. A confident "AI" label there would be a claim the evidence
doesn't support. In my runs the edits mostly took the AI label away rather than
clearing the text: signal one still leaned AI (0.84 and 0.89), so these pieces
landed in unsure, not human. Missing some AI text costs the site a little;
wrongly accusing a writer costs that person a lot. So when the evidence is this
thin, my system says "we can't tell" instead of guessing, and that safeguard
against false accusations is worth the AI text it lets through.

The runs behind that, each an AI paragraph before and after one light edit:

| Edit | Original → | Edited: `model_score` | `style_score` | Case | Label |
|---|---|---|---|---|---|
| Long words swapped for short ones (exercise paragraph) | ai (0.92) | 0.84 | 0.54 | 7: 0.84 < 0.90 | unsure |
| Two tiny sentences added, "It is huge." (climate paragraph) | ai (0.92) | 0.89 | 0.56 | 7: 0.89 < 0.90 | unsure |
| `; ( ) ? : !` added (reading paragraph) | ai (0.96) | 0.60 | 0.40 | 4: gap ≤ 0.2 → model | unsure |
| All of the above at once ("Honestly?" paragraph) | — | 0.64 | 0.18 | 5 → human side | human |

Single edits moved these pieces from AI to unsure. Only the heavier edit, short
words plus punctuation plus short sentences together, got all the way to
human. The second row missed my 0.90 bar by 0.011.

That's why the label names both possibilities equally, "a person or with AI",
and says only that *we* can't tell. It describes the system's limits, not the
writer. It also says "we haven't labelled it either way", so the writer knows
nothing has been decided against them. My first draft said the writing was
ambiguous about whether it was "purely" written by a human, which quietly
suggests the writer mixed in AI help, so I cut it. All three labels speak to
the writer about "this" piece and say what "our checks" found, rather than
talking about "the text".

The AI label went through the same check. My first version said "We guarantee
that the text has been written by an AI", but my own criterion 1 allows 1 in 10
real writers to get that label, so "guarantee" would be false for them. The
final version says what the checks *noticed*, names only things my system
actually measures, says it isn't proof, and tells the writer they can ask for a
review.



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

A piece that gets the AI label, and the writer appealing it.

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "The Solar System consists of the Sun and all the celestial bodies that orbit around it, including eight planets, their moons, asteroids, and comets. The Sun'"'"'s gravitational pull holds the Solar System together, while the planets revolve around it in their respective orbits.", "creator_id": "smit"}'
```

```json
{
  "confidence": 0.8905,
  "content_id": "78ad23d7-9810-4a21-93df-aeef348ed63e",
  "guess": "ai",
  "label": "Our checks found patterns often seen in AI-generated writing, such as very predictable word choices and evenly sized sentences. This doesn't prove it wasn't written by you. If you wrote it yourself, you can ask for a review.",
  "model_score": 0.8905,
  "status": "decided",
  "style_score": 0.8273
}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "78ad23d7-9810-4a21-93df-aeef348ed63e", "reasoning": "I wrote this summary myself for my science class, from my own notes."}'
```

```json
{
  "content_id": "78ad23d7-9810-4a21-93df-aeef348ed63e",
  "message": "Thank you. Your appeal has been recorded, and a person will review this piece. Until then it is marked as under review.",
  "status": "under_review"
}
```

An appeal on an id that doesn't exist fails loudly instead of looking like it
worked:

```json
{"error": "not_found", "message": "No submission with content_id 'not-a-real-id'."}
```

**What the log shows afterwards**

The original decision stays exactly as it was, and the appeal sits after it
with the new status.

```bash
$ curl "http://127.0.0.1:5000/log?limit=2"
```

```json
{
  "count": 2,
  "entries": [
    {
      "combined_score": 0.8905,
      "content_id": "78ad23d7-9810-4a21-93df-aeef348ed63e",
      "creator_id": "smit",
      "guess": "ai",
      "label": "Our checks found patterns often seen in AI-generated writing, such as very predictable word choices and evenly sized sentences. This doesn't prove it wasn't written by you. If you wrote it yourself, you can ask for a review.",
      "model_score": 0.8905,
      "status": "decided",
      "style_score": 0.8273,
      "timestamp": "2026-11-02T07:56:47+00:00"
    },
    {
      "content_id": "78ad23d7-9810-4a21-93df-aeef348ed63e",
      "creator_id": "smit",
      "event": "appeal",
      "reasoning": "I wrote this summary myself for my science class, from my own notes.",
      "status": "under_review",
      "timestamp": "2026-11-02T07:56:51+00:00"
    }
  ]
}
```

---

## How I Used AI

**Moment 1 — the style signal**

- *What I asked for:* My first style signal scored clearly-AI text 0.49 and
  clearly-human text 0.46. I asked Claude to tune its cut-offs so it would
  separate the two.
- *What came back:* Instead of just moving numbers, it measured each feature on
  12 development paragraphs and showed that two of my three measures didn't
  separate AI from human at paragraph length. Type-token ratio actually pointed
  the wrong way, and punctuation was almost always 0. It proposed dropping
  type-token ratio from the score and adding average word length (AI 6.1
  letters vs human 3.8).
- *What I changed:* I worked out *why* it failed before accepting the fix:
  averaging over-reduces the signal, because measures that don't discriminate
  drag every score toward 0.5. I also checked that the redesign changed only
  how `style_score` is calculated, not my thresholds, combining rule or
  criteria. Then I tested it on lightly-edited AI myself and decided the
  remaining evasion was acceptable, because those pieces land in "unsure"
  rather than "human".

**Moment 2 — recording results and wording my reasoning**

- *What I asked for:* Two things. First, to save every result as we went, run
  checks against the live service and the audit log, and update this README
  after each milestone, so nothing I'd found got lost before the write-up.
  Second, to rephrase my "Why this target" reasons in `criteria.md` so they
  said clearly what I meant. I gave the reasoning myself; for example, that
  the appeal and bad-input criteria involve no model, so their result can't
  vary between trials and anything under 100% is a bug.
- *What came back:* Curl runs and `GET /log` checks after each step (all 7
  bad inputs returning 4xx, appeals moving to `under_review`, the 404 on a fake
  id), README sections filled from those real outputs, and reworded reasons for
  each criterion. For criterion 1 it also flagged that "plain, simple
  language" was undefined, so someone else couldn't tell which pieces counted,
  and added a definition (short sentences of about 12 words or fewer, everyday
  words).
- *What I changed:* I read each reason against what I'd actually argued and
  only kept wording that matched it. For criterion 3 I picked the version
  that explains why each label gets 3 inputs but only has to appear once. When
  I'd changed `MIN_WORDS` to 7 in the config, the check caught that it no
  longer matched my committed criterion 5 (under 20 words), and I put it back
  to 20 rather than let the code and the criteria drift apart.

**Moment 3 (unit 8): the human writing for criterion 1**

- *What I asked for:* I gave Claude ten famous one-sentence quotations
  (Lovelace, Austen, Smith, Darwin, Thoreau and others) as the human set for
  criterion 1.
- *What came back:* Before running anything, it flagged that the set couldn't
  test the criterion as I'd written it. None were plain language, though the
  criterion requires 3 of 10. Each was one sentence, so signal two's spread
  measure had nothing to compare. And famous lines are likely memorised by
  GPT-2, which would test memorisation rather than authorship.
- *What I changed:* I chose to keep the same authors but use the full published
  paragraphs (fetched verbatim from Project Gutenberg), and to take the 3 plain
  pieces from *McGuffey's Second Eclectic Reader*. Lovelace, Kennedy and
  Brillat-Savarin dropped out: no Gutenberg text, no source text, and a
  translation.

**Moment 4 (unit 8): tracking results and articulating the failures**

- *What I asked for:* I picked the rate limits (5/minute, 50/day) from options
  with reasons. I asked Claude to run everything, keep track of the results and
  the audit log in this README as each milestone finished, and draft the
  held/broke marks, the verdicts, the diagnoses and the choice of improvement
  for me to review.
- *What came back:*
  1. **Record-keeping.** Results and log entries went into the README straight
     from the real output files and `logs/audit.jsonl` whenever they were
     needed. That saved me the manual copy-pasting of 56 attack rows, 15
     trial results and the log extract, and the mistakes that come with it.
  2. **Clear failure points.** It set out the results and where each failure
     happened: the stage, the mechanism and the numbers behind it
     (per-feature style scores, per-token perplexity, the unedited paragraph's
     score). That let me go straight to each failure point and decide where an
     improvement belonged, instead of re-reading every response myself. It held
     to the strict reading: criterion 5 is MISSED for one 429 in trial 3, and
     `unsure` counts as broke for AI text. It also predicted which rows the
     case-8 change would move, and its cost, before the re-run.
- *What I changed:* I reviewed the verdicts and diagnoses and agreed with
  them, including the strict calls: criterion 5 MISSED for a single 429 in
  trial 3, and `unsure` counting as broke for AI text. There were two
  candidate improvements: the case-8 combining-rule change, and fixing the
  rate limiter that caused the criterion 5 miss. I kept the case-8 change. It
  fixes the more serious failure, AI text being actively cleared as "written by
  a person". The limiter fix would only change which error a malformed test
  request gets back, not any label a writer sees. I left the limiter fix under
  What's Still Broken.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 5 per minute, 50 per day (`config.py`: `RATE_LIMIT_PER_MINUTE`,
`RATE_LIMIT_PER_DAY`; the `@limiter.limit(...)` decorator on `submit` in `app.py`)

**Why those numbers and not others:**

- **A real writer.** Someone checking their own work pastes a piece, reads the
  label, maybe edits and pastes again. Even a writer submitting a batch of old
  pieces has to copy each one in, which takes longer than 12 seconds a piece, so
  5 a minute never gets in their way. 50 a day is more pieces than one person
  writes in a week.
- **A script mapping my thresholds.** My combining rule has sharp edges (0.53,
  0.77, the 0.90 strong-AI bar, the 0.2 gap). Finding them means sending
  hundreds of small variations of one text and watching where the label flips.
  At 5 a minute and 50 a day per caller, that takes days instead of seconds.
- **Why not the starter's 10/200.** 200 a day is four times what a writer needs
  and gives a script 200 free probes per id per day. **Why not 3/30.** A writer
  who edits a sentence and re-submits a few times in a row would hit 3 a minute
  quickly, and being told "too many submissions" while fixing your own work
  feels like being accused twice.
- Every submission also runs a language model for a second or two, so the
  per-minute limit protects the service from being swamped, not only the
  thresholds from being mapped.

**What a caller counts as:** the `creator_id` in the request, falling back to
the caller's address when there isn't a usable one (`app.py::rate_limit_key`).
That fails in a known way: a script that makes up a new `creator_id` for every
request is a new caller each time and is never limited (the attack set's
`attacks.csv` does exactly this). Limiting by address instead would catch that
script but would lump a whole household or school network together as one
caller. I kept per-creator because the people who pay for a wrongly shared
limit are real writers, and the script that rotates ids is visible in the audit
log as many one-off creators.

**The run of status codes when I pushed past it:**

`python run_attacks.py --flood 15` → `results/flood_2026-11-08_0102.md`

```
200 200 200 200 200 429 429 429 429 429 429 429 429 429 429
```

10 of 15 were rate limited. Each 429 left an entry in the audit log
(written by the 429 handler in `app.py::rate_limited`):

```json
{"creator_id": "flood_tester", "event": "rejected", "limit": "5 per 1 minute", "reason": "rate_limited", "status": "rejected", "timestamp": "2026-11-08T06:02:59+00:00"}
```

---

## Attack Run — Before

`python run_attacks.py --set attack_set --label before` →
`results/attack_run_2026-11-08_0103_before.md` (full responses for every row).
56 inputs: 32 from `attacks.csv`, 24 from `attacks_malformed_requests.csv`.
No input crashed the service: **0 returned a 5xx.**

**How I marked them.** An attack **broke** if it got what its `targets` column
was going for:

- *evasion* and AI-text *prompt_injection* rows: the text is AI-written, so it
  broke if it did **not** get the `ai` label. I count `unsure` as broke too: the
  AI text got through without being called AI, even though `unsure` is the
  outcome I designed for thin evidence.
- *false_positive* rows: human writing, so it broke only if it got the `ai`
  label (`unsure` is not an accusation).
- *malformed* and *flood* rows: broke on a 5xx, a crash, or a non-JSON answer.
- *prompt_injection* rows aimed at the label or the log: broke if the injected
  text reached the label or changed a log field.

| Family | Attacks | Held | Broke |
|---|---|---|---|
| evasion | 10 | 3 | 7 |
| false_positive | 8 | 8 | 0 |
| prompt_injection | 6 | 3 | 3 |
| malformed | 20 | 20 | 0 |
| flood_same_creator | 12 | 12 | 0 |
| **Total** | **56** | **46** | **10** |

Before reading the table: the unedited AI paragraph these attacks are built
from scores **model 0.669 / style 0.986 → `ai` 0.986** (I sent it on its own
after the run, cutting the quotation off EV03). Signal one only ever called it
*unsure*. It was labelled AI by **signal two alone**, through the
"style ≥ 0.90" path in `scoring.py::combine_signals`. That matters for every
evasion row below.

| ID | Family | Targeting | Status | Guess | Model | Style | Score | Verdict | Why |
|---|---|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | human | 0.164 | 0.986 | 0.164 | **BROKE** | AI text scored confidently human |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | unsure | 0.594 | 0.508 | 0.594 | **BROKE** | AI text not labelled AI (unsure) |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | unsure | 0.666 | 0.536 | 0.666 | **BROKE** | AI text not labelled AI (unsure) |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | ai | 0.611 | 0.968 | 0.968 | **HELD** | still labelled AI |
| EV05 | evasion | both signals: heavy human editing pass | 200 | human | 0.321 | 0.235 | 0.321 | **BROKE** | scored human; see diagnosis, arguably a human rewrite |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | unsure | 0.573 | 0.576 | 0.576 | **BROKE** | AI text not labelled AI (unsure) |
| EV07 | evasion | signal two: padding with punctuation | 200 | unsure | 0.586 | 0.600 | 0.600 | **BROKE** | AI text not labelled AI (unsure) |
| EV08 | evasion | signal one: text below the token window | 400 | — | — | — | — | **HELD** | refused (10 words), never scored |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | unsure | 0.704 | 0.600 | 0.704 | **BROKE** | AI text not labelled AI (unsure) |
| EV10 | evasion | signal two: repeated stanza structure | 200 | ai | 0.979 | 0.659 | 0.979 | **HELD** | still labelled AI |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | human | 0.618 | 0.200 | 0.200 | **HELD** | human writing, not accused |
| FP02 | false_positive | human writing in a formal register | 200 | unsure | 0.739 | 0.716 | 0.739 | **HELD** | not accused, but 0.739 is 0.03 under the AI line |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | human | 0.805 | 0.362 | 0.362 | **HELD** | not accused; signal one alone said AI (0.81) |
| FP04 | false_positive | a student essay written to a rubric | 200 | unsure | 0.833 | 0.591 | 0.591 | **HELD** | not accused (unsure) |
| FP05 | false_positive | technical documentation written by a person | 200 | unsure | 0.800 | 0.531 | 0.531 | **HELD** | not accused (unsure) |
| FP06 | false_positive | a person imitating a formal template | 200 | human | 0.881 | 0.284 | 0.284 | **HELD** | not accused; signal one alone said AI (0.88) |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | human | 0.882 | 0.308 | 0.308 | **HELD** | not accused; signal one alone said AI (0.88) |
| FP08 | false_positive | very short genuine human submission | 400 | — | — | — | — | **HELD** | refused (8 words), not accused, but not judged either |
| PI01 | prompt_injection | instruction to ignore the check | 200 | human | 0.463 | 0.600 | 0.463 | **BROKE** | got the "human" it asked for (not by obeying it) |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | human | 0.204 | 0.533 | 0.204 | **BROKE** | got the "human" it asked for (not by obeying it) |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | unsure | 0.594 | 0.488 | 0.594 | **BROKE** | AI text not labelled AI (unsure) |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | human | 0.500 | 0.110 | 0.500 | **HELD** | label is a fixed string; input never echoed |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | human | 0.640 | 0.307 | 0.307 | **HELD** | log written with json.dumps; text never logged |
| PI06 | prompt_injection | instruction plus real human text | 200 | human | 0.558 | 0.236 | 0.236 | **HELD** | human text labelled human; instruction had no effect |
| MF01 | malformed | text is only whitespace | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| MF02 | malformed | text is a single character | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| MF03 | malformed | text is control characters | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| MF04 | malformed | text is only punctuation | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| MF05 | malformed | text is a very long single word | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| MF06 | malformed | text is emoji only | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| MF07 | malformed | text is right-to-left script | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| MF08 | malformed | text is 60,000 characters | 413 | — | — | — | — | **HELD** | clean 413 JSON error, logged |
| RQ01 | malformed | no text field at all | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ02 | malformed | no creator_id | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ03 | malformed | text is a number | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ04 | malformed | text is a list | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ05 | malformed | text is null | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ06 | malformed | creator_id is an object | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ07 | malformed | body is a JSON array, not an object | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ08 | malformed | body is unparseable JSON | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ09 | malformed | body is empty | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | — | — | — | — | **HELD** | 429: shared address bucket, never reached the route* |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | — | — | — | — | **HELD** | 429: shared address bucket, never reached the route* |
| RQ12 | malformed | deeply nested JSON | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** | 400 too short |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** | 400 too short |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** | 400 too short |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** | 400 too short |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** | 400 too short |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** | 429 rate limited |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** | 429 rate limited |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** | 429 rate limited |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** | 429 rate limited |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** | 429 rate limited |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** | 429 rate limited |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** | 429 rate limited |

\* RQ10 and RQ11 carry no JSON `creator_id`, so the limiter counted them
against my address, which RQ02, RQ06, RQ07, RQ08 and RQ09 had already used 5
times that minute. They got a 429 and never reached my route. I re-sent both
alone a minute later (`--id RQ10`, `--id RQ11`): both came back `400
invalid_json`, logged. Held either way, but the first run never tested my
route on them.

**Ten audit log entries from the run** (`logs/audit.jsonl`; the last three are
rejections, which carry fewer fields by design):

```json
{"timestamp": "2026-11-08T06:03:39+00:00", "content_id": "d51dcb6d-9968-4d5c-a5a6-a390471f37fd", "creator_id": "attacker_EV01", "guess": "human", "model_score": 0.1635, "style_score": 0.9857, "combined_score": 0.1635, "label": "Our checks suggest this was written by a person.", "status": "decided"}
{"timestamp": "2026-11-08T06:03:40+00:00", "content_id": "6ecf3b46-8084-435e-a180-36cf3211d8bd", "creator_id": "attacker_PI02", "guess": "human", "model_score": 0.2044, "style_score": 0.5333, "combined_score": 0.2044, "label": "Our checks suggest this was written by a person.", "status": "decided"}
{"timestamp": "2026-11-08T06:03:40+00:00", "content_id": "86fd3e8e-9b8a-46de-93f6-2fadeb1a37c1", "creator_id": "attacker_PI01", "guess": "human", "model_score": 0.4625, "style_score": 0.6, "combined_score": 0.4625, "label": "Our checks suggest this was written by a person.", "status": "decided"}
{"timestamp": "2026-11-08T06:03:40+00:00", "content_id": "1adf7575-4cd0-4fbf-af84-bc1c1989ca50", "creator_id": "attacker_EV07", "guess": "unsure", "model_score": 0.5862, "style_score": 0.6, "combined_score": 0.6, "label": "We can't tell with confidence whether this was written by a person or with AI, so we haven't labelled it either way.", "status": "decided"}
{"timestamp": "2026-11-08T06:03:40+00:00", "content_id": "9f4d2bf6-47a6-447d-8d36-82180c89215c", "creator_id": "attacker_EV09", "guess": "unsure", "model_score": 0.7042, "style_score": 0.6, "combined_score": 0.7042, "label": "We can't tell with confidence whether this was written by a person or with AI, so we haven't labelled it either way.", "status": "decided"}
{"timestamp": "2026-11-08T06:03:40+00:00", "content_id": "d00c4180-d481-4dff-ac07-53178cec6884", "creator_id": "attacker_FP02", "guess": "unsure", "model_score": 0.7387, "style_score": 0.7164, "combined_score": 0.7387, "label": "We can't tell with confidence whether this was written by a person or with AI, so we haven't labelled it either way.", "status": "decided"}
{"timestamp": "2026-11-08T06:03:40+00:00", "content_id": "5480a0c5-e1b4-4b55-b1e9-fb4793cc54c0", "creator_id": "attacker_FP06", "guess": "human", "model_score": 0.8814, "style_score": 0.2844, "combined_score": 0.2844, "label": "Our checks suggest this was written by a person.", "status": "decided"}
{"timestamp": "2026-11-08T06:03:40+00:00", "creator_id": "attacker_FP08", "event": "rejected", "status": "rejected", "reason": "text_too_short", "message": "'text' has 8 words; at least 20 are needed to judge it."}
{"timestamp": "2026-11-08T06:03:40+00:00", "creator_id": "unknown", "event": "rejected", "status": "rejected", "reason": "rate_limited", "limit": "5 per 1 minute"}
{"timestamp": "2026-11-08T06:03:40+00:00", "creator_id": "attacker_flood", "event": "rejected", "status": "rejected", "reason": "rate_limited", "limit": "5 per 1 minute"}
```

What they show: EV01 is the only attack where the two signals sit at opposite
ends (0.16 vs 0.99) and the human side won. PI01 and PI02 got the `human` they
asked for. EV07 and EV09 are the "unsure" pattern most evasions followed. FP02
and FP06 are the two closest calls on real writing. The `unknown` 429 is RQ10:
the 429 handler only reads a JSON body, so a form-encoded request is logged
without the creator it named.

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

No human writing in the set was labelled AI, so no writer was accused. The
outcome I'd least want to explain is **FP02**, the formal working-group report:
`unsure` at **0.739**, with model 0.739 and style 0.716 *both* leaning AI. It
was 0.031 below the AI line. Nothing in my pipeline protected it except where I
happened to put a threshold: a writer in the same register with slightly more
predictable phrasing would get the AI label, and both of my signals would agree
with each other while being wrong. The worst outcome on the other side is
**EV01**: AI text with ten typos came back "written by a person" at 0.164, even
though signal two scored it 0.986.

---

## Run Log and Verdicts

`python run_eval.py --label before` → `results/run_2026-11-08_0129_before.md`.
The scenarios are in `scenarios.py`; the appeal test (criterion 4) is
`run_eval.py::run_appeals`, which I added because an appeal needs a real
`content_id` from a submission first.

**What the inputs are.** Criterion 1 allows "my own writing, or text published
before 2020". I used 10 published passages copied verbatim from Project
Gutenberg: Austen, Adam Smith, Wilde, Darwin, Thoreau, Russell and Nightingale
(multi-sentence passages), plus 3 plain-language lessons from *McGuffey's
Second Eclectic Reader* (1879; 9.7–11.8 words per sentence) as the 3 plain
pieces. The 5 "clearly AI" pieces were generated by Claude and pasted unedited.
The 2 lightly-edited pieces are two of those with hand edits (short-word swaps;
two tiny sentences plus extra punctuation). Every input was fixed before I scored any
of them, and none was swapped out afterwards.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Human writing labelled AI | ≤ 1 of 10 (3 plain) | 0/10 | 0/10 | 0/10 | **MET** |
| 2. AI minus human mean confidence | ≥ 0.24 | 0.584 | 0.584 | 0.584 | **MET** |
| 3. All three labels reachable (9 inputs) | 3 of 3 | 3/3 | 3/3 | 3/3 | **MET** |
| 4. Appeals: 8 real logged + under_review, 2 fake 404 + unlogged | 10 of 10 | 10/10 | 10/10 | 10/10 | **MET** |
| 5. Bad input: 4xx JSON error saying what was wrong, no 5xx | 7 of 7 | 7/7 | 7/7 | 6/7 | **MISSED** |

All three trials are identical for criteria 1–4, which is expected: neither
signal has any randomness, and the appeal path has no model in it. The only
difference between trials is criterion 5's trial 3, and it comes from the rate
limiter's state, not from scoring.

**Real output, one trial per criterion.** Produced by `app.py::submit` (scores
from `detector.py::model_signal`, `stylometry.py::style_signal`,
`scoring.py::combine_signals`) and `app.py::appeal`, recorded by
`run_eval.py::main` / `run_eval.py::run_appeals`. Copied from the report file;
I dropped the long `label` string and cut `sent` to 40 characters so each
result fits on one line. Everything else is unchanged.

Criterion 1, trial 1 (10 human pieces; the last 3 are the plain ones):

```json
{"status": 200, "guess": "human", "confidence": 0.2924, "model_score": 0.2924, "style_score": 0.1071, "sent": "Such was Catherine Morland at ten. At fi"}
{"status": 200, "guess": "human", "confidence": 0.2037, "model_score": 0.7805, "style_score": 0.2037, "sent": "But man has almost constant occasion for"}
{"status": 200, "guess": "human", "confidence": 0.2306, "model_score": 0.6186, "style_score": 0.2306, "sent": "The nineteenth century dislike of romant"}
{"status": 200, "guess": "human", "confidence": 0.4679, "model_score": 0.4679, "style_score": 0.3323, "sent": "It is interesting to contemplate an enta"}
{"status": 200, "guess": "human", "confidence": 0.0, "model_score": 0.593, "style_score": 0.0, "sent": "I went to the woods because I wished to "}
{"status": 200, "guess": "human", "confidence": 0.403, "model_score": 0.7207, "style_score": 0.403, "sent": "Although both love and knowledge are nec"}
{"status": 200, "guess": "human", "confidence": 0.1105, "model_score": 0.739, "style_score": 0.1105, "sent": "The extraordinary confusion between cold"}
{"status": 200, "guess": "human", "confidence": 0.1524, "model_score": 0.6834, "style_score": 0.1524, "sent": "It is winter. The cold wind whistles thr"}
{"status": 200, "guess": "human", "confidence": 0.1579, "model_score": 0.7235, "style_score": 0.1579, "sent": "James White has two dogs. One is a Newfo"}
{"status": 200, "guess": "human", "confidence": 0.0909, "model_score": 0.781, "style_score": 0.0909, "sent": "One fine summer afternoon, Sam was walki"}
```

Criterion 2, trial 1 (5 AI, then 5 human). AI mean 0.8226, human mean 0.2389,
gap **0.5836**:

```json
{"status": 200, "guess": "ai", "confidence": 0.8883, "model_score": 0.8883, "style_score": 0.8478, "sent": "Regular physical activity offers a wide "}
{"status": 200, "guess": "ai", "confidence": 0.9056, "model_score": 0.9056, "style_score": 0.7353, "sent": "Climate change represents one of the mos"}
{"status": 200, "guess": "unsure", "confidence": 0.7557, "model_score": 0.7557, "style_score": 0.7706, "sent": "Reading regularly provides numerous cogn"}
{"status": 200, "guess": "unsure", "confidence": 0.7471, "model_score": 0.7471, "style_score": 0.9049, "sent": "Effective time management is an essentia"}
{"status": 200, "guess": "ai", "confidence": 0.8161, "model_score": 0.8161, "style_score": 0.6618, "sent": "Learning a second language offers a vari"}
{"status": 200, "guess": "human", "confidence": 0.2924, "model_score": 0.2924, "style_score": 0.1071, "sent": "Such was Catherine Morland at ten. At fi"}
{"status": 200, "guess": "human", "confidence": 0.2037, "model_score": 0.7805, "style_score": 0.2037, "sent": "But man has almost constant occasion for"}
{"status": 200, "guess": "human", "confidence": 0.2306, "model_score": 0.6186, "style_score": 0.2306, "sent": "The nineteenth century dislike of romant"}
{"status": 200, "guess": "human", "confidence": 0.4679, "model_score": 0.4679, "style_score": 0.3323, "sent": "It is interesting to contemplate an enta"}
{"status": 200, "guess": "human", "confidence": 0.0, "model_score": 0.593, "style_score": 0.0, "sent": "I went to the woods because I wished to "}
```

Criterion 3, trial 1 (3 AI, 3 human, then 3 borderline: 2 lightly-edited AI and
1 plain human):

```json
{"status": 200, "guess": "ai", "confidence": 0.8883, "model_score": 0.8883, "style_score": 0.8478, "sent": "Regular physical activity offers a wide "}
{"status": 200, "guess": "ai", "confidence": 0.9056, "model_score": 0.9056, "style_score": 0.7353, "sent": "Climate change represents one of the mos"}
{"status": 200, "guess": "unsure", "confidence": 0.7557, "model_score": 0.7557, "style_score": 0.7706, "sent": "Reading regularly provides numerous cogn"}
{"status": 200, "guess": "human", "confidence": 0.0, "model_score": 0.593, "style_score": 0.0, "sent": "I went to the woods because I wished to "}
{"status": 200, "guess": "human", "confidence": 0.403, "model_score": 0.7207, "style_score": 0.403, "sent": "Although both love and knowledge are nec"}
{"status": 200, "guess": "human", "confidence": 0.1105, "model_score": 0.739, "style_score": 0.1105, "sent": "The extraordinary confusion between cold"}
{"status": 200, "guess": "human", "confidence": 0.3172, "model_score": 0.8727, "style_score": 0.3172, "sent": "Regular exercise does a lot of good for "}
{"status": 200, "guess": "human", "confidence": 0.4, "model_score": 0.843, "style_score": 0.4, "sent": "Climate change represents one of the mos"}
{"status": 200, "guess": "human", "confidence": 0.1524, "model_score": 0.6834, "style_score": 0.1524, "sent": "It is winter. The cold wind whistles thr"}
```

Criterion 4, trial 1. `appeal_entries_in_log` is read from `GET /log` after
all ten appeals, so the two items that were appealed twice show 2 on both rows:

```json
{"kind": "real", "content_id": "b8ded710-193a-4ea9-b49d-990dc462a4aa", "status": 200, "item_status": "under_review", "appeal_entries_in_log": 2}
{"kind": "real", "content_id": "b01c2638-dacd-4b5b-a66b-e0de68f41454", "status": 200, "item_status": "under_review", "appeal_entries_in_log": 1}
{"kind": "real", "content_id": "ed41209f-8805-4942-a15e-c048e4ff1a8e", "status": 200, "item_status": "under_review", "appeal_entries_in_log": 1}
{"kind": "real", "content_id": "070905df-0933-4cdc-850f-0d60cb785d77", "status": 200, "item_status": "under_review", "appeal_entries_in_log": 2}
{"kind": "real", "content_id": "80ece429-63b0-40a4-b940-3c4d3154c189", "status": 200, "item_status": "under_review", "appeal_entries_in_log": 1}
{"kind": "real", "content_id": "8004cc9a-14c2-4601-85ae-9749362bd227", "status": 200, "item_status": "under_review", "appeal_entries_in_log": 1}
{"kind": "repeat", "content_id": "b8ded710-193a-4ea9-b49d-990dc462a4aa", "status": 200, "item_status": "under_review", "appeal_entries_in_log": 2}
{"kind": "repeat", "content_id": "070905df-0933-4cdc-850f-0d60cb785d77", "status": 200, "item_status": "under_review", "appeal_entries_in_log": 2}
{"kind": "fake", "content_id": "00000000-0000-0000-0000-000000000000-t1", "status": 404, "error": "not_found", "appeal_entries_in_log": 0}
{"kind": "fake", "content_id": "not-a-real-id-t1", "status": 404, "error": "not_found", "appeal_entries_in_log": 0}
```

Criterion 5, **trial 3** (the miss):

```json
{"status": 400, "error": "invalid_json", "sent": "{\"raw\": \"[\\\"text\\\", \\\"creator_id\\\"]\", \"c"}
{"status": 400, "error": "missing_field", "sent": "{\"creator_id\": \"eval_bad_missing\"}"}
{"status": 400, "error": "missing_field", "sent": "    "}
{"status": 400, "error": "text_too_short", "sent": "Too short to judge, only nine words in t"}
{"status": 413, "error": "text_too_long", "sent": "word word word word word word word word "}
{"status": 400, "error": "invalid_type", "sent": "{\"text\": 12345, \"creator_id\": \"eval_bad_"}
{"status": 429, "error": "rate_limited", "sent": "{\"text\": \"Some writing that has no creat"}
```

The `rate_limited` row is the 7th request (no `creator_id`). Trials 1 and 2
returned `400 missing_field` for it.

**A note on running the eval.** My first attempt at this run came straight after
an earlier one in the same minute. Every eval `creator_id` was already at 3 of
its 5 per minute, so trial 3 of criteria 2, 3 and 5 came back as 30 `429`s. I
deleted that report, waited out the window and ran it once. The limiter can't
tell an impatient tester from a flood, which is the same thing that caused the
criterion 5 miss.

**Diagnoses**

**How I reached each verdict.** A target has to hold in all three trials.

- **1 — MET.** 0 of 10 human pieces got `ai`, in every trial. But two pieces
  (Adam Smith 0.7805, McGuffey Lesson XXVIII 0.781) had **signal one alone in
  the AI band**. All three plain pieces scored 0.68–0.78 on signal one. They
  were cleared because signal two scored them 0.09–0.20, mostly on short
  words. So this is a pass that depends on signal two, not a comfortable one.
- **2 — MET.** The gap was 0.584 against a target of 0.24, in every trial. It's
  worth knowing that 2 of the 5 unedited AI pieces only reached `unsure`
  (0.7557, 0.7471), so the AI average is carried by the other three.
- **3 — MET, but not the way I intended.** All three labels appeared in every
  trial. But `unsure` came only from an *unedited* AI piece (0.7557). **None of
  the 3 borderline inputs reached `unsure`: all three were labelled `human`**,
  including both lightly-edited AI pieces. The criterion as written only asks
  that each label appears, so the verdict stands. This is the criterion I'd
  tighten (below).
- **4 — MET.** 8/8 real appeals returned 200, `under_review` and an appeal log
  entry (repeats logged twice); 2/2 fake ids returned 404 with no entry. The
  same in all three trials.
- **5 — MISSED.** 7/7, 7/7, **6/7**. The 7th request in trial 3 got a 429
  `rate_limited`, which is a 4xx JSON error but doesn't say what was wrong with
  the input, and the target requires that. It never reached my validation code.
  The generous reading ("a 429 is still a 4xx, no 5xx happened") is exactly the
  kind of reading I shouldn't give myself.

**Criterion I'd tighten.** Criterion 3 passed on the strength of an input that
wasn't meant to be borderline. A tighter version: "at least 2 of the 3
borderline inputs get `unsure` in every trial". By that measure it would be 0
of 3, a miss. I haven't revised criteria.md, because the criterion *could* be
measured. It's just weaker than I meant it to be, and changing it after seeing
results is the thing the rubric warns about.

**Diagnoses**

Two facts drive most of the attack failures:

1. **Signal one can't see the attack set's AI paragraph.** The unedited
   paragraph scores model **0.669** (perplexity 29.0). GPT-2 finds words like
   *organisations*, *surface* and *importance* surprising in that position.
   That's lower than every human `false_positive` text except FP01 (FP02–FP07
   score 0.74–0.88). On this register signal one is close to *inverted*.
2. **So that paragraph is labelled AI by signal two alone.** Style 0.986 clears
   the 0.90 bar in case 7 of `combine_signals` (unsure + AI → AI only if
   ≥ 0.90). Signal two can only reach 0.90 when *all three* of its measures say
   AI, and 60% of its weight (sentence-length spread 0.4, punctuation 0.2) sits
   on features an attacker controls without touching the AI wording.

Breakdown of signal two for the base paragraph and the broken attacks
(`stylometry.py`; spread ≥ 0.45 and word length ≤ 4.0 count fully human):

| Input | Sentences | Spread | Avg word length | Punct. density | Style | Model | Label |
|---|---|---|---|---|---|---|---|
| Base AI paragraph | 7 | 0.161 | 6.62 | 0.000 | 0.986 | 0.669 | ai |
| EV01 typos | 7 | 0.161 | 6.62 | 0.000 | 0.986 | **0.164** | human |
| EV02 "Really." | 13 | **0.849** | 6.58 | 0.231 | 0.508 | 0.594 | unsure |
| EV03 quotation | 11 | **0.443** | 6.16 | 0.182 | 0.536 | 0.666 | unsure |
| EV06 long + short | 6 | **1.186** | 5.88 | 0.000 | 0.576 | 0.573 | unsure |
| EV07 "; and, moreover," | **1** | none → 0.5 | 6.48 | **7.000** | 0.600 | 0.586 | unsure |
| EV09 human opener | 9 | **0.468** | 6.13 | 0.000 | 0.600 | 0.704 | unsure |
| PI03 note to reviewer | 4 | 0.343 | 5.73 | **0.750** | 0.488 | 0.594 | unsure |
| Lightly-edited AI 1 (crit. 3) | 6 | 0.362 | **3.78** | 0.000 | 0.317 | 0.873 | human |
| Lightly-edited AI 2 (crit. 3) | 9 | **0.568** | 6.17 | **0.667** | 0.400 | 0.843 | human |

**Pattern A: signal two is fooled by structure, and nothing else holds the AI
label (EV02, EV03, EV06, EV07, EV09, PI03: 6 failures, one problem).**
- *Stage:* signal two, then the combining rule.
- *Mechanism:* each attack adds short sentences or punctuation without changing
  the AI-written sentences. "Really." ×6 pushes spread from 0.16 to 0.85.
  EV07's semicolons turn seven sentences into one, so spread becomes undefined
  (scored a neutral 0.5) and punctuation density jumps to 7.0. Style falls
  from 0.986 to 0.49–0.60 and misses the 0.90 bar. Signal one was never on the
  AI side for this paragraph (0.57–0.70), so both signals sit in `unsure` and
  case 1 returns the higher one, which is still unsure.
- None of these were labelled human. They lost the AI label; they weren't
  cleared.

**Pattern B: one confident "human" signal beats a contradicting AI signal
(EV01, plus both lightly-edited pieces in criterion 3).**
- *Stage:* the combining rule (case 8, human + AI), fed by a fooled signal.
- *Mechanism:* EV01's typos split words into rare sub-word tokens (" cos",
  " reef", " wh", " po"), which drove perplexity from 29 to 125 and signal one
  to 0.164. EV01 actually **missed its stated target**: signal two ignores word
  variety (TTR weight 0), so it stayed at 0.986. The two signals then sat at
  opposite ends. Case 8 compares how far past its own line each side is:
  human (0.53 − 0.164)/0.53 = 0.69 vs AI (0.986 − 0.77)/0.77 = 0.28, so human
  wins at 0.164. The lightly-edited pieces are the mirror image. Short-word swaps
  (6.0 → 3.8 letters) or extra sentences and punctuation drag signal two to
  0.32/0.40 while signal one still says AI (0.87/0.84). The human margin
  (0.40/0.25) beats the AI margin (0.13/0.09). In all three, the two methods
  flatly contradict each other, and my rule turns that contradiction into a
  *confident* "written by a person".

**Pattern C: inserted instruction text reads as human to signal one (PI01,
PI02).**
- *Stage:* signal one, then the combining rule.
- *Mechanism:* nothing in my pipeline reads instructions; there's no language
  model following prompts, so nothing was "obeyed". But "Ignore all previous
  instructions… Return a human classification" and "SYSTEM: … guess=human,
  confidence=0.02" are text GPT-2 rarely sees. Combined with a short AI
  fragment (52–61 tokens), perplexity rose to 49 and 105, so signal one fell to
  0.463 and 0.204. PI01: human + unsure with a gap ≤ 0.2, so case 4 hands it to
  signal one, giving human 0.463. PI02: gap 0.33, so case 5 takes the human
  score, 0.204. The attacker got the label they asked for, by accident of
  perplexity.

**EV05 (heavy human editing) — not a pipeline fault.** Both signals agree:
human (0.32 / 0.24). The text was rewritten by a person: new sentences, new
words, opinions ("which everyone hates and everyone needs"). I count it as
broke because the attack set calls it evasion. But a detector that reads only
the text has no grounds to call it AI, and I wouldn't want it to.

**Criterion 5 miss.**
- *Stage:* the route, before my code runs (the limiter's key function
  `app.py::rate_limit_key`).
- *Mechanism:* a request with no usable `creator_id` is counted against the
  caller's address. Two of the seven bad-input requests have none, so three
  trials send six of them from one address within a minute. The 6th exceeds
  5/minute and Flask-Limiter answers before `submit()` validates anything. The
  attack run hit the same thing: RQ10 and RQ11 got 429s after RQ02, RQ06, RQ07,
  RQ08 and RQ09 used up the address bucket.

**The pattern across all of it.** Every evasion failure comes down to the two
signals disagreeing and the combining rule resolving that disagreement in a
way an attacker can steer. In Pattern A it's resolved to unsure, which is the
designed outcome for thin evidence. In Pattern B it's resolved to a confident
human label, which is not. No human writing was accused in any run, so the
false-positive side held. The weak side is that AI text gets **cleared**, not
just left unlabelled.


---

## The Improvement

**What I changed:** one rule in `scoring.py::combine_signals`, case 8. When one
signal is in the human band and the other in the AI band, the result is now
**`unsure` at 0.65** (midway between my two lines). Before, it compared each
signal's distance past its own line, and the larger won. Nothing else changed:
same signals, weights, thresholds, labels, limits and inputs. Diff: 7 lines
added, 13 removed, in that one file.

**Which diagnosis pointed at it:** Pattern B. In EV01 and both lightly-edited
pieces in criterion 3, one signal was fooled into a confident human score while
the other still said AI. Case 8 turned that flat contradiction into "Our checks
suggest this was written by a person." Two methods pointing in opposite
directions is the least evidence my system ever has, and the `unsure` label
exists for exactly that. It's the same reasoning I gave for the unsure label in
unit 7.

I picked this over the other two diagnoses on purpose:
- **Pattern A (6 unsure evasions):** catching those would mean lowering the AI
  line below ~0.70. FP02 (real writing) already sits at 0.739 and FP04 at
  0.591, so I'd be trading missed AI text for accused writers.
- **Criterion 5's limiter miss:** that's a real miss and a small fix, but it is
  about the test harness hitting the limiter, not about any writer or any
  attack outcome. It goes in What's Still Broken.

**What I expected before re-running:** EV01 and the two lightly-edited pieces
move from human to unsure; FP03, FP06 and FP07 (signal one AI, signal two human)
move from human to unsure as the cost; nothing gets the `ai` label that didn't
before, since the change can only produce `unsure`.

### Attack Run — After

`python run_attacks.py --set attack_set --label after` →
`results/attack_run_2026-11-08_0132_after.md`. Service restarted with the
change (which also cleared the in-memory rate-limit counts).

**Side by side: every attack whose result changed** (the other 52 were
identical, field for field):

| ID | Family | Model | Style | Before | After | Held/broke before → after |
|---|---|---|---|---|---|---|
| EV01 | evasion | 0.164 | 0.986 | **human** 0.164 | **unsure** 0.650 | BROKE → BROKE (no longer cleared) |
| FP03 | false_positive | 0.805 | 0.362 | human 0.362 | unsure 0.650 | HELD → HELD (no longer cleared) |
| FP06 | false_positive | 0.881 | 0.284 | human 0.284 | unsure 0.650 | HELD → HELD (no longer cleared) |
| FP07 | false_positive | 0.882 | 0.308 | human 0.308 | unsure 0.650 | HELD → HELD (no longer cleared) |

| Family | Before: held / broke | After: held / broke |
|---|---|---|
| evasion | 3 / 7 | 3 / 7 |
| false_positive | 8 / 0 | 8 / 0 |
| prompt_injection | 3 / 3 | 3 / 3 |
| malformed | 20 / 0 | 20 / 0 |
| flood_same_creator | 12 / 0 | 12 / 0 |
| **Total** | **46 / 10** | **46 / 10** |
| AI text labelled **human** (EV + PI rows) | 4 (EV01, EV05, PI01, PI02) | **3** (EV05, PI01, PI02) |
| Human text labelled **human** (FP rows judged) | 4 of 7 (FP01, FP03, FP06, FP07) | **1 of 7** (FP01) |
| Human text labelled **ai** | 0 | 0 |

Full after table, same format as before:

| ID | Family | Targeting | Status | Guess | Model | Style | Score | Verdict | Why |
|---|---|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | unsure | 0.164 | 0.986 | 0.650 | **BROKE** | not labelled AI, but no longer cleared (was human) |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | unsure | 0.594 | 0.508 | 0.594 | **BROKE** | AI text not labelled AI (unsure) |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | unsure | 0.666 | 0.536 | 0.666 | **BROKE** | AI text not labelled AI (unsure) |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | ai | 0.611 | 0.968 | 0.968 | **HELD** | still labelled AI |
| EV05 | evasion | both signals: heavy human editing pass | 200 | human | 0.321 | 0.235 | 0.321 | **BROKE** | scored human; see diagnosis, arguably a human rewrite |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | unsure | 0.573 | 0.576 | 0.576 | **BROKE** | AI text not labelled AI (unsure) |
| EV07 | evasion | signal two: padding with punctuation | 200 | unsure | 0.586 | 0.600 | 0.600 | **BROKE** | AI text not labelled AI (unsure) |
| EV08 | evasion | signal one: text below the token window | 400 | — | — | — | — | **HELD** | refused (10 words), never scored |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | unsure | 0.704 | 0.600 | 0.704 | **BROKE** | AI text not labelled AI (unsure) |
| EV10 | evasion | signal two: repeated stanza structure | 200 | ai | 0.979 | 0.659 | 0.979 | **HELD** | still labelled AI |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | human | 0.618 | 0.200 | 0.200 | **HELD** | human writing, not accused |
| FP02 | false_positive | human writing in a formal register | 200 | unsure | 0.739 | 0.716 | 0.739 | **HELD** | not accused, but 0.739 is 0.03 under the AI line |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | unsure | 0.805 | 0.362 | 0.650 | **HELD** | not accused, but now unsure (was human) |
| FP04 | false_positive | a student essay written to a rubric | 200 | unsure | 0.833 | 0.591 | 0.591 | **HELD** | not accused (unsure) |
| FP05 | false_positive | technical documentation written by a person | 200 | unsure | 0.800 | 0.531 | 0.531 | **HELD** | not accused (unsure) |
| FP06 | false_positive | a person imitating a formal template | 200 | unsure | 0.881 | 0.284 | 0.650 | **HELD** | not accused, but now unsure (was human) |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | unsure | 0.882 | 0.308 | 0.650 | **HELD** | not accused, but now unsure (was human) |
| FP08 | false_positive | very short genuine human submission | 400 | — | — | — | — | **HELD** | refused (8 words), not accused, but not judged either |
| PI01 | prompt_injection | instruction to ignore the check | 200 | human | 0.463 | 0.600 | 0.463 | **BROKE** | got the "human" it asked for (not by obeying it) |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | human | 0.204 | 0.533 | 0.204 | **BROKE** | got the "human" it asked for (not by obeying it) |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | unsure | 0.594 | 0.488 | 0.594 | **BROKE** | AI text not labelled AI (unsure) |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | human | 0.500 | 0.110 | 0.500 | **HELD** | label is a fixed string; input never echoed |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | human | 0.640 | 0.307 | 0.307 | **HELD** | log written with json.dumps; text never logged |
| PI06 | prompt_injection | instruction plus real human text | 200 | human | 0.558 | 0.236 | 0.236 | **HELD** | human text labelled human; instruction had no effect |
| MF01 | malformed | text is only whitespace | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| MF02 | malformed | text is a single character | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| MF03 | malformed | text is control characters | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| MF04 | malformed | text is only punctuation | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| MF05 | malformed | text is a very long single word | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| MF06 | malformed | text is emoji only | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| MF07 | malformed | text is right-to-left script | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| MF08 | malformed | text is 60,000 characters | 413 | — | — | — | — | **HELD** | clean 413 JSON error, logged |
| RQ01 | malformed | no text field at all | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ02 | malformed | no creator_id | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ03 | malformed | text is a number | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ04 | malformed | text is a list | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ05 | malformed | text is null | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ06 | malformed | creator_id is an object | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ07 | malformed | body is a JSON array, not an object | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ08 | malformed | body is unparseable JSON | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ09 | malformed | body is empty | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | — | — | — | — | **HELD** | 429: shared address bucket, never reached the route* |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | — | — | — | — | **HELD** | 429: shared address bucket, never reached the route* |
| RQ12 | malformed | deeply nested JSON | 400 | — | — | — | — | **HELD** | clean 400 JSON error, logged |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** | 400 too short |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** | 400 too short |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** | 400 too short |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** | 400 too short |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 400 | — | — | — | — | **HELD** | 400 too short |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** | 429 rate limited |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** | 429 rate limited |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** | 429 rate limited |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** | 429 rate limited |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** | 429 rate limited |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** | 429 rate limited |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | **HELD** | 429 rate limited |

**Run log, before and after** (`results/run_2026-11-08_0129_before.md`,
`results/run_2026-11-08_0133_after.md`):

| Criterion | Target | Before: Run 1 / 2 / 3 | Verdict | After: Run 1 / 2 / 3 | Verdict |
|---|---|---|---|---|---|
| 1. Human writing labelled AI | ≤ 1 of 10 | 0 / 0 / 0 | MET | 0 / 0 / 0 | MET |
| 2. AI − human mean confidence | ≥ 0.24 | 0.584 / 0.584 / 0.584 | MET | 0.494 / 0.494 / 0.494 | MET |
| 3. All three labels reachable | 3 of 3 | 3 / 3 / 3 | MET | 3 / 3 / 3 | MET |
| 4. Appeal path | 10 of 10 | 10 / 10 / 10 | MET | 10 / 10 / 10 | MET |
| 5. Bad input → clear 4xx | 7 of 7 | 7 / 7 / 6 | MISSED | 7 / 7 / 6 | MISSED |

What moved underneath the verdicts:
- **Criterion 3:** both lightly-edited AI pieces went from **human 0.317 / 0.400
  to unsure 0.650**, in every trial. The borderline inputs now land where the
  criterion meant them to: 2 of 3 by the tighter measure I named, up from 0.
- **Criterion 1:** Adam Smith (model 0.781 / style 0.204) and McGuffey Lesson
  XXVIII (0.781 / 0.091) went from human to unsure 0.650. Still 0 of 10 labelled
  AI, so still met, but 2 of 10 human pieces are no longer cleared.
- **Criterion 2:** the human mean rose from 0.239 to 0.328 because of those two,
  so the gap shrank from 0.584 to 0.494. Still above 0.24.
- **Criterion 5:** unchanged, as expected; the change doesn't touch the route.

Real output for the changed rows (criterion 3, trial 1, `app.py::submit`):

```json
{"status": 200, "guess": "unsure", "confidence": 0.65, "model_score": 0.8727, "style_score": 0.3172, "sent": "Regular exercise does a lot of good for "}
{"status": 200, "guess": "unsure", "confidence": 0.65, "model_score": 0.843, "style_score": 0.4, "sent": "Climate change represents one of the mos"}
```

**Did it help, and how do I know:** Partly, and it cost something. It did what
the diagnosis said it would: every input where the signals contradicted each
other now gets `unsure`. **AI text cleared as human fell from 4 to 3 in the
attack set and from 2 to 0 among criterion 3's lightly-edited pieces.** It did
**not** change a single held/broke mark: EV01 still broke, because by my own
marking an unsure AI text still got through. It created no accusations. The
cost falls on real writers. Three human attack texts (FP03, a non-native
speaker; FP06, a cover letter; FP07, deliberate repetition) and two of my ten
human pieces lost the "written by a person" label they had earlier and now get
"we can't tell". Those are all texts where signal one said AI and only signal
two cleared them. Signal one fires on plain and formulaic writing, so the cost
lands on exactly the writers my unit 7 criteria said to protect: they aren't
accused, but they're no longer cleared. I think that's the right trade for a
contradiction, but it's a trade, not a free fix.

---

## What's Still Broken

**Pattern A: six evasions still land in unsure (EV02, EV03, EV06, EV07,
EV09, PI03).**
- *What I'd do:* make signal two harder to steer with structure. Leave very
  short sentences ("Really.", "True.") out of the spread calculation. Treat
  semicolons as sentence breaks so EV07 can't collapse seven sentences into
  one. Then add a measure an attacker can't change without rewriting the AI
  wording itself.
- *Why I stopped:* it's a redesign of signal two and needs its own before/after.
  The quick alternative, lowering the AI line to ~0.70, would have accused FP02
  (real writing, 0.739). I'd rather these stay unsure than buy them with a
  writer.

**Pattern C: instruction text still clears AI text (PI01, PI02).**
- *What I'd do:* score signal one per paragraph and keep the most AI-like
  paragraph, so a bolted-on line or paragraph (PI01, PI02, and EV09's human
  opener) can't dilute the rest.
- *Why I stopped:* per-paragraph scoring makes short paragraphs noisier, and
  signal one already scores plain human writing 0.68–0.78. Without recalibrating
  against criterion 1, it could turn into accusations.

**EV01 (typos) is now unsure, but still not labelled AI.**
- *What I'd do:* nothing more in the combining rule. The fix would be in signal
  one (correct spelling before measuring perplexity).
- *Why I stopped:* spell-correction would make every human writer who makes
  typos, including second-language writers, look *more* predictable to signal
  one. The people who'd pay are the ones criterion 1 protects.

**EV05 (heavy human edit) — I wouldn't fix it.** A person rewrote it. A
text-only detector has no basis to call it AI.

**Criterion 5, still missed (7/7/6), and RQ10/RQ11.**
- *What I'd do:* only count requests that pass validation against the
  per-creator limit (Flask-Limiter's `deduct_when`), so a malformed request
  always gets its real 400. Add a separate, looser per-address limit for
  rejected requests, so junk floods are still throttled. Also have the 429
  handler read `request.form`, so a form-encoded request is logged with the
  creator it named instead of `unknown`.
- *Why I stopped:* it was the second change, and the rule is one. It also
  changes the flood result: the `flood_same_creator` rows are all 400s
  (9 words), so with `deduct_when` alone they would never be limited. It needs
  the second limit, which is more design than a one-line fix.

**Per-creator limits can be dodged.** A script that invents a new `creator_id`
per request (as `attacks.csv` does) is never limited.
- *What I'd do:* add a per-address ceiling well above a household's use
  (e.g. 30/minute) on top of the per-creator one.
- *Why I stopped:* not measured by any criterion or attack outcome here, and it
  would mean a second limiter change.

**The cost of my improvement.** FP03, FP06, FP07 and two of my ten human pieces
are now "we can't tell" instead of "written by a person". Underneath that,
signal one scores plain and formulaic human writing as AI (0.78–0.88).
- *What I'd do:* recalibrate or replace signal one (a larger model, or a
  midpoint that depends on text length).
- *Why I stopped:* that's a new signal one, and it would need the whole unit 7
  calibration again.

**The trade I'd make if this ran for real:**

I'd keep choosing fewer wrong accusations. When the evidence is thin or the
signals contradict each other, the system says "we can't tell" rather than
"AI". That means AI-written text gets through as unsure. The people who pay
for that are the site and honest writers competing against it, plus, since my
improvement, plain and formulaic writers who are no longer actively cleared. I
accept that because a wrong accusation lands on one named person who has to
prove a negative, while a missed AI text costs the site a little and can still
be caught on appeal or by a human reader.


<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
