# Token-efficient book workflow

This repository is a 22-chapter technical book with optional executable labs. Optimize for the quality of the book's explanations, conceptual structure, and reader experience. Labs support the text; they do not define the editorial workflow.

## Scope editorial work

- Keep each edit attributable to one chapter or one named cross-chapter quality gate, but do not stop merely because one chapter is complete.
- When the user authorizes continued review, a chapter range, or the remaining known issues, proceed through an explicit editorial queue in the same task. Preserve clear per-chapter diffs; one chapter may still be one commit, but acceptance and commits are not mandatory pause points.
- Cross-chapter terminology, reading routes, references, licensing, navigation, and publication structure may be edited together when a single quality gate requires consistent changes across several files.
- Do not turn continued review into indiscriminate rewriting. Use the manifest, handoff, reader feedback, and existing audits as indexes; inspect the current text before accepting an old finding.
- A Goal is allowed only when the user explicitly requests it and its completion condition names a bounded chapter range or quality gate. An editorial queue may contain several bounded items and continue until the queue is complete or context requires a handoff.
- Do not repeat a whole-book audit after every local change.

## Minimal context startup

Read only:

1. `BOOK_HANDOFF.md`;
2. the target entry in `specs/book-manifest.json`;
3. the target chapter or lab files;
4. only the directly relevant spec or test.

Do not preload `docs/status.md`, every chapter, all reviews, all experiment cards, or long session history. Search for a precise symbol, claim ID, chapter number, or path before opening files. Read focused ranges instead of entire long files. Do not re-read unchanged files in the same task.

## Execution and output budget

- Plan the exact files before editing and prefer one coherent patch.
- Default to no subagents and no web research. Use them only when the bounded task requires independent work or current external evidence.
- Keep command output small: use quiet modes, focused tests, or redirect verbose output to a log and show at most the final 80 relevant lines.
- Never place full Docker/build/test logs in chat. Report the command, exit status, and concise failure excerpt.
- Run the narrowest relevant check first. Batch documentation checks at a coherent editorial milestone instead of forcing a build and commit after every chapter. Run `make check`, `make smoke-all`, Docker rebuilds, or site-wide review only for an explicit release milestone or user request.
- Do not rerun a passing check unless inputs affecting it changed.

## Evidence boundaries

- Preserve the repository distinction between `reviewed`, `smoke`, and `reproducible`.
- Never turn paper results, smoke fixtures, submitted jobs, or unrun GPU paths into book-measured evidence.
- When changing a chapter status, update `specs/book-manifest.json`; do not weaken schemas or gates to make a check pass.

## Session boundary

- If continued review is authorized, proceed from one bounded queue item to the next without asking the user to repeat “continue”.
- If no continuation or range was authorized, stop when the named item is complete; do not invent a new broad audit.
- If context reaches roughly 60%, finish the current atomic edit, update `BOOK_HANDOFF.md`, and recommend a fresh task (`/new`) using that handoff rather than beginning another large queue item.
- Use `/compact` only to finish the current bounded task, not to prolong a multi-chapter session.
- Keep `BOOK_HANDOFF.md` under 25 lines and overwrite stale state instead of appending history. Record only target, changed files, checks/evidence, blockers, and the exact next action.

## Automatic chapter relay

Use the relay only when `BOOK_QUEUE.md` says `enabled: true` and names an exact current target, next target, and acceptance command. This file is the dispatch authority; chat history is not.

1. Set the current item to `active` before editing. Work only on that item.
2. Run its named acceptance command. A failed or unrun check cannot advance the queue.
3. Update `BOOK_HANDOFF.md` with compact evidence and the exact next target.
4. If there is no next target, set queue status to `complete` and stop.
5. Before creating a successor task, set status to `dispatching`. Then create exactly one new Codex task in the same saved project's `local` checkout, with a prompt containing the next target, allowed scope, acceptance command, and this relay protocol.
6. After confirmed creation, record the returned task ID, set status to `dispatched`, and end the current task immediately. Do not wait for or monitor the successor.

Safety rules:

- Never dispatch while another chapter task is active in the same checkout.
- Never commit, push, publish, or broaden permissions merely to support relay.
- If creation fails or its result is ambiguous after status became `dispatching`, set status to `blocked` and stop. Never retry automatically; this prevents duplicate successors.
- If a resumed task sees `dispatching`, `dispatched`, `blocked`, or a non-empty successor task ID, it must not create another successor.
- A successor may continue the relay only because its prompt explicitly carries the user's relay authorization. Otherwise keep relay disabled.
