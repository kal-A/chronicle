# Scene 2 Content Fixture — "Vienna and Berlin: The Blank Cheque"

Plan 0 deliverable (`plans/phase-1-static-prototype.md`). This is the structured Source → Document → Passage → Claim → EvidenceLink → Relationship chain for Scene 2, in human-reviewable form, ahead of being encoded into the runtime domain contract in Plan 2. Everything below is `prototype-curated`, not `reviewed` — it satisfies the content gate in `docs/research/phase-1-scene-outline.md`, not the full bar in `docs/research/review-standard.md`. No item here may be displayed in the UI without also displaying its `prototype-curated` label.

Status key used below: `identified` / `acquired` / `passages-extracted` / `prototype-curated` (curated to the Plan 0 gate, pending independent reviewer sign-off) / `reviewed`.

---

## Sources and Documents

### `jc-src-001` — Szögyény-Marich to Berchtold, telegram no. 237, "The Blank Check"

- **Source status:** `passages-extracted` (was `curated`)
- **Document/edition used:** English translation by Adam Blauhut, published on German History in Documents and Images (GHDI); original published in Ludwig Bittner et al., eds., *Österreich-Ungarns Aussenpolitik von der Bosnischen Krise 1908 bis zum Kriegsausbruch 1914* (Vienna, 1930), vol. 8, no. 10,058; reprinted in Imanuel Geiss, *Julikrise und Kriegsausbruch 1914* (Hannover, 1963–64), vol. 1, pp. 83–84.
- **Access/rights:** Public web transcription (GHDI); translation credited, not public domain — display as short attributed excerpt, not full reproduction.
- **Known limitations:** Web transcription of a translated edition, not the original-language archival document; GHDI's translation choices are a layer of interpretation between the reader and the German original. The passage below establishes what Szögyény *reported*, not an independent verification of what Wilhelm II privately intended.

