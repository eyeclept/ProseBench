# Answer-key audit disagreements

Auditor: gpt-6.1-sol. Fill the `decision` column of `audit_decisions.csv` with keep, accept, or drop.
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

## P1 R3 DISPUTE (suggested: review)

Target: `incentivizes ethical hackers to report flaws rather than exploit them`

Key: field_specific / change / promote_to_sentence

Auditor: not_instance / keep / keep

Reason: The contrast between reporting and exploiting flaws is integral to what the bug bounty incentivizes, not a bolted-on antonym trailer. Reporting and exploitation are distinct actions, not ordinary-knowledge antonyms. This is not a Rule 3 instance.

## P1 R4 DISPUTE (suggested: accept)

Target: ` Union’s Cybe`

Key: curly_quote / change / punct_straight_quote

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

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Decentralized Backup** – Microgrids that can island during disturbances`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Differential Protection** – Compares currents at two ends`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Distance Protection** – Measures impedance to locate fault location`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Distribution Management Systems (DMS)** – Automate reconfiguration, outage management`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Geographic Dispersion** – Renewable units are often sited`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Hardening Infrastructure** – Substation flood protection`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Hydrogen Integration** – Using excess renewable electricity for electrolysis`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Intermittency** – Power output varies with weather`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Massive DER Penetration** – Millions of rooftop PV installations`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Overcurrent Protection** – Detects excessive line currents`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Primary (Local) Control** – Governor action on turbines`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Provides Synthetic Inertia** – Emulates the kinetic response of rotating masses`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Substations** – Nodes where transformers step voltage`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Tertiary (Economic Dispatch)** – Centralized optimization ensures generation`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `- **Transmission Lines** – Overhead conductors`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `1. **Generation** – Conversion of primary energy`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is specifically an en dash used as a separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `2. **Grid Stability** – Reduced rotating inertia and limited natural reactive power support`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `2. **Transmission & Distribution (T&D)** – Transport of electric power`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is specifically an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `200 kV—are em`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: The em dash closes the same parenthetical voltage-range fragment.

## P2 R4 DISPUTE (suggested: accept)

Target: `3. **Control & Protection** – Continuous monitoring`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is specifically an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `4. **Smart Devices** – Automated switches, reclosers`

Key: endash_range / change / punct_hyphen

Auditor: endash_separator /  / punct_hyphen

Reason: The offending character is an en dash separator.

## P2 R4 DISPUTE (suggested: accept)

Target: `dscape—promis`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: The em dash closes the appositive benefits list.

## P2 R4 DISPUTE (suggested: review)

Target: `ectric‑vehicl`

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: other_nonkeyboard /  / 

Reason: This real substring contains a nonbreaking hyphen.

## P2 R4 DISPUTE (suggested: accept)

Target: `entury’s powe`

Key: curly_quote / change / punct_straight_quote

Auditor: curly_quote /  / punct_straight_quote

Reason: The offending character is a curly apostrophe.

## P2 R4 DISPUTE (suggested: accept)

Target: `ltages—typica`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: The em dash opens a parenthetical voltage-range fragment.

## P2 R4 DISPUTE (suggested: accept)

Target: `nefits—reliab`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: The em dash opens an appositive benefits list.

## P2 R4 DISPUTE (suggested: review)

Target: `tility‑scale `

Key: other_nonkeyboard / change / ascii_equivalent

Auditor: other_nonkeyboard /  / 

Reason: This real substring contains a nonbreaking hyphen, not an unspecified character type.

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

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: This opens an appositive list of staple crops.

## P3 R4 DISPUTE (suggested: accept)

Target: `change—underm`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: This closes the same parenthetical fragment before the main verb.

## P3 R4 DISPUTE (suggested: accept)

Target: `crobes—throug`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: This opens a parenthetical through-phrase.

## P3 R4 DISPUTE (suggested: accept)

Target: `deling—offers`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: This closes the participial parenthesis before offers.

## P3 R4 DISPUTE (suggested: accept)

Target: `ecules—chiefl`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: This opens an appositive fragment; an em dash requires a contextual punctuation decision, not a generic character swap.

## P3 R4 DISPUTE (suggested: accept)

Target: `enoids—absorb`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: This closes the pigment appositive; paired commas preserve the clause.

## P3 R4 DISPUTE (suggested: accept)

Target: `millet—accoun`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: This closes the staple-crop appositive list.

## P3 R4 DISPUTE (suggested: accept)

Target: `nities—via de`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: This opens a parenthetical prepositional fragment.

## P3 R4 DISPUTE (suggested: accept)

Target: `nolics—for th`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: This closes the metabolite appositive list.

## P3 R4 DISPUTE (suggested: accept)

Target: `olites—alkalo`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: This opens an appositive list of metabolites.

## P3 R4 DISPUTE (suggested: accept)

Target: `onoids—offers`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: This closes the parenthetical through-phrase before the main verb.

## P3 R4 DISPUTE (suggested: accept)

Target: `search—spanni`

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: This opens a participial parenthesis modifying research.

## P3 R4 DISPUTE (suggested: accept)

Target: `thways—areas `

Key: emdash_fragment / change / punct_comma

Auditor: emdash_fragment /  / punct_comma

Reason: The dash introduces an explanatory noun fragment, not another independent clause.

## P3 R5 MISSED (suggested: review)

Target: `a deep, nuanced understanding`

Key:  /  / 

Auditor: no_number / change / cut

Reason: Deep intensifies the claimed understanding without specifying evidence; the key covers nuanced under rule 1 but misses this rule-5 padding.

