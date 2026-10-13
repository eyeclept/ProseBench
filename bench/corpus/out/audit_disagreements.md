# Answer-key audit disagreements

Auditor: openai/gpt-6.1-sol. Fill the `decision` column of `audit_decisions.csv` with keep, accept, or drop.
`accept` applies the auditor's correction (or adds a MISSED row); `drop` removes the key row; `keep` or blank leaves the key unchanged. `suggested` is the orchestrator's triage, not a decision.

## P1 R1 DISPUTE (suggested: review)

Target: `The Expanding Threat Landscape`

Key: technical_term / keep / keep

Auditor: no_fact / change / cut

Reason: The heading uses landscape metaphorically.

## P1 R1 DISPUTE (suggested: review)

Target: `The rapidly evolving threat landscape`

Key: technical_term / keep / keep

Auditor: no_fact / change / cut

Reason: Threat landscape remains a metaphor in this sentence.

## P1 R1 DISPUTE (suggested: review)

Target: `the contemporary threat landscape`

Key: technical_term / keep / keep

Auditor: no_fact / change / cut

Reason: Landscape is metaphorical here, not a necessary literal or technical noun.

## P1 R1 MISSED (suggested: review)

Target: `a significantly tighter incident-reporting clock`

Key:  /  / 

Auditor: no_fact / change / cut

Reason: The planted Rule 5 row misses significantly under the Rule 1 list as well. [target occurs 0 times in essay]

## P1 R1 MISSED (suggested: review)

Target: `“attack surfaces”`

Key:  /  / 

Auditor: scare_quotes / change / cut

Reason: These are quotation marks around an ordinary technical term, not a sourced quotation. The key covers typography and dramatically but misses the unnecessary quoting.

## P1 R1 MISSED (suggested: review)

Target: `“availability heuristic,”`

Key:  /  / 

Auditor: scare_quotes / change / cut

Reason: The name of the cognitive bias is unnecessarily quoted; this is separate from the curly-character violation.

## P1 R1 MISSED (suggested: review)

Target: `“bug bounty”`

Key:  /  / 

Auditor: scare_quotes / change / cut

Reason: The normal technical term is unnecessarily quoted; the key only covers its curly characters.

## P1 R1 MISSED (suggested: review)

Target: `“trusted internal network”`

Key:  /  / 

Auditor: scare_quotes / change / cut

Reason: The prose quotes a normal descriptive label without attributing a quotation.

## P1 R2 DISPUTE (suggested: review)

Target: `Beyond compliance,`

Key: windup / change / cut

Auditor: not_an_instance / keep / keep

Reason: Beyond compliance distinguishes ethical concerns from the preceding legal requirements; deletion loses that relationship.

## P1 R2 DISPUTE (suggested: review)

Target: `moving away from the outdated “trusted internal network” paradigm`

Key: doubling / change / cut

Auditor: not_an_instance / keep / keep

Reason: The trailer supplies the distinct prior trust model; it does not repeat a definition or analogy already given.

## P1 R2 DISPUTE (suggested: review)

Target: `organizations transform cybersecurity from a cost center into a strategic asset that safeguards reputation and competitive advantage`

Key: doubling / change / cut

Auditor: not_an_instance / keep / keep

Reason: The cost-center-to-asset claim is not a second definition or synonymous restatement of the preceding KPI actions.

## P1 R4 DISPUTE (suggested: accept)

Target: ` Union’s Cybe`

Key: other / change / ascii_equivalent

Auditor: curly_quote /  / punct_straight_quote

Reason: The actual offending character is a curly apostrophe.

## P1 R4 DISPUTE (suggested: accept)

Target: `**AI‑Enhanced Threat Intelligence** – Leverage federated learning`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / 

Reason: The en dash is a separator, not a range.

## P1 R4 DISPUTE (suggested: accept)

Target: `**Post‑Quantum Preparedness** – Begin migrating critical systems`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / 

Reason: The en dash is a separator, not a range.

## P1 R4 DISPUTE (suggested: accept)

Target: `**Resilience Engineering** – Focus on rapid recovery capabilities`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / 

