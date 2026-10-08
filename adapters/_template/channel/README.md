# Channel (template)

Two things live here, both optional.

## Metadata assistant

A script that asks your internal data-catalog bot a factual question and prints its reply (`adapter.json → channel.metadata_assistant`). The workflow calls it at discovery level 3 and treats the answer as an external claim to be verified by a probe. Interface: `script "<question>"` → reply text on stdout, exit 0; exit 2 on timeout.

## Q&A channel operations (for `qa-followup`)

The agent names four operations; write the concrete commands for your chat tool here:

| Operation | Command |
|---|---|
| `ack(thread)` | |
| `reply_in_thread(root_message_id, text)` | |
| `dm_owner(text)` | |
| `read_document(url)` | |

The daemon that starts `qa-followup` sessions (polling, one session per channel, bindings, guardrails) lives outside the harness.

## Secrets

Chat ids, bot ids, app ids, endpoints: read from the environment variables listed in `adapter.json → channel.secrets_env`, or from `channel/secrets.json` which is git-ignored. Never in tracked files.
