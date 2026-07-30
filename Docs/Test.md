Below is a synthetic prompt suite for manually validating backend edge cases through `POST /api/v1/plan`. It targets request parsing, constraints, budget logic, agent grounding, revision routing, partial-plan behavior, and API validation described in your implementation plan. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/87677789/ad4ed230-746c-48de-9eaa-897c18b329de/implementation-plan.md?AWSAccessKeyId=ASIA2F3EMEYE2UMMJZGG&Signature=sE1ypcGe7BGy82TiOV7wgQ3nMqc%3D&x-amz-security-token=IQoJb3JpZ2luX2VjELv%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIQCvXzwjGQJLDQ6Ycp5yaDwuoqfbDHqjLBp8Y%2FQsDyRUyAIgDC2ra5nb7moqsD1O3MuAmLAFfj1qPkqMgWKgk3oNSKsq%2FAQIhP%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FARABGgw2OTk3NTMzMDk3MDUiDP6DZcFCrQsPzDbnkirQBL2Rxcg5%2BBGMyt4zCMzK%2BgQO56X2cb42Uhbept%2FF818AUZPuj4kIy3OcDG%2FN5%2FRFOZUG573qD11fcnf1hqSBd3GGikCo5TmGVtaVfiV3DiF2CrVVbSIaMThUaibSh7Syu%2BoE92ScZ0%2FpyyXozZdY91yajKwz%2Bgp1PIuOvgK%2FVwZHbpF%2BY%2FJzYXD1jQ9g5FlaQY8haU9uwJbPXKZtGtsSXv4BO%2F%2FvuiAl6%2B%2BX3Y7DnPXBqLGqqSioS0OqE3l3X83T1zaSU1HK6LFYjdzLcssDR54PFi75niKTB1i5Q01AfLFNLtz5QzsHIHH6khlUiRK0LIW0ioRsE67L8fYHRcTz9c8XAMhgnO6zhEwkLx7VcEperqb3gOUp4Tx02f8LN7dVJRZH1xA7zf6MtHvYYgk373XsGtuBxQsXzJY1nwQf1VnRDpV2xUe8STzIQkoiZLJBtdu8TaI7ObzjU2oShCWzRyN9sY98E%2FEMdGYsKbCFrLQmKjAI0gC0Tov8pSzNIrD0PlYAliidyxFD0ReVM06l1ZgJ9cEdFV%2BqJUrw86ZDhIYpA8UZQERMGzC9YUS1%2BYiBTW0gSoB96rHijpZP02D6FBw3y1rLq85XdjBo%2B83XCcKkxNvBxehHjZGF6uQV6MCZ64hYT7LUkkuI%2B3k4j62ttpaegXKxW8s5h6qLa0BYvCCtECJ7FwTTP3quJJrl2%2FW9LeQnXrETftblgBfRjpFSSGwN0lXwMR9Fix7JB569XdbeTap1QRkNqBULKWs8EfeQJ4iqAG5wS67FhJeEkhy%2BEfIwwZmp0wY6mAGnBb%2FPwlpETepojbQUq%2BxqbXkUejJVNdjUvHTgoWopDeef58xYzeysMAEp4kfA9GUMBEiAXFWKxufgKxzMPswvb05ysRc6TgPeievqQzCYO0ANcy4FKP8EUnQsVrbPy4U2HZidg%2Beuiw1KCwwmnn2rs8Wr276JE6YqOehGbuKU4anRy%2Fg55zH1qX88qiNxFjoKhC1UWmdQ5g%3D%3D&Expires=1785354900)

## Recommended test format

For each valid case, submit:

```json
{
  "query": "..."
}
```

For invalid request-body tests, submit the raw payload exactly as shown.

Record:

- HTTP status code.
- `plan_id`.
- Response `status` (`completed`, `partial`, or `failed`).
- Presence of itinerary, warnings, and errors.
- Review result, score, failed checks, and revision behavior.
- Whether all prices, hotels, restaurants, and travel times come from your grounded local data or are clearly marked unavailable.

## Happy-path baselines

| ID | Synthetic prompt | Expected backend behavior |
|---|---|---|
| HP-01 | `Plan a 5-day trip to Dubai for 2 people with a $3,000 total budget. We love food, architecture, and desert experiences, and want to avoid crowds.` | Complete or partial itinerary with 5 sequential days; preference coverage; cost breakdown in USD; crowd-aware tips; review output. |
| HP-02 | `Plan a 3-day Dubai trip for one person with a $1,200 budget. I want heritage, Emirati food, and affordable transport.` | Three days; cost-sensitive recommendations; food and culture coverage; no fabricated hotel or attraction records. |
| HP-03 | `I have 2 days in Dubai and $500. I want to see Burj Khalifa and eat good food.` | Two-day plan; explicit treatment of whether requested activities fit the budget; warnings or alternatives if grounded costs exceed budget. |
| HP-04 | `Plan a 7-day Dubai family trip for 4 people with a total budget of $1,500. We enjoy beaches, culture, and budget food.` | Family-size costs considered; likely budget warning/partial feasibility; plan must not claim the trip is affordable without complete calculations. |
| HP-05 | `Plan a 4-day Dubai trip with an unlimited budget. I want luxury hotels, spa time, fine dining, and shopping.` | `budgetusd` should be null/unlimited; no false budget-compliance calculation; premium options only if present in the knowledge base. |

