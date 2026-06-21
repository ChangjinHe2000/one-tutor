# Source-to-question workflow

## 1. Inspect the source set

Inventory the supplied files and identify the smallest useful units: chapters, lessons, concepts, cases, formulas, vocabulary groups, or learning objectives. Preserve source locations so every key can be audited.

Use an appropriate file-reading capability for PDF, DOCX, slides, spreadsheets, webpages, images, or handwritten notes. Perform OCR only when necessary and treat OCR output as fallible.

## 2. Choose question forms

- Use single choice for concept boundaries and common confusions.
- Use multiple choice only when the number of correct choices is unambiguous.
- Use true/false sparingly; target meaningful misconceptions rather than trivial wording.
- Use short answer for recall, derivation steps, terminology, and explanation. Use manual grading when exact matching would be unfair.

Prefer retrieval and discrimination over copying sentences with one blank removed.

## 3. Write atomic, independent questions

Make each question answerable without opening the source or seeing a previous item. Include any necessary passage, data, or diagram. If that cannot be done safely, mark the question non-independent or disabled.

Avoid:

- “According to the figure above” when the figure is absent.
- Questions whose options overlap.
- Negation-heavy stems unless the negation is central and visually clear.
- Keys inferred from general model knowledge when the source provides a different convention.
- Explanations that merely repeat the correct option.

## 4. Build stable identity

Construct IDs from subject/topic plus a stable sequence or source anchor, for example `networking-tcp-014`. Never use the daily quiz number as the question ID. Keep the ID when correcting spelling, formatting, or explanations so learning history remains attached.

Create a new ID when the tested proposition or correct answer materially changes.

## 5. Validate before selection

Run the bundled validator. Resolve all errors. Manually examine context warnings, missing explanations, OCR artifacts, equations, tables, and image-dependent items.

Spot-check at least:

- Correct option-to-key mapping.
- Explanation consistency with the source.
- No answer markers or highlighted keys in the stem.
- No duplicate paraphrases testing the same source line unintentionally.
- Usable encoding for formulas and non-Latin text.

## 6. Handle imperfect questions during grading

Separate question defects from learner errors. Mark defective items `exclude: true`, explain why, and repair or disable them after the session. Never convert a parser failure or ambiguous item into a “knowledge gap.”

## 7. Respect sharing boundaries

Publish generated workflow code and original examples. Do not bundle textbooks, paid course files, private notes, personal history, or substantial copied question banks unless redistribution is authorized. Prefer requiring recipients to point the skill at their own materials.
