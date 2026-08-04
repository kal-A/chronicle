# Phase 1 July Crisis Scene Outline

This is a four-scene prototype outline, not a finished historical narrative. Each scene identifies the decision problem, actors, evidence route, and uncertainty the interface must preserve. All content remains draft until passage-level curation and human review are logged in `validation-status.md`.

## Scene 1 — Sarajevo: Event, Report, and Initial Awareness

**Range:** 28 June–1 July 1914  
**Places:** Sarajevo (city precision), Vienna (city precision), Belgrade (city precision)  
**Actors:** Franz Ferdinand and Sophie; Gavrilo Princip; Austro-Hungarian officials; Serbian government officials  
**Center:** The assassination occurs, but reports, interpretations, and knowledge of responsibility propagate at different times.

**Historical behavior to demonstrate:** Separate event time from report time and actor-awareness time. The interface must not infer that any government knew the plot's organization at the instant of the assassination.

**Disputed relationship:** The extent and form of Serbian state involvement in the plot. The prototype must allow multiple claims and an `insufficient_evidence` or `disputed` relationship rather than collapse state, unofficial networks, and individual conspirators.

**Initial sources:** `jc-src-012`, `jc-src-013`, `jc-src-014`, `jc-src-017`; dedicated Sarajevo/Serbian primary sources remain an acquisition gap.

## Scene 2 — Vienna and Berlin: The “Blank Cheque”

**Range:** 4–10 July 1914  
**Places:** Vienna and Berlin (city precision; no building-level pins)  
**Actors:** Franz Joseph; Wilhelm II; Berchtold; Szögyény-Marich; Hoyos; Bethmann Hollweg; Jagow; Tschirschky  
**Center:** Austria-Hungary seeks German backing while deciding how to respond to Serbia; German assurances are reported to Vienna.

**Historical behavior to demonstrate:** A telegram has separate sent/received times and reports a prior conversation. The UI distinguishes what Wilhelm expressed, what Szögyény reported, what Vienna received, and later historians' interpretations.

**Disputed relationship:** How strongly German support enabled or shaped Austria-Hungary's move toward an ultimatum and war. The 5 July report directly supports that an assurance was communicated; its causal weight remains disputed and requires secondary comparison.

**Initial sources:** `jc-src-001`, `jc-src-002`, `jc-src-008`, `jc-src-009`, `jc-src-012`–`jc-src-018`.

**Recommended first vertical slice:** This scene has the strongest available combination of compact scope, direct documentary evidence, actor-awareness timing, geographic movement, and honest historiographical disagreement.

## Scene 3 — The Ultimatum and Serbian Reply

**Range:** 23–25 July 1914  
**Places:** Vienna and Belgrade (city precision)  
**Actors:** Berchtold; Nikola Pašić; Baron Giesl; Serbian cabinet; Russian government  
**Center:** Austria-Hungary presents a time-limited ultimatum; Serbia replies; diplomatic relations are broken.

**Historical behavior to demonstrate:** The deadline, sent/delivered/received times, clause-by-clause response, and Russian advice cannot be reduced to “Serbia accepted everything except one demand.”

**Disputed relationship:** Whether the ultimatum was constructed to be rejected and whether the reply offered a sufficient diplomatic opening. These are interpretations supported differently by documents and historians.

**Initial sources:** `jc-src-004`, `jc-src-006`, `jc-src-010`, `jc-src-011`, `jc-src-012`–`jc-src-019`.

## Scene 4 — From Local War to General War

**Range:** 28 July–4 August 1914  
**Places:** Vienna, Belgrade, St. Petersburg, Berlin, Paris, Brussels, London (city precision)  
**Actors:** Austro-Hungarian, Russian, German, French, Belgian, and British governments; military leadership  
**Center:** Declaration of war, mobilization decisions, German ultimatums and operations, Belgian neutrality, and Britain's entry.

**Historical behavior to demonstrate:** Mobilization orders and war declarations are distinct events; military assessments exert pressure without being modeled as automatic causes. KnownAtTime records must identify what each cabinet had received when it acted.

**Disputed relationship:** “War by timetable” versus continued political choice. The graph must not depict mobilization as an irreversible mechanical edge without classified evidence.

**Initial sources:** `jc-src-003`, `jc-src-005`–`jc-src-008`, `jc-src-012`–`jc-src-020`.

## Content Gate Before Implementation

For Scene 2, extract and record at least:

1. One supporting Passage from `jc-src-001` for the reported German assurance.
2. One Passage from `jc-src-002` showing German awareness of the ultimatum deliberation.
3. Two specialist-secondary passages that interpret the assurance's causal significance differently or with materially different emphasis.
4. Source, document/edition, passage locator, language/translation, temporal scope, geographic scope, and limitations for every passage.
5. Human review notes confirming which statements are documentary facts and which are later interpretations.