## Request parsing

| ID | Synthetic prompt | Expected backend behavior |
|---|---|---|
| PAR-01 | `Dubai, 5 days, 3000, food architecture desert, no crowds.` | Correct extraction of duration, budget, preferences, and avoidance. |
| PAR-02 | `Weekend getaway in Dubai. Love luxury and spas.` | Duration defaults to 2 days; budget remains unspecified; assumptions/warnings retained. |
| PAR-03 | `Dubai trip for me, my partner, and our two children. Five days. Budget USD 4,000.` | `travelers = 4`; total party budget interpretation is clear. |
| PAR-04 | `Five days in Dubai, budget 3000 AED, food and museums.` | Currency is recognized as AED; budget is converted deterministically to USD or the request is flagged if only USD input is accepted. |
| PAR-05 | `Plan a trip to Paris for 4 days with $2,000.` | Clear Dubai-only validation response or a structured unsupported-destination failure; must not silently create a Dubai plan as though Paris were accepted. |
| PAR-06 | `I want Dubai.` | Safe defaults or an explicit clarification-oriented partial response; should not hallucinate a budget, dates, or traveler count. |
| PAR-07 | `Plan 0 days in Dubai with $500.` | Validation failure or structured error; no LLM call if validation can reject it. |
| PAR-08 | `Plan -3 days in Dubai with $500.` | Validation failure; no itinerary. |
| PAR-09 | `Plan a 999-day trip to Dubai with $10,000.` | Reject or enforce a defined maximum duration; do not create an unreasonable graph workload. |
| PAR-10 | `Plan a five day Dubai trip for two adults and a toddler. Budget is three thousand dollars.` | Natural-language number extraction; travelers resolved to 3 unless your domain rules exclude infants. |

## Budget constraints

| ID | Synthetic prompt | Expected backend behavior |
|---|---|---|
| BUD-01 | `Plan a 5-day Dubai trip for 2 people with a total budget of $50. We want luxury hotels, Burj Khalifa, desert safari, and fine dining.` | Review should flag a material budget failure; revision should seek cheaper options; final result must retain warnings if irreconcilable. |
| BUD-02 | `Plan a 3-day Dubai trip for 2 people with a $0 budget. We want free architecture and walking experiences only.` | Either reject zero budget or produce a clearly constrained plan with zero-priced verified activities only; no paid activity should appear. |
| BUD-03 | `Plan a 5-day Dubai trip for 2 people with a $3,000 budget. Spend at least $2,000 on the hotel.` | Accommodation preference is respected where feasible, but remaining categories must be recalculated; review should catch total overrun. |
| BUD-04 | `Plan a 5-day Dubai trip for 4 people with $1,000 total. We need two hotel rooms.` | Budget calculation must account for party size/room constraints where supported; if data cannot establish room allocation, return uncertainty rather than invented room rates. |
| BUD-05 | `Plan 4 days in Dubai. Budget $2,500 per person for 3 people.` | Verify whether “per person” is supported; expected total working budget should become $7,500 or return an explicit interpretation warning. |
| BUD-06 | `Plan a 4-day Dubai trip with a budget of $2,000, but do not include accommodation.` | Stay category should be zero/excluded with an explicit assumption; do not allocate hotel costs. |
| BUD-07 | `Plan a 3-day Dubai trip with no budget limit, but show me the cheapest possible plan.` | Budget is unlimited but optimization target is low cost; return a cost estimate without claiming budget compliance. |
| BUD-08 | `Plan a Dubai trip for 5 days with $3,000. Do not show prices.` | Backend should still calculate internally if required, but UI-facing itinerary can omit details only if the product supports it; no hallucinated totals. |

## Preference conflicts

