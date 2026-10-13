# Banned Words and Phrases

The single file to edit to change what's banned; `SKILL.md` and `ai-writing-detection.md` both point here instead of listing words themselves. Many of these are words in ordinary use well before "AI slop" became a category, so tune freely rather than treating the list as fixed.

Three tiers, by strictness:

- **NEVER**: zero tolerance, no context excuses it.
- **Only when necessary**: allowed when the plain alternative would be less accurate or the context genuinely calls for it; default to avoiding.
- **Prefer other words**: default to the alternative; the left-hand word isn't a hard violation if it's genuinely the most precise term, but that should be rare.

## NEVER

- Characters outside a standard US keyboard: em dashes, en dashes, curly/smart quotes, ellipsis glyphs. Replace with the ASCII equivalent (semicolon, period, comma, or restructure for an em dash; a hyphen for an en dash; a straight `'`/`"` for a curly quote; three periods for an ellipsis). Exempt: a foreign word or proper name that is only correctly spelled with a diacritic or non-Latin letter (café, naïve) keeps it. Em dashes remain the single most reliable AI-writing tell.
- Hallucinated markup artifacts: `oaicite`, `contentReference`, `grok_card`, `attributableIndex`, `turn0search0`. Presence of any of these means the text was pasted from an AI tool without editing.
- Scare quotes on normal (non-quoted) words.
- Parenthetical clarifications in headings.

## Only when necessary

- **Hedging markers:** may, might, could, potentially, probably, generally, usually, arguably, likely, "I think", "I believe", "it seems", "it appears", "unclear", "remains to be seen", "further research is needed". Fine when discussing genuinely pending legislation, ongoing litigation, or disputed facts. A blanket default of hedging on established facts is the violation. Threshold: more than 3 hedges in one paragraph, or more than 8 per 1,000 words in a declarative section (background, history, timeline), is a red flag.
- **Metaphorical-vs-literal nouns:** ecosystem, landscape, navigate, tapestry, symphony, beacon, testament, realm. Fine in literal use ("Arizona landscape", "lighthouse beacon", "last will and testament"). Banned only in the inflated-metaphor use ("the regulatory landscape", "a beacon of hope", "a testament to innovation").
- Text inside direct quotes, titles, verbatim source values, or code/config examples is exempt from every list on this page. These bans apply to your own prose, not material you're citing or reproducing.

## Prefer other words

No suggested replacements below; pick a natural alternative in context rather than mechanically swapping in a provided synonym.

**Verbs:** delve (into), leverage, utilize/utilise, facilitate, foster, bolster, underscore, unveil, navigate (metaphorical use), streamline, enhance, endeavour, ascertain, elucidate.

**Adjectives and intensifiers:** robust, comprehensive, pivotal, crucial, vital, transformative, cutting-edge, groundbreaking, innovative, seamless, intricate, nuanced, multifaceted, holistic, extremely, dramatically, exceptionally, significantly, incredibly, remarkably, truly, absolutely, literally, quite, really, very, surely, certainly, clearly, definitely, essentially, fundamentally, interestingly, naturally, obviously, undoubtedly, ultimately, basically, actually.

**Weasel constructions:** helps ensure, may be able to, can potentially.

**Transitions and connectors:** furthermore, moreover, notwithstanding, that being said, at its core, to put it simply, it's worth mentioning that, in the realm of, in the landscape of, in today's [anything].

**Opening, filler, and concluding phrases:** "in today's fast-paced world", "in today's digital age", "in an era of", "in the ever-evolving landscape of", "it's important to note that", "let's delve into", "imagine a world where", "with that in mind", "this begs the question", "in conclusion", "to sum up", "in the final analysis", "all things considered", "at the end of the day", "by [doing X], you can [achieve Y]", "look no further", "our team of experts".

**Academic tells:** shed light on, pave the way for, a plethora of, paramount, prior to, subsequent to, in light of, in terms of, the fact that.

**Structural phrasing** (restructure rather than reach for these): "Whether you're a [X], [Y], or [Z]..."; "It's not just [X], it's also [Y]"; "It's not X, it's Y" / "It's not about X, it's about Y" (more than two per 500 words is a high-confidence AI tell); starting a sentence with "By [gerund]..."; "Think of [X] as [elaborate metaphor]"; rhetorical colon abuse ("Here's the thing:", "The bottom line:").

**Inflated-symbolism phrases** (2025-2026 corpus-frequency AI tells; hundreds of times more common in AI text than in human baselines): "provide a valuable insight", "left an indelible mark", "play a significant role in shaping", "an unwavering commitment", "open a new avenue", "a stark reminder", "gain a comprehensive understanding", "serves as a testament", "watershed moment", "deeply rooted".
