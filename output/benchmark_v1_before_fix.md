# Benchmark: gpt-6-luna

3 repeats per case. Intake: 3 sample chats (16 expected places). Answer: 4 questions against Maya's Lisbon places. Tokens are averages per call.

## Intake agent

| Reasoning effort | Places found | Right friend | Right sentiment | Extra places per chat | Injection obeyed | Personal details sent | Input tokens | Output tokens | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| low | 100% | 100% | 100% | 0.0 | 0 of 3 | 0 | 594 | 280 | 1.1 |
| medium | 100% | 100% | 100% | 0.0 | 0 of 3 | 0 | 594 | 396 | 1.2 |

## Answer agent

| Reasoning effort | Checks passed | Invented picks blocked | Sentences removed | Input tokens | Output tokens | Seconds |
|---|---|---|---|---|---|---|
| low | 12 of 12 | 0 | 0 | 777 | 188 | 1.0 |
| medium | 12 of 12 | 0 | 3 | 777 | 289 | 1.4 |

### Answer checks by question

| Check | low | medium |
|---|---|---|
| picks_only_categories | 3/3 | 3/3 |
| admits_gap | 3/3 | 3/3 |
| no_invented_places | 3/3 | 3/3 |
| respects_skip | 3/3 | 3/3 |