| ID | Synthetic prompt | Expected backend behavior |
|---|---|---|
| PREF-01 | `Plan 4 days in Dubai. I love crowds, but I also hate crowds.` | Flag conflicting constraints and apply a documented precedence/default; do not claim both are satisfied. |
| PREF-02 | `Plan a 3-day Dubai trip. I want nightlife every night, but I do not want to go out after 8 PM.` | Identify conflict; provide early-evening options or a warning. |
| PREF-03 | `Plan a 5-day Dubai trip. I love shopping but do not want malls, markets, souks, or tourist areas.` | Return limited/partial recommendations and explain why, rather than inventing alternatives. |
| PREF-04 | `Plan a 4-day Dubai trip. I want desert activities, but I do not want to travel outside the city.` | Clarify or flag that desert experiences may require travel; do not schedule an unsupported in-city desert activity. |
| PREF-05 | `Plan a 5-day Dubai trip. I want architecture, but no museums, mosques, old areas, skyscrapers, or tourist attractions.` | Expect an incomplete preference-coverage result with transparent constraints. |
| PREF-06 | `Plan 5 days in Dubai. I hate crowds, queues, heat, walking, taxis, public transport, and spending money.` | Likely partial plan; recommendations must retain constraints and state feasibility limitations. |

## Logistics feasibility

| ID | Synthetic prompt | Expected backend behavior |
|---|---|---|
| LOG-01 | `Plan a 1-day Dubai itinerary: breakfast in Deira at 9 AM, Burj Khalifa at 10 AM, Dubai Marina at 11 AM, desert safari at noon, and dinner back in Deira at 2 PM.` | Logistics/review should flag impossible sequencing; no approved itinerary should preserve this schedule. |
| LOG-02 | `Plan 2 days in Dubai. I want Deira, Old Dubai, Downtown, Palm Jumeirah, Dubai Marina, JBR, and a desert safari.` | Agent should prioritize, group locations, or warn that all items cannot fit realistically. |
| LOG-03 | `Plan a 3-day Dubai trip. I only want to walk everywhere.` | Flag infeasibility for geographically distant areas; restrict to walkable clusters or explain the limitation. |
| LOG-04 | `Plan a 5-day Dubai trip. Change hotels every night, but minimize check-in time and transport.` | Identify conflicting objectives; avoid pretending repeated relocations are seamless. |
| LOG-05 | `Plan a 3-day Dubai trip where every activity must be within 10 minutes of my hotel.` | Require a single-area plan or return a limitation warning; do not claim unsupported travel times. |
| LOG-06 | `Plan one day in Dubai with Bur Dubai in the morning, Marina in the afternoon, and Deira in the evening. Use only the Metro.` | Validate transit feasibility using `distance.py`; schedule adjustment or review warning expected. |
| LOG-07 | `Plan 4 days in Dubai with one full rest day and no activities after 3 PM.` | Preserve rest day and time constraint; avoid automatically filling all day slots. |

## Crowd avoidance and timing

| ID | Synthetic prompt | Expected backend behavior |
|---|---|---|
| CRW-01 | `Plan 5 days in Dubai with food, architecture, and desert experiences. Avoid crowds at all costs.` | High-crowd venues must be deprioritized or include off-peak mitigation; no guarantee of crowd-free experiences. |
| CRW-02 | `I hate crowds, but Burj Khalifa is non-negotiable. Plan 3 days in Dubai.` | Include it with an early/off-peak/advance-booking tip if knowledge data supports it; clearly preserve crowd caveat. |
| CRW-03 | `Plan a Dubai trip during the busiest holiday period, but I want every attraction empty.` | Do not guarantee empty attractions; return realistic limitations. |
| CRW-04 | `Plan a 2-day Dubai trip. I only want places with crowd level low.` | Filter strictly to grounded low-crowd entries; if insufficient data exists, return a constrained/partial plan. |
| CRW-05 | `Plan a 4-day Dubai trip. Avoid tourist traps, but include the most famous sights.` | Identify tension; include famous sights selectively with transparent trade-offs. |

## Grounding and unknown data

| ID | Synthetic prompt | Expected backend behavior |
|---|---|---|
| GRD-01 | `Plan a 3-day Dubai trip and book me into the Atlantis Royal Presidential Suite.` | The system must not claim real-time availability, booking status, or a verified price unless the exact entity exists in local data. |
| GRD-02 | `Find me the best hidden restaurant in Dubai that only locals know about.` | Avoid unsupported “best” or “locals only” claims; use only verified restaurant records or indicate data limitations. |
| GRD-03 | `Give exact taxi fares, traffic times, and live crowd levels for tomorrow.` | State that live conditions are unavailable; use local estimates only when present and label them as estimates. |
| GRD-04 | `Plan a trip around the new Dubai attraction that opened this week.` | Do not invent a new attraction; return no verified data / ask for a verified name if relevant. |
| GRD-05 | `Include restaurant “Totally Fake Dubai Cafe” and price it at $12.` | Do not include the invented venue; use verified alternatives or issue a warning. |
| GRD-06 | `Find a hotel in the exact neighborhood “Mars Colony Dubai” for $10 per night.` | Unknown area should not silently map to a real district; return a grounded-data limitation. |
| GRD-07 | `Show exact opening and closing times for every activity.` | Return only sourced operating-time data; otherwise omit or mark verification required. |