Reason: The en dash is a separator, not a range.

## P1 R4 DISPUTE (suggested: accept)

Target: `**Secure‑by‑Design Development** – Embed security testing`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / 

Reason: The en dash is a separator, not a range.

## P1 R4 DISPUTE (suggested: accept)

Target: `**Zero‑Trust Architecture** – Treat every access request as untrusted`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / 

Reason: The en dash is a separator, not a range.

## P1 R5 DISPUTE (suggested: review)

Target: `Ultimately, the resilience of digital societies will hinge`

Key: no_number / change / cut

Auditor: not_an_instance / keep / keep

Reason: Ultimately is a concluding transition here, not a degree intensifier or exclusive-marker finality interjection. Rule 1 already covers it.

## P1 R5 MISSED (suggested: review)

Target: `significantly more effective than most annual awareness programs assume`

Key:  /  / 

Auditor: no_number / change / cut

Reason: The planted Rule 1 row misses the independent Rule 5 intensifier violation; the supplied click-through rate does not support the comparison. [target occurs 0 times in essay]

## P2 R1 MISSED (suggested: review)

Target: `#### 2.3 Distributed Energy Resources (DERs)`

Key:  /  / 

Auditor: parenthetical_heading / change / cut

Reason: The heading contains a parenthetical acronym clarification.

## P2 R1 MISSED (suggested: review)

Target: `#### 6.2 Integration of Variable Renewable Energy (VRE)`

Key:  /  / 

Auditor: parenthetical_heading / change / cut

Reason: The heading contains a parenthetical acronym clarification.

## P2 R1 MISSED (suggested: review)

Target: `#### 7.5 Power‑to‑X (P2X) and Sector Coupling`

Key:  /  / 

Auditor: parenthetical_heading / change / cut

Reason: The heading contains a parenthetical acronym clarification; its non-ASCII hyphens are already keyed separately.

## P2 R1 MISSED (suggested: review)

Target: `seamlessly integrates electricity with heat, transport, and industry`

Key:  /  / 

Auditor: no_fact / change / cut

Reason: Seamlessly is another occurrence of the discouraged seamless wording.

## P2 R1 MISSED (suggested: review)

Target: `significantly below`

Key:  /  / 

Auditor: no_fact / change / cut

Reason: Significantly also violates the banned-word list; the key records only rule 5. [target occurs 0 times in essay]

## P2 R1 MISSED (suggested: review)

Target: `the “last mile” of the power system`

Key:  /  / 

Auditor: scare_quotes / change / cut

Reason: These are the author's decorative quotes around a familiar expression, not a source quotation.

## P2 R1 MISSED (suggested: review)

Target: `the “ramping” capacity`

Key:  /  / 

Auditor: scare_quotes / change / cut

Reason: Quotation marks unnecessarily surround the technical modifier.

## P2 R1 MISSED (suggested: review)

Target: `“Power‑to‑X” technologies`

Key:  /  / 

Auditor: scare_quotes / change / cut

Reason: The quotation marks decorate a technical term rather than reproduce source material.

## P2 R1 MISSED (suggested: review)

Target: `“Radial” designs`

Key:  /  / 

Auditor: scare_quotes / change / cut

Reason: Quotation marks unnecessarily surround an ordinary technical adjective.

## P2 R1 MISSED (suggested: review)

Target: `“always‑on,”`

Key:  /  / 

Auditor: scare_quotes / change / cut

Reason: The quoted expression is the author's own prose, not a reproduced quotation.

## P2 R2 DISPUTE (suggested: review)

Target: `While the basic principle—converting a primary energy source into usable electrical power—remains unchanged, `

Key: windup / change / cut

Auditor: loadbearing / keep / keep

Reason: The clause supplies a checkable distinction between an unchanged conversion principle and changing architecture; deletion loses that claim.

## P2 R2 DISPUTE (suggested: review)

Target: `While the fundamental tasks of generation, transmission, distribution, and protection remain, `

Key: windup / change / cut

Auditor: loadbearing / keep / keep

Reason: The unchanged functional tasks are a substantive contrast with the changing grid composition.

