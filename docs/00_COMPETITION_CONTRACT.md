# Kiroween 2026 Competition Contract — Paper2App

**Status:** BUILD AUTHORIZED WITH RULES-PAGE RE-AUDIT GATE
**Created:** 2026-10-31 (Türkiye)
**Competition:** Kiroween 2026
**Primary category:** Frankenstein
**Project:** Paper2App

## 1. Build Authorization

Paper2App development is authorized because the Kiroween 2026 Devpost Overview explicitly states that the event is open for hacking, building starts now, and only projects created during the Submission Period (October 30–December 4, 2026) are eligible. The FAQ independently confirms that projects started before October 30 are not eligible.

Paper2App's competition repository was created after the Submission Period opened. No production code from the pre-competition `franki` concept folder is copied into this repository.

**Decision:** `BUILD = YES`

## 2. Important Publication Caveat

At the time of this contract, the Devpost Overview and FAQ contain 2026 submission requirements, but the dedicated Rules page still displays an "Official Rules not yet available" notice.

Therefore:

- development may begin;
- the Rules page must be re-audited as soon as the full Official Rules appear;
- any new eligibility, IP, licensing, category, judging, or submission constraint becomes authoritative and may require an immediate scope adjustment;
- no assumption in this document overrides the eventual Official Rules.

## 3. Current Verified Requirements

Current official Devpost surfaces state that:

1. The Submission Period is October 30 to December 4, 2026.
2. The submission deadline is December 4, 2026 at 2:00 PM Pacific Time.
3. Only new projects created during the Submission Period are eligible.
4. The project must be a working software application using Kiro.
5. The project must be submitted to exactly one main category.
6. Paper2App targets **Frankenstein**: combining seemingly incompatible technologies into one unexpectedly powerful application.
7. The repository must be a public GitHub repository.
8. The repository must include an open-source license.
9. The repository must contain `/.kiro` at the project root and it must not be excluded by `.gitignore`.
10. A URL to a working application must be provided.
11. A public YouTube demo video must be provided and should remain under three minutes.
12. The submission must explain how Kiro was used and should demonstrate meaningful use of Kiro features such as specs, steering, hooks, MCP, Crew, powers, or other supported workflows.
13. Teams may contain up to three people.
14. Current judging criteria include Potential Impact, Technological Implementation, Design, Innovation/Idea, and Presentation.

## 4. Official Source Surfaces

- Overview: https://kiroween.devpost.com/
- FAQ: https://kiroween.devpost.com/details/faqs
- Rules: https://kiroween.devpost.com/rules
- Resources: https://kiroween.devpost.com/resources

These URLs must be rechecked before major scope changes and before submission.

## 5. Fresh-Project Boundary

The following are permitted as design knowledge but are not imported as production implementation:

- pre-competition architectural reasoning;
- conceptual Paper2App requirements;
- DocumentIR and AppSpec design decisions;
- benchmark ideas;
- demo-case ideas;
- generic engineering lessons.

The following must be newly created inside the competition period:

- production source code;
- executable implementation;
- project-specific runtime assets;
- project-specific tests;
- project-specific Kiro configuration/specs/steering;
- deployment configuration;
- competition submission artifacts.

## 6. Current Category Lock

**Primary category: Frankenstein**

Reason: Paper2App combines document/image understanding, OCR where justified, semantic inference, typed intermediate representations, deterministic validation, dynamic UI/runtime generation, persistence, and Kiro-assisted engineering into one end-to-end transformation:

`Paper / photo -> understanding -> DocumentIR -> AppSpec -> validation -> working application`

The project must remain a coherent product rather than a collection of technologies. Every major component must earn its place in the transformation.

## 7. Submission-Critical Gates

Before final submission the project must prove:

- public GitHub repository exists;
- open-source license is visible;
- `/.kiro` is present at repository root;
- working public application URL exists;
- demo video is public and under three minutes;
- Kiro usage is documented with concrete evidence;
- end-to-end Paper2App flow works;
- at least two materially different paper workflows generate functioning applications through the same pipeline;
- repository can be built/run from documented instructions;
- Official Rules have been re-audited and no unresolved eligibility issue remains.

## 8. Stop Conditions

Development must pause for rule review if any newly published Official Rule conflicts with:

- project start timing;
- use of pre-existing materials;
- licensing;
- public repository requirements;
- Kiro usage requirements;
- category eligibility;
- deployment or submission requirements.

## 9. F00-W01 Decision

**Competition Rule Lock:** PASS WITH RE-AUDIT OBLIGATION

**Fresh Project Build Authorization:** PASS

**Next:** bootstrap project charter, roadmap, Kiro steering, license, repository metadata, then initialize Git and establish the first canonical competition commit.