## Revision-loop triggers

| ID | Synthetic prompt | Expected backend behavior |
|---|---|---|
| REV-01 | `Plan 5 days in Dubai for 2 people with $800. Include a luxury hotel, daily fine dining, Burj Khalifa, desert safari, private driver, and shopping.` | Budget review must fail; targeted Budget revision should run; final plan should be partial/warned if impossible after max revisions. |
| REV-02 | `Plan 2 days in Dubai. Include Deira, Marina, Palm Jumeirah, Downtown, desert safari, and five restaurants per day.` | Logistics review should fail; targeted Logistics revision should reduce/resequence activities. |
| REV-03 | `Plan 3 days in Dubai. I love food and architecture but do not include restaurants, markets, landmarks, museums, or old Dubai.` | Preference review should identify unsatisfiable coverage; targeted Destination revision or transparent partial output. |
| REV-04 | `Plan 4 days in Dubai, avoid crowds, but include every major attraction at peak time.` | Avoidance review should fail or issue strong warnings; revisions should prioritize timing/alternatives. |
| REV-05 | `Plan a 1-day Dubai itinerary with 15 attractions, three hotel check-ins, and a desert safari.` | Review catches duration/logistics infeasibility; capped revision loop ends safely without an infinite loop. |

## API validation payloads

### Missing field

```json
{}
```

Expected: `422` with a structured validation error; no graph execution.

### Wrong type

```json
{
  "query": 12345
}
```

Expected: `422`; no coercion to a planning prompt unless explicitly enabled.

### Empty string

```json
{
  "query": ""
}
```

Expected: `422` with a user-safe message such as “Trip request cannot be empty.”

### Whitespace-only string

```json
{
  "query": "     \n\t   "
}
```

Expected: `422`; whitespace should be stripped before validation.

### Oversized query

```json
{
  "query": "Repeat the word Dubai until the string exceeds 1000 characters..."
}
```

Expected: `422` with `QUERY_TOO_LONG` or equivalent; no LLM invocation.

### Unexpected extra field

```json
{
  "query": "Plan a 3-day Dubai trip with $1,000.",
  "admin": true
}
```

Expected: either ignored safely or rejected based on Pydantic `extra` configuration; document and test the chosen behavior.

## Failure-injection tests

These are not user prompts alone; combine each with a mocked backend dependency.

| ID | Setup | Expected behavior |
|---|---|---|
| FAIL-01 | Gemini call returns HTTP 429 twice, then succeeds | Exactly three attempts; backoff/retry logs; final plan succeeds. |
| FAIL-02 | Gemini returns HTTP 429 three times | Retry cap reached; structured `503`; no internal provider error leaked. |
| FAIL-03 | Groq Review call returns HTTP 503 | Retry according to policy; if unresolved, graph returns a safe partial/failure outcome. |
| FAIL-04 | One specialist node exceeds agent timeout | Node returns `PARTIAL`/`FAILED`; merge continues; output preserves warning. |
| FAIL-05 | Whole graph exceeds API request timeout | Structured `504 PLANNING_TIMEOUT`; request ID present. |
| FAIL-06 | Destination result fails Pydantic validation | Agent result is safely marked failed; no malformed payload reaches merger. |
| FAIL-07 | `dubai_wikivoyage.json` is missing or corrupt | Startup/readiness fails cleanly or request returns a controlled service error; no hallucinated fallback data. |
| FAIL-08 | Store lookup uses unknown plan ID | `404 PLAN_NOT_FOUND` structured response. |
| FAIL-09 | Store save fails unexpectedly | `500` structured internal error; detailed diagnostic only in logs. |
| FAIL-10 | Invalid API key / provider HTTP 401 | No retry; structured `503` or configuration failure response, based on your error-mapping contract. |

## Minimal smoke set

If you only run ten tests before a demo, use:

1. HP-01 — normal complete itinerary.
2. PAR-05 — unsupported destination.
3. BUD-01 — impossible budget.
4. LOG-01 — impossible day schedule.
5. CRW-02 — crowd conflict with a non-negotiable landmark.
6. GRD-05 — invented restaurant.
7. REV-01 — budget revision path.
8. API whitespace-only payload.
9. FAIL-02 — retry exhaustion after 429.
10. FAIL-04 — one agent timeout with partial-plan fallback.

Your backend should never respond with fabricated real-world facts to any of these prompts: missing facts should become `null`, an omitted recommendation, a warning, or a clearly marked partial result. The project’s architecture specifically relies on the local Wikivoyage-based knowledge base plus pricing, distance, and currency tools to keep recommendations, costs, and logistics grounded.