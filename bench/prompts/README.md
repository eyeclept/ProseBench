# Prompt fill rules

- `{rule_text}`: contents of `bench/rules/rule{N}.md`.
- `{reference_block}`: rule 1 only. The text `\n<reference name="banned-words-phrases.md">\n` + contents of `bench/rules/banned-words-phrases.md` + `\n</reference>\n`. Empty string for rules 2-5.
- `{framing_addendum}`: rule 3 `easy` framing only. Contents of `rule3_easy_addendum.md`. Empty string otherwise. The `verbatim` framing relies on the escalation sentence already in `rule3.md`.
- `{passage}`: contents of `bench/corpus/out/P{n}/injected.md`.
- System prompt: `system.md`, identical for every model.
