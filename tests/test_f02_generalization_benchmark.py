from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
import sys
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2app.understanding import (
    assemble_validated_document_ir,
    run_ocr_provider,
    run_vision_provider,
    validate_document_ir,
)
from tests.golden.generalization_cases import generalization_cases


_RUNS_PER_CASE = 20


def _jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _fingerprint(document: object) -> str:
    payload = json.dumps(_jsonable(document), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _percentile_95(values: list[float]) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))
    return ordered[index]


class F02GeneralizationBenchmarkTests(unittest.TestCase):
    def test_two_materially_different_workflows_share_one_validated_pipeline(self) -> None:
        total_runs = 0
        valid_runs = 0
        all_latencies_ms: list[float] = []
        fingerprints_by_case: dict[str, set[str]] = {}
        case_receipts: list[str] = []

        for case in generalization_cases():
            fingerprints: set[str] = set()
            latencies_ms: list[float] = []
            for _ in range(_RUNS_PER_CASE):
                started = time.perf_counter_ns()
                vision = run_vision_provider(case.vision_provider, case.provider_image)
                ocr = run_ocr_provider(case.ocr_provider, case.provider_image)
                document = assemble_validated_document_ir(case.normalized_image, vision, ocr)
                elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000.0

                report = validate_document_ir(document)
                total_runs += 1
                if report.is_valid:
                    valid_runs += 1
                self.assertTrue(report.is_valid, msg=f"{case.name} produced invalid DocumentIR: {report.issues}")
                fingerprints.add(_fingerprint(document))
                latencies_ms.append(elapsed_ms)
                all_latencies_ms.append(elapsed_ms)

            fingerprints_by_case[case.name] = fingerprints
            self.assertEqual(len(fingerprints), 1, msg=f"{case.name} DocumentIR fingerprint drifted across repeated runs")
            case_receipts.append(
                f"{case.name}: runs={len(latencies_ms)} valid={len(latencies_ms)} "
                f"mean_ms={sum(latencies_ms) / len(latencies_ms):.3f} p95_ms={_percentile_95(latencies_ms):.3f} "
                f"fingerprint={next(iter(fingerprints))[:16]}"
            )

        self.assertEqual(len(fingerprints_by_case), 2)
        self.assertEqual(valid_runs, total_runs)
        self.assertEqual(total_runs, 2 * _RUNS_PER_CASE)
        valid_rate = valid_runs / total_runs
        self.assertEqual(valid_rate, 1.0)

        print(
            "F02_W07_BENCHMARK "
            f"cases=2 runs={total_runs} valid={valid_runs} valid_ir_rate={valid_rate:.3f} "
            f"mean_ms={sum(all_latencies_ms) / len(all_latencies_ms):.3f} "
            f"p95_ms={_percentile_95(all_latencies_ms):.3f}"
        )
        for receipt in case_receipts:
            print(f"F02_W07_CASE {receipt}")

    def test_production_source_contains_no_demo_named_branch(self) -> None:
        src_root = Path(__file__).resolve().parents[1] / "src" / "paper2app"
        forbidden = (
            "equipment_checkout",
            "equipment checkout",
            "safety_inspection",
            "safety inspection",
            "safety / inspection",
        )
        hits: list[str] = []
        for path in src_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8").casefold()
            for token in forbidden:
                if token.casefold() in text:
                    hits.append(f"{path.relative_to(src_root)}:{token}")
        self.assertEqual(hits, [], msg=f"demo-specific production branch markers found: {hits}")

    def test_generalization_cases_are_materially_different(self) -> None:
        equipment, safety = generalization_cases()
        equipment_kinds = {item.visual_kind.value for item in equipment.vision_provider.observations.elements}
        safety_kinds = {item.visual_kind.value for item in safety.vision_provider.observations.elements}
        self.assertNotEqual(equipment.name, safety.name)
        self.assertIn("checkbox", equipment_kinds)
        self.assertIn("signature_line", equipment_kinds)
        self.assertIn("radio", safety_kinds)
        self.assertIn("handwriting_area", safety_kinds)
        self.assertGreater(len(safety.vision_provider.observations.elements), len(equipment.vision_provider.observations.elements))


if __name__ == "__main__":
    unittest.main()
