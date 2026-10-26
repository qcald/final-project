# Benchmark: gpt-6-luna

3 repeats per case. Intake: 4 sample chats (23 expected places, one deliberately messy). Answer: 4 questions against Maya's Lisbon places. Tokens are averages per call.

## Intake agent

| Reasoning effort | Places found | Right friend | Right sentiment | Extra places per chat | Injection obeyed | Personal details sent | Input tokens | Output tokens | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| low | 100% | 100% | 100% | 0.0 | 0 of 3 | 0 | 608 | 364 | 0.6 |
| medium | 100% | 100% | 100% | 0.0 | 0 of 3 | 0 | 608 | 528 | 0.7 |
| high | 100% | 100% | 100% | 0.0 | 0 of 3 | 0 | 608 | 558 | 1.2 |

### Intake agent on the messy chat only

| Reasoning effort | Places found | Right friend | Right sentiment | Right city | Extra places |
|---|---|---|---|---|---|
| low | 100% | 100% | 100% | 100% | 0.0 |
| medium | 100% | 100% | 100% | 100% | 0.0 |
| high | 100% | 100% | 100% | 100% | 0.0 |

## Answer agent

| Reasoning effort | Checks passed | Invented picks blocked | Sentences removed | Input tokens | Output tokens | Seconds |
|---|---|---|---|---|---|---|
| low | 12 of 12 | 0 | 0 | 777 | 188 | 0.2 |
| medium | 12 of 12 | 0 | 0 | 777 | 289 | 0.2 |
| high | 12 of 12 | 0 | 0 | 777 | 264 | 1.2 |

### Answer checks by question

| Check | low | medium | high |
|---|---|---|---|
| picks_only_categories | 3/3 | 3/3 | 3/3 |
| admits_gap | 3/3 | 3/3 | 3/3 |
| no_invented_places | 3/3 | 3/3 | 3/3 |
| respects_skip | 3/3 | 3/3 | 3/3 |
