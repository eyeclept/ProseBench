Apply the editing rule below to the passage. Apply only this rule. Leave all other text unchanged.

<rule>
{rule_text}
</rule>
{reference_block}{framing_addendum}
<passage>
{passage}
</passage>

Respond with one JSON object in this exact shape:
{"edits": [{"original": "<exact substring of the passage>", "replacement": "<new text>", "reason": "<one sentence>"}]}

- "original" must appear character-for-character in the passage. Make it just long enough to be unique.
- "replacement" is the text that takes the place of "original". Use "" to delete it.
- Set "replacement" to null to flag an instance for the author without changing it.
- Return {"edits": []} if the rule requires no change.
