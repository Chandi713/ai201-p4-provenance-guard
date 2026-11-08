# Attack run — before

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-08 01:03
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **56**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `d51dcb6d-9968-4d5c-a5a6-a390471f37fd` | human | 0.164 |  |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `9cd25fd0-17ed-46c4-9ac4-6ea187e21fff` | unsure | 0.594 |  |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `d700be61-ae76-4bd9-a451-14dcfe5e2847` | unsure | 0.666 |  |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `a569df10-ae78-4c53-9bda-5ea915e62e82` | ai | 0.968 |  |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `2323ebff-0fe6-4f55-b8bb-dcb8bf0eff88` | human | 0.321 |  |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `9d39d50b-7562-47ce-9099-464c36647fab` | unsure | 0.576 |  |
| EV07 | evasion | signal two: padding with punctuation | 200 | `1adf7575-4cd0-4fbf-af84-bc1c1989ca50` | unsure | 0.600 |  |
| EV08 | evasion | signal one: text below the token window | 400 | `—` | — | — |  |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `9f4d2bf6-47a6-447d-8d36-82180c89215c` | unsure | 0.704 |  |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `9654892f-6a1b-4e5d-87a1-fb810a80eb0d` | ai | 0.979 |  |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `58422c00-be27-4a75-9d7f-200ea95d0c99` | human | 0.200 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `d00c4180-d481-4dff-ac07-53178cec6884` | unsure | 0.739 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `3b50d213-2237-4a64-a479-eda148d2d771` | human | 0.362 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `f6c9fecd-db72-4238-b56c-d006c42482b4` | unsure | 0.591 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `e3753df3-6684-41ea-bee2-6c0bf1d38bc3` | unsure | 0.531 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `5480a0c5-e1b4-4b55-b1e9-fb4793cc54c0` | human | 0.284 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `10e436ae-7963-4b98-ac15-e72e9d5e6cc5` | human | 0.308 |  |
| FP08 | false_positive | very short genuine human submission | 400 | `—` | — | — |  |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `86fd3e8e-9b8a-46de-93f6-2fadeb1a37c1` | human | 0.463 |  |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `6ecf3b46-8084-435e-a180-36cf3211d8bd` | human | 0.204 |  |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `4ad6481f-3801-4115-8aac-406473616cb4` | unsure | 0.594 |  |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `01177169-c64b-4e81-9b5c-e0ea426fcf86` | human | 0.500 |  |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `6d1054ad-d7dc-4a88-b054-ef5b0b836f01` | human | 0.307 |  |
| PI06 | prompt_injection | instruction plus real human text | 200 | `677a8adc-83f4-46a7-8ada-0c746fa7a99c` | human | 0.236 |  |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — |  |
| MF02 | malformed | text is a single character | 400 | `—` | — | — |  |
| MF03 | malformed | text is control characters | 400 | `—` | — | — |  |
| MF04 | malformed | text is only punctuation | 400 | `—` | — | — |  |
| MF05 | malformed | text is a very long single word | 400 | `—` | — | — |  |
| MF06 | malformed | text is emoji only | 400 | `—` | — | — |  |
| MF07 | malformed | text is right-to-left script | 400 | `—` | — | — |  |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — |  |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — |  |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — |  |
| RQ03 | malformed | text is a number | 400 | `—` | — | — |  |
| RQ04 | malformed | text is a list | 400 | `—` | — | — |  |
| RQ05 | malformed | text is null | 400 | `—` | — | — |  |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — |  |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — |  |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — |  |
| RQ09 | malformed | body is empty | 400 | `—` | — | — |  |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | `—` | — | — |  |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | `—` | — | — |  |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — |  |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 0 | 20 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "d51dcb6d-9968-4d5c-a5a6-a390471f37fd",
  "creator_id": "attacker_EV01",
  "guess": "human",
  "confidence": 0.1635,
  "model_score": 0.1635,
  "style_score": 0.9857,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "9cd25fd0-17ed-46c4-9ac4-6ea187e21fff",
  "creator_id": "attacker_EV02",
  "guess": "unsure",
  "confidence": 0.5943,
  "model_score": 0.5943,
  "style_score": 0.5077,
  "label": "We can't tell with confidence whether this was written by a person or with AI, so we haven't labelled it either way.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "d700be61-ae76-4bd9-a451-14dcfe5e2847",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.6662,
  "model_score": 0.6662,
  "style_score": 0.5361,
  "label": "We can't tell with confidence whether this was written by a person or with AI, so we haven't labelled it either way.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "a569df10-ae78-4c53-9bda-5ea915e62e82",
  "creator_id": "attacker_EV04",
  "guess": "ai",
  "confidence": 0.968,
  "model_score": 0.6114,
  "style_score": 0.968,
  "label": "Our checks found patterns often seen in AI-generated writing, such as very predictable word choices and evenly sized sentences. This doesn't prove it wasn't written by you. If you wrote it yourself, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "2323ebff-0fe6-4f55-b8bb-dcb8bf0eff88",
  "creator_id": "attacker_EV05",
  "guess": "human",
  "confidence": 0.3212,
  "model_score": 0.3212,
  "style_score": 0.2355,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "9d39d50b-7562-47ce-9099-464c36647fab",
  "creator_id": "attacker_EV06",
  "guess": "unsure",
  "confidence": 0.5761,
  "model_score": 0.5727,
  "style_score": 0.5761,
  "label": "We can't tell with confidence whether this was written by a person or with AI, so we haven't labelled it either way.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "1adf7575-4cd0-4fbf-af84-bc1c1989ca50",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.5862,
  "style_score": 0.6,
  "label": "We can't tell with confidence whether this was written by a person or with AI, so we haven't labelled it either way.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_EV08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "9f4d2bf6-47a6-447d-8d36-82180c89215c",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.7042,
  "model_score": 0.7042,
  "style_score": 0.6,
  "label": "We can't tell with confidence whether this was written by a person or with AI, so we haven't labelled it either way.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "9654892f-6a1b-4e5d-87a1-fb810a80eb0d",
  "creator_id": "attacker_EV10",
  "guess": "ai",
  "confidence": 0.9792,
  "model_score": 0.9792,
  "style_score": 0.6594,
  "label": "Our checks found patterns often seen in AI-generated writing, such as very predictable word choices and evenly sized sentences. This doesn't prove it wasn't written by you. If you wrote it yourself, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "58422c00-be27-4a75-9d7f-200ea95d0c99",
  "creator_id": "attacker_FP01",
  "guess": "human",
  "confidence": 0.2,
  "model_score": 0.6175,
  "style_score": 0.2,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "d00c4180-d481-4dff-ac07-53178cec6884",
  "creator_id": "attacker_FP02",
  "guess": "unsure",
  "confidence": 0.7387,
  "model_score": 0.7387,
  "style_score": 0.7164,
  "label": "We can't tell with confidence whether this was written by a person or with AI, so we haven't labelled it either way.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "3b50d213-2237-4a64-a479-eda148d2d771",
  "creator_id": "attacker_FP03",
  "guess": "human",
  "confidence": 0.3624,
  "model_score": 0.8051,
  "style_score": 0.3624,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "f6c9fecd-db72-4238-b56c-d006c42482b4",
  "creator_id": "attacker_FP04",
  "guess": "unsure",
  "confidence": 0.5905,
  "model_score": 0.8329,
  "style_score": 0.5905,
  "label": "We can't tell with confidence whether this was written by a person or with AI, so we haven't labelled it either way.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "e3753df3-6684-41ea-bee2-6c0bf1d38bc3",
  "creator_id": "attacker_FP05",
  "guess": "unsure",
  "confidence": 0.5308,
  "model_score": 0.8005,
  "style_score": 0.5308,
  "label": "We can't tell with confidence whether this was written by a person or with AI, so we haven't labelled it either way.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "5480a0c5-e1b4-4b55-b1e9-fb4793cc54c0",
  "creator_id": "attacker_FP06",
  "guess": "human",
  "confidence": 0.2844,
  "model_score": 0.8814,
  "style_score": 0.2844,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "10e436ae-7963-4b98-ac15-e72e9d5e6cc5",
  "creator_id": "attacker_FP07",
  "guess": "human",
  "confidence": 0.3085,
  "model_score": 0.8816,
  "style_score": 0.3085,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_FP08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "86fd3e8e-9b8a-46de-93f6-2fadeb1a37c1",
  "creator_id": "attacker_PI01",
  "guess": "human",
  "confidence": 0.4625,
  "model_score": 0.4625,
  "style_score": 0.6,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "6ecf3b46-8084-435e-a180-36cf3211d8bd",
  "creator_id": "attacker_PI02",
  "guess": "human",
  "confidence": 0.2044,
  "model_score": 0.2044,
  "style_score": 0.5333,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "4ad6481f-3801-4115-8aac-406473616cb4",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.5943,
  "model_score": 0.5943,
  "style_score": 0.488,
  "label": "We can't tell with confidence whether this was written by a person or with AI, so we haven't labelled it either way.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "01177169-c64b-4e81-9b5c-e0ea426fcf86",
  "creator_id": "attacker_PI04",
  "guess": "human",
  "confidence": 0.4998,
  "model_score": 0.4998,
  "style_score": 0.1103,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "6d1054ad-d7dc-4a88-b054-ef5b0b836f01",
  "creator_id": "attacker_PI05",
  "guess": "human",
  "confidence": 0.3067,
  "model_score": 0.6401,
  "style_score": 0.3067,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "677a8adc-83f4-46a7-8ada-0c746fa7a99c",
  "creator_id": "attacker_PI06",
  "guess": "human",
  "confidence": 0.2362,
  "model_score": 0.5583,
  "style_score": 0.2362,
  "label": "Our checks suggest this was written by a person.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF06",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF07",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 413,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
