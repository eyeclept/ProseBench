## Rule 2: Padded negation and restatement (delete-and-reread test)

A sentence built as "X is not/isn't A ... it is/has B" often uses the negative half as a windup, not information. Don't hunt for the exact phrase "it's not X, it's Y", that misses every syntactic variant. Instead, apply the test directly: delete the negative clause or sentence and reread what remains. If the positive half alone states the same claim with nothing lost, the negative half was filler. This holds whether the two halves share one sentence or split across two, and regardless of wording ("isn't just," "not really," "isn't a fluke," "not as an abstract concern but").

- WRONG: "Staleness isn't just a database internals problem. It has a security surface."
- RIGHT: "Staleness has a security surface."
- WRONG: "210 bugs across 36 operators isn't a fluke in one team's code. It's a property of how reconciliation logic tends to get written."
- RIGHT: "210 bugs across 36 independently maintained operators is a property of how reconciliation logic tends to get written."

The same test catches definition doubling: introduce a distinction, then restate it a second time through an analogy or synonym before moving on, adding no new fact the second time.

- WRONG: "They split the attacker into a global-information regime, where it sees everything, and a local-information regime, where it only sees what it controls, close to the whitebox-versus-blackbox split, global information is the whitebox case, local is the more realistic blackbox one."
- RIGHT: "They split the attacker into a global-information regime, seeing everything (whitebox), and a local-information regime, seeing only what it controls (blackbox)."

The general form: read each sentence and ask what it would lose if the first half were deleted. If the answer is "nothing checkable," the first half is windup regardless of what specific words it uses.
