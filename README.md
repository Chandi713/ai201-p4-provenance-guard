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

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



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
