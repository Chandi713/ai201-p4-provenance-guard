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

**What it measures:**

**Why that might differ between human and AI writing:**

**What it can't see:**

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:**

**The numbers:**

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human |  |  |
| unsure |  |  |
| high-confidence AI |  |  |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

> Interim run from Milestone 3: one signal wired in, `confidence`, `label` and
> `style_score` are still placeholders. Replaced with a full run after
> Milestone 5.

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "My grandmother kept her buttons in a biscuit tin that had long since lost its biscuits. On wet Sundays she would tip them out on the rug and let me sort them by colour.", "creator_id": "smit"}'
```

```json
{
  "confidence": null,
  "content_id": "46484925-28d1-4319-ac53-9baa34015d05",
  "guess": "unsure",
  "label": "placeholder",
  "model_score": 0.3672,
  "status": "decided",
  "style_score": null
}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "...", "reasoning": "..."}'
```

```json

```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=1"
```

```json
{
  "count": 1,
  "entries": [
    {
      "combined_score": null,
      "content_id": "46484925-28d1-4319-ac53-9baa34015d05",
      "creator_id": "smit",
      "guess": "unsure",
      "label": "placeholder",
      "model_score": 0.3672,
      "status": "decided",
      "style_score": null,
      "timestamp": "2026-11-02T06:54:18+00:00"
    }
  ]
}
```

---

## How I Used AI

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

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
