# Paper2App Product Steering

## Product identity

Paper2App turns a photo of a paper workflow into a working, persistent application.

One-line hook:

> Take a picture of a paper workflow and turn it into a working application.

## Competition context

- Kiroween 2026
- Primary category: Frankenstein
- Fresh project created during the Submission Period
- Kiro usage must remain substantive and evidenced in this repository

## Primary product flow

`Paper/photo -> understand structure and intent -> DocumentIR -> AppSpec -> deterministic validation -> schema-driven runtime -> persistent working app`

## Product priorities

1. End-to-end usefulness over architectural spectacle.
2. Two materially different paper workflows through the same pipeline.
3. Real persistence and reload proof.
4. Explicit confidence/uncertainty instead of hallucinated certainty.
5. Fast judge comprehension.
6. Clean, coherent UX.
7. Measurable evidence for claims.

## Demo targets

Primary: Equipment Checkout.

Secondary: Safety / Inspection Report.

Do not hard-code either demo into the runtime. Both must be expressed through common contracts.

## Non-goals

Do not turn Paper2App into:

- a universal no-code suite;
- an enterprise BPM product;
- a generic source-code generator;
- a giant agent framework;
- a perfect OCR or handwriting system;
- a multi-user SaaS platform unless competition evidence proves it necessary.

## Decision rule

Complexity must earn its place.

When choosing between a broad clever mechanism and a smaller reliable mechanism that satisfies the product contract, prefer the smaller reliable mechanism.