**Passage `jc-src-001-p1`:** Szögyény reports that Wilhelm II stated Austria-Hungary "could count on Germany's full support," Germany taking Austria-Hungary's side "in line with its customary loyalty." (Short attributed excerpt; full text remains in the cited edition, not reproduced here.)
- Locator: Bittner et al. vol. 8, no. 10,058; Geiss vol. 1, pp. 83–84; GHDI translation.
- `sent_time`: 5 July 1914, Berlin (Szögyény's telegram to Berchtold).
- `report_time`/`awareness_time` for Vienna: on or shortly after 5 July 1914 (exact received-time stamp not yet located in this edition — recorded as a gap, not assumed).

### `jc-src-002` — Tschirschky to Jagow, telegram no. 85, "Germany and the Ultimatum"

- **Source status:** `passages-extracted` (was `curated`)
- **Document/edition used:** English translation by Adam Blauhut (GHDI); original published in Walther Schücking and Max Montgelas, eds., *Die Deutschen Dokumente zum Kriegsausbruch*, 5 vols. (Berlin, 1922), vol. 5, p. 29.
- **Access/rights:** Public web transcription (GHDI); translation credited.
- **Known limitations:** Same translation-layer caveat as `jc-src-001`. Marginal notes are reproduced by the editors of the 1922 documentary edition, not photographed from the original — their transcription accuracy is inherited from that edition, not independently re-verified by Chronicle.

**Passage `jc-src-002-p1`:** Tschirschky reports from Vienna that "concrete demands had to be made of Serbia" and that if Serbia accepted them, the outcome would be "very disagreeable" to Count Berchtold — i.e., Vienna's foreign minister was, as of 10 July, oriented toward demands designed not to be simply accepted.
- Locator: Schücking/Montgelas vol. 5, p. 29; GHDI translation.
- `sent_time`: 10 July 1914, Vienna. `received_time`: not yet located in this edition (gap).

**Passage `jc-src-002-p2`:** Wilhelm II's marginal annotation on this report quotes Frederick the Great dismissing councils of war: "I am against councils of war and counseling, especially since the more timid party always gains the upper hand."
- Locator: same document, marginalia as reproduced in Schücking/Montgelas vol. 5, p. 29.
- `awareness_time`: establishes Wilhelm II had read and reacted to Tschirschky's 10 July report by the time of annotation (exact date of annotation not separately dated in this edition — treat annotation date as ≤ receipt, not identical to it).

### `jc-src-020` — Keiger, "The Historiography of the Origins of the First World War" (1914-1918-online)

- **Source status:** `passages-extracted` (was `curated`)
- **Access/rights:** Open scholarly reference, openly accessible.
- **Use:** Not evidence about July 1914 itself — evidence *that a genuine, citable historiographical dispute exists* about how much causal weight to assign the German assurance. Used to support the `disputed` classification on Relationship R1 below without Chronicle manufacturing the dispute itself.

**Passage `jc-src-020-p1`:** Characterizes Fischer's thesis: German leaders "planned a war of aggression" from late 1912 onward, and that Fischer's account "significantly reduced the interpretive weight placed on the international system" in favor of domestic political drivers.
**Passage `jc-src-020-p2`:** Characterizes Clark's *The Sleepwalkers* as "saturated with agency," focused on "how" rather than "why," arguing German behavior showed relative military calm through the crisis and shifting analytical weight toward the contingent, distributed decisions of multiple powers rather than singular German premeditation.

### `jc-src-021` — Autograph Letter of Franz Joseph to the Kaiser

- **Source status:** `passages-extracted` (was not previously in the register — new)
- **Document/edition used:** English translation, World War I Document Archive (Brigham Young University).
- **Access/rights:** Public transcription, public domain.
- **Known limitations:** The hosting archive's own metadata is internally inconsistent about the letter's composition date (its page title suggests 2 July; its stated "Date" field says 5 July). Recorded as an approximate range (1–5 July 1914) rather than resolved by assumption. What is well corroborated — by cross-reference with `jc-src-001` — is that this letter was delivered to Wilhelm II in Berlin on 5 July, alongside Szögyény's visit.

**Passage `jc-src-021-p1`:** Franz Joseph writes that the Sarajevo assassination was "the direct consequence of the agitation carried on by the Russian and Serbian Pan-Slavists whose sole aim is the weakening of the Triple Alliance and the destruction of my Empire." (Short attributed excerpt.)
- Locator: World War I Document Archive (BYU), "Autograph Letter of Franz Joseph to the Kaiser."
- This passage is evidence of Franz Joseph's own framing and the appeal that accompanied the request for backing — distinct from `jc-src-001`, which is Szögyény's report of Wilhelm's *response*, not the letter itself.

### `jc-src-016` (Fischer) and `jc-src-013` (Clark) — status unchanged: `identified`

Not yet acquired at passage level — Chronicle does not yet hold a directly-quotable passage from either book. `jc-src-020` is used instead to establish that the dispute is real and to characterize each side accurately, pending direct acquisition of `jc-src-016`/`jc-src-013` for future passage-level citation. This is recorded as an open gap, not silently upgraded.

---

## Entities (Scene 2)

| Entity | Type | Role in scene |
|---|---|---|
| Wilhelm II | Person | German Emperor; gives the verbal assurance; annotates the 10 July report |
| Franz Joseph I | Person | Austro-Hungarian Emperor; sender of the letter Szögyény delivered |
| Leopold Berchtold | Person | Austro-Hungarian Foreign Minister; recipient of Szögyény's telegram |
| László Szögyény-Marich | Person | Austro-Hungarian Ambassador to Berlin; reports the assurance |
| Heinrich von Tschirschky | Person | German Ambassador to Vienna; reports Vienna's ultimatum deliberations |
| Gottlieb von Jagow | Person | German Foreign Secretary; recipient of Tschirschky's report |
| Berlin | Place | City precision; German capital |
| Vienna | Place | City precision; Austro-Hungarian capital |

No building-level pins. No modern political-border implication for either city.

## Events / Decisions

- **E1 — Szögyény–Wilhelm II meeting, Berlin, 5 July 1914.** Szögyény delivers Franz Joseph's letter; Wilhelm II gives a verbal assurance of support. `event_time`: 5 July 1914, Berlin. Evidence: `jc-src-001-p1` (reported, not directly witnessed by Chronicle's source chain — Szögyény's own account is the evidentiary basis); `jc-src-021-p1` (context — Franz Joseph's own letter, the appeal that accompanied this meeting).
- **E2 — Szögyény's telegram to Berchtold, sent 5 July 1914.** `sent_time` 5 July 1914; `received_time` unresolved (gap, recorded honestly). Evidence: `jc-src-001-p1`.
- **D1 — Vienna's orientation toward a demand designed to be difficult to accept, reported 10 July 1914.** `decided_by`: Berchtold and associated Austro-Hungarian officials (Tschirschky's report characterizes Vienna's posture, not a single named individual's private intent). Evidence: `jc-src-002-p1`.
- **E3 — Wilhelm II's marginal reaction to Tschirschky's 10 July report.** Evidence: `jc-src-002-p2`. `awareness_time`: on or before annotation, exact date not established (gap).

