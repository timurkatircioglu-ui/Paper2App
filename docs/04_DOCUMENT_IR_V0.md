# Paper2App — DocumentIR Contract V0.1

**Status:** Canonical competition baseline

## Purpose

DocumentIR answers:

> What is actually present in this physical document, and how confident are we?

It does **not** answer how the application should be implemented.

## Top-level shape

```json
{
  "schema": "paper2app.document_ir",
  "schema_version": "0.1",
  "source": {},
  "document": {},
  "pages": [],
  "regions": [],
  "elements": [],
  "field_candidates": [],
  "relations": [],
  "uncertainties": []
}
```

## Core principles

1. Preserve source identity and raw observations.
2. Keep observation and inference distinguishable.
3. Important inferences may carry confidence and observable evidence.
4. `unknown` is a valid result.
5. References and geometry validate deterministically.
6. Different document types share the same contract.
7. Application implementation concepts are forbidden.

## Source

Suggested fields:

- `source_id`
- `media_type`
- original dimensions
- source SHA-256
- capture kind
- normalization metadata

The original and normalized document representations remain distinguishable.

## Pages

The contract supports `pages[]` even though competition V1 may initially accept only one page. This avoids coupling the representation to the first capability boundary.

## Geometry

Use normalized coordinates in the `0.0..1.0` range where practical.

Example:

```json
{
  "bbox": {"x": 0.12, "y": 0.31, "w": 0.25, "h": 0.04}
}
```

Geometry is first-class evidence for label/input association and document structure.

## Regions

Candidate region hints may include:

- `title_area`
- `section`
- `field_group`
- `table_like`
- `instructions`
- `footer`
- `unknown`

The vocabulary should remain bounded.

## Elements

Candidate visual kinds:

- `text`
- `blank_line`
- `input_box`
- `checkbox`
- `radio`
- `signature_line`
- `handwriting_area`
- `separator`
- `arrow`
- `unknown`

Visual observation and semantic role are separate properties. For example `visual_kind=text` is observational while `role_hint=field_label` is inferential.

## Text preservation

Keep raw and normalized text separate.

Example:

```json
{
  "raw": "DATE :",
  "normalized": "Date",
  "confidence": 0.96
}
```

Normalization must never silently erase the raw extraction.

## Field candidates

A field candidate links document evidence without committing application implementation.

Possible semantic value hints:

- `free_text`
- `person_name`
- `number`
- `date`
- `time`
- `boolean`
- `choice`
- `multiline_text`
- `signature`
- `identifier`
- `email`
- `phone`
- `unknown`

These are document-semantic hints, not database types.

## Relations

Initial bounded relation vocabulary:

- `labels`
- `contains`
- `belongs_to`
- `option_of`
- `follows`
- `aligned_with`
- `associated_with`

Example: text `Returned` may `labels` an adjacent checkbox.

Directional clarification for `follows`: when `follows` is used as ordered workflow evidence, `source_id` is the predecessor and `target_id` is the successor. This direction is part of the bounded DocumentIR contract so downstream synthesis never guesses order.

## Evidence

Evidence records observable support rather than private model reasoning.

Useful evidence can include:

- element IDs;
- text content;
- visual kind;
- spatial proximity/alignment;
- containment;
- provider observation identifiers.

Do not store chain-of-thought.

## Uncertainty

Ambiguity remains explicit. Example: a field may be `signature` with medium confidence or `free_text` with similar confidence. The system must be allowed to emit an unresolved candidate rather than forcing certainty.

## Deterministic invariants

- known schema/version;
- all IDs unique;
- references resolve;
- confidence in `0.0..1.0` when present;
- geometry remains in valid bounds;
- page references resolve;
- relation endpoints resolve;
- evidence references resolve;
- raw values are preserved when supplied;
- application implementation concepts are absent.

## Forbidden content

DocumentIR must not define:

- SQL/database tables;
- React components;
- API routes;
- CRUD implementation;
- storage engine;
- CSS/layout implementation;
- executable workflow code;
- generated source code.

## Demo proof

The same contract must represent both Equipment Checkout and Safety / Inspection Report documents.

## Architecture laws

- D1 Source truth is preserved.
- D2 Raw extraction is never silently overwritten.
- D3 Observation and inference remain distinguishable.
- D4 Important inference may carry confidence.
- D5 Important inference may cite observable evidence.
- D6 UNKNOWN is valid.
- D7 References validate deterministically.
- D8 DocumentIR describes the document, not application implementation.
- D9 Different document types share one contract.