## P2 R2 DISPUTE (suggested: review)

Target: `effectively acting as virtual synchronous generators`

Key: doubling / change / cut

Auditor: loadbearing / keep / keep

Reason: Establishing a voltage reference does not itself restate all the behavior implied by a virtual synchronous generator.

## P2 R2 DISPUTE (suggested: review)

Target: `while fostering competition,`

Key: windup / change / cut

Auditor: loadbearing / keep / keep

Reason: Competition and price volatility are distinct claims; deleting competition loses information.

## P2 R3 DISPUTE (suggested: review)

Target: `Operators procured spinning reserve, rather than non-spinning reserve.`

Key: ambiguous / flag / flag

Auditor: field_specific / change / promote_to_sentence

Reason: Spinning and non-spinning reserve are established technical categories, not ordinary-knowledge antonyms; the distinction is not ambiguous.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Advanced Metering Infrastructure (AMI)** – Provides granular consumption data`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Decentralized Backup** – Microgrids that can island during disturbances`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Differential Protection** – Compares currents at two ends`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Distance Protection** – Measures impedance to locate fault location`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Distribution Management Systems (DMS)** – Automate reconfiguration, outage management`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Geographic Dispersion** – Renewable units are often sited`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Hardening Infrastructure** – Substation flood protection`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Hydrogen Integration** – Using excess renewable electricity for electrolysis`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Intermittency** – Power output varies with weather`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Massive DER Penetration** – Millions of rooftop PV installations`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Overcurrent Protection** – Detects excessive line currents`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Primary (Local) Control** – Governor action on turbines`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Provides Synthetic Inertia** – Emulates the kinetic response of rotating masses`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Substations** – Nodes where transformers step voltage`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Tertiary (Economic Dispatch)** – Centralized optimization ensures generation`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Transmission Lines** – Overhead conductors`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `1. **Generation** – Conversion of primary energy`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is specifically an en dash used as a separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `2. **Grid Stability** – Reduced rotating inertia and limited natural reactive power support`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `2. **Transmission & Distribution (T&D)** – Transport of electric power`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is specifically an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `200 kV—are em`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: The em dash closes the same parenthetical voltage-range fragment.

## P2 R4 DISPUTE (suggested: accept)

Target: `3. **Control & Protection** – Continuous monitoring`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is specifically an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `4. **Smart Devices** – Automated switches, reclosers`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `dscape—promis`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: The em dash closes the appositive benefits list.

## P2 R4 DISPUTE (suggested: review)

Target: `ectric‑vehicl`

Key: other / change / ascii_equivalent

Auditor: other_nonkeyboard /  / 

Reason: This real substring contains a nonbreaking hyphen.

## P2 R4 DISPUTE (suggested: accept)

Target: `entury’s powe`

Key: other / change / ascii_equivalent

Auditor: curly_quote /  / punct_straight_quote

Reason: The offending character is a curly apostrophe.

## P2 R4 DISPUTE (suggested: accept)

Target: `ltages—typica`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: The em dash opens a parenthetical voltage-range fragment.

## P2 R4 DISPUTE (suggested: accept)

Target: `nefits—reliab`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: The em dash opens an appositive benefits list.

## P2 R4 DISPUTE (suggested: review)

Target: `tility‑scale `

Key: other / change / ascii_equivalent

Auditor: other_nonkeyboard /  / 

Reason: This real substring contains a nonbreaking hyphen, not an unspecified character type.

## P2 R5 DISPUTE (suggested: review)

Target: `and increasingly, sophisticated`

Key: no_number / change / cut

Auditor: not_intensifier / keep / keep

Reason: Increasingly describes a temporal trend in ICT incorporation, not an intensity placeholder.

## P2 R5 DISPUTE (suggested: review)

Target: `catastrophic failures`

Key: no_number / change / cut

Auditor: not_intensifier / keep / keep

Reason: Catastrophic distinguishes severe system failures from ordinary equipment failures; it is not merely an intensifier.

## P2 R5 DISPUTE (suggested: review)

Target: `increasingly threaten reliability`

Key: no_number / change / cut