## KnownAtTime

- **K1:** Berchtold/Vienna was informed of the German assurance on or shortly after 5 July 1914, via Szögyény's telegram (`jc-src-001-p1`). Chronicle does not assert Vienna "knew" this at the exact instant Wilhelm spoke it — only from the point the telegram is evidenced to have been sent, with received-time recorded as an honest gap rather than assumed same-day.

## Claims

- **C0:** "Franz Joseph's letter framed the Sarajevo assassination as the result of Pan-Slavist agitation aimed at weakening the Triple Alliance and destroying Austria-Hungary, seeking German backing on that basis." — `direct`, supported by `jc-src-021-p1`.
- **C1:** "Szögyény reported that Wilhelm II stated Austria-Hungary could count on Germany's full support." — `direct`, supported by `jc-src-001-p1`.
- **C2:** "Wilhelm II reacted to Tschirschky's 10 July report by dismissing the value of further diplomatic consultation, quoting Frederick the Great against councils of war." — `direct`, supported by `jc-src-002-p2`.
- **C3:** "By 10 July 1914, Vienna's diplomatic posture (as reported by Tschirschky) was oriented toward demands not designed to be simply accepted." — `direct` as a report of what Tschirschky stated; the underlying claim about Vienna's actual intent is `indirect` (Tschirschky's characterization, not a first-person Austro-Hungarian statement of intent). Supported by `jc-src-002-p1`.

## Relationship

- **R1:** "The German assurance of 5 July materially enabled/shaped Austria-Hungary's move toward a harsher, less compromise-oriented approach to Serbia." — `evidence_classification`: **disputed**.
  - Supporting interpretation (Fischer-aligned, per `jc-src-020-p1`): the assurance is read as part of deliberate German encouragement toward war, i.e., higher causal weight assigned to Berlin's intent.
  - Qualifying/counterweight interpretation (Clark-aligned, per `jc-src-020-p2`): causal weight is distributed across multiple powers' contingent choices; Clark's reading resists treating the German assurance alone as sufficient explanation for Vienna's subsequent path.
  - This relationship must render both positions with their sourcing, not resolve to a single stated cause — a single-answer UI treatment of R1 would itself be a defect under `AGENTS.md` §3.

## Explicit Gaps (do not silently fill)

- Exact received-time for Szögyény's 5 July telegram in Vienna.
- Exact received/annotation-date separation for Tschirschky's 10 July report.
- Direct passage-level quotation from Fischer (`jc-src-016`) and Clark (`jc-src-013`) themselves — currently represented via `jc-src-020`'s characterization of both, which is an honest and citable substitute but not a replacement for eventually acquiring the primary specialist texts.
- Original-German-language verification of both GHDI translations against the cited archival editions.

## Owner Review Note

Reviewed by Kamal (owner review, not independent domain-expert review, per `docs/research/review-standard.md`) as fit for Phase 1 prototype use under the `prototype-curated` label. Confirms: passages traceable to cited editions, R1 renders as genuinely disputed rather than resolved, gaps above are disclosed rather than hidden. Date of this owner review to be logged in `docs/research/validation-status.md` when formally signed off.
