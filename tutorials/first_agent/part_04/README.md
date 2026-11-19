# Part 4: Ask Before Acting

Preview an email draft and require approval before saving it locally.

## Follow the code

1. Offer two tools: the read-only `search_notes` and `save_email_draft`.
2. Search notes as before. When a draft is requested, validate its `to`, `subject` and `body` fields.
3. Create a frozen `EmailDraft` object. Show its exact JSON, escaping control characters.
4. Ask for an explicit `yes` within 30 seconds or the remaining overall time, whichever is smaller. Other answers or closed input count as no. A timeout stops with `deadline` and saves nothing.
5. On no, return `{"approved": false, "saved": false}` to the model. The model explains it to the user.
6. On yes, check the deadline again, then save that same immutable object. Only this step creates or appends the outbox file. A repeated identical draft in the same run is rejected.

## Run from the repository root

```sh
make run-python SERIES=first_agent PART=04
# Choose a separate practice outbox:
make run-python SERIES=first_agent PART=04 ARGS='--outbox .local/practice/outbox.jsonl'
```

Inspect the recipient, subject and body. Type `yes` to save or `no` to decline.
When answered within the budgets, both answers return `final_answer` after three model steps and two tool calls.
With `yes`, the answer says the draft was saved. With `no`, the model answers
“You did not approve the draft, so I did not save it.” and no outbox is created.

The default destination is root `.local/first-agent/outbox.jsonl`. Each approved
run appends one JSON line marked `simulated: true`. **No email is sent**, including
with `--live`. This is a local draft exercise. The model does not choose the file
path; the application does. A new run can save another copy after fresh approval.
An interrupted or failed write needs manual inspection before retrying.

## Use a real model

```sh
make run-python SERIES=first_agent PART=04 ARGS='--live'
```

Configure the root `.env` as described in the [series guide](../README.md).
Use `--question 'your question'` to change the live request. `--query` only changes
the simulated model's first search word. Live requests may spend credits.
**Live model verification has not been run.** SDK behavior is tested with HTTP
fixtures; no successful live-model behavior is claimed.

## Check

```sh
uv run --locked pytest tests/first_agent
```

See the [series guide](../README.md#verification) for the full verification commands.

[All five parts](../README.md)