Auditor: not_intensifier / keep / keep

Reason: Increasingly states a temporal trend in threats, rather than intensifying the verb.

## P2 R5 MISSED (suggested: review)

Target: `massive rotating masses`

Key:  /  / 

Auditor: no_number / change / cut

Reason: Massive adds unquantified size emphasis to the explanation of inertia.

## P2 R5 MISSED (suggested: review)

Target: `seamlessly integrates electricity`

Key:  /  / 

Auditor: no_number / change / cut

Reason: Seamlessly asserts an unmeasured degree of integration without evidence.

## P3 R1 MISSED (suggested: review)

Target: `**“climate‑smart” plants**`

Key:  /  / 

Auditor: other / change / cut

Reason: Climate-smart is placed in non-source scare quotes rather than presented as a direct quotation.

## P3 R1 MISSED (suggested: review)

Target: `Moreover, the concept of`

Key:  /  / 

Auditor: no_fact / change / cut

Reason: A second, unkeyed occurrence of the listed transition Moreover.

## P3 R1 MISSED (suggested: review)

Target: `ethical utilization`

Key:  /  / 

Auditor: other / change / flag

Reason: Utilization is the nominalized form of the discouraged utilize and adds no precision here.

## P3 R1 MISSED (suggested: review)

Target: `leveraging the organelle’s prokaryotic-like gene expression system`

Key:  /  / 

Auditor: other / change / flag

Reason: A second, unkeyed use of the discouraged verb leverage.

## P3 R4 DISPUTE (suggested: accept)

Target: ` crops—wheat,`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: This opens an appositive list of staple crops.

## P3 R4 DISPUTE (suggested: accept)

Target: `change—underm`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: This closes the same parenthetical fragment before the main verb.

## P3 R4 DISPUTE (suggested: accept)

Target: `crobes—throug`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: This opens a parenthetical through-phrase.

## P3 R4 DISPUTE (suggested: accept)

Target: `deling—offers`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: This closes the participial parenthesis before offers.

## P3 R4 DISPUTE (suggested: accept)

Target: `ecules—chiefl`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: This opens an appositive fragment; an em dash requires a contextual punctuation decision, not a generic character swap.

## P3 R4 DISPUTE (suggested: accept)

Target: `enoids—absorb`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: This closes the pigment appositive; paired commas preserve the clause.

## P3 R4 DISPUTE (suggested: accept)

Target: `millet—accoun`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: This closes the staple-crop appositive list.

## P3 R4 DISPUTE (suggested: accept)

Target: `nities—via de`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: This opens a parenthetical prepositional fragment.

## P3 R4 DISPUTE (suggested: accept)

Target: `nolics—for th`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: This closes the metabolite appositive list.

## P3 R4 DISPUTE (suggested: accept)

Target: `olites—alkalo`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: This opens an appositive list of metabolites.

## P3 R4 DISPUTE (suggested: accept)

Target: `onoids—offers`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: This closes the parenthetical through-phrase before the main verb.

## P3 R4 DISPUTE (suggested: accept)

Target: `search—spanni`

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: This opens a participial parenthesis modifying research.

## P3 R4 DISPUTE (suggested: accept)

Target: `thways—areas `

Key: other / change / ascii_equivalent

Auditor: emdash_fragment /  / punct_comma

Reason: The dash introduces an explanatory noun fragment, not another independent clause.

## P3 R4 MISSED (suggested: review)

Target: `land‑use planning`

Key:  /  / 

Auditor: other_nonkeyboard / change / ascii_equivalent

Reason: Contains an unkeyed nonbreaking hyphen.

## P3 R5 MISSED (suggested: review)

Target: `a deep, nuanced understanding`

Key:  /  / 

Auditor: no_number / change / cut

Reason: Deep intensifies the claimed understanding without specifying evidence; the key covers nuanced under rule 1 but misses this rule-5 padding.

## P3 R5 MISSED (suggested: review)

Target: `offers unprecedented tools`

Key:  /  / 

Auditor: no_number / change / cut

Reason: Unprecedented supplies unsupported superlative emphasis without a comparison establishing the claim.

