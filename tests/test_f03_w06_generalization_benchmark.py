from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
import sys
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2app.specification import (
    AppSpecValidationError,
    AppSpecValidationStatus,
    Capability,
    FieldType,
    ValidationRuleKind,
    synthesize_validated_app_spec,
    validate_app_spec,
)
from tests.golden.app_spec_generalization_cases import appspec_generalization_document_irs
from tests.golden.document_ir_samples import safety_inspection_golden


def _canonical(value):
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _canonical(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    return value


def _fingerprint(value) -> str:
    payload = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


class F03W06GeneralizationBenchmarkTests(unittest.TestCase):
    def test_two_materially_different_cases_are_valid_and_structurally_stable(self) -> None:
        total_runs = 0
        total_valid = 0
        case_fingerprints: dict[str, str] = {}

        for case_name, document_ir in appspec_generalization_document_irs():
            latencies_ms: list[float] = []
            fingerprints: set[str] = set()
            for _ in range(20):
                started = time.perf_counter_ns()
                app_spec = synthesize_validated_app_spec(document_ir)
                elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
                report = validate_app_spec(app_spec)
                total_runs += 1
                if report.valid:
                    total_valid += 1
                self.assertIs(report.status, AppSpecValidationStatus.PASS)
                latencies_ms.append(elapsed_ms)
                fingerprints.add(_fingerprint(app_spec))

            self.assertEqual(len(fingerprints), 1)
            fingerprint = next(iter(fingerprints))
            case_fingerprints[case_name] = fingerprint
            print(
                "F03_W06_CASE "
                f"{case_name}: runs=20 valid=20 mean_ms={mean(latencies_ms):.3f} "
                f"p95_ms={_p95(latencies_ms):.3f} fingerprint={fingerprint}"
            )

        self.assertEqual(total_runs, 40)
        self.assertEqual(total_valid, 40)
        self.assertEqual(len(case_fingerprints), 2)
        self.assertNotEqual(case_fingerprints["equipment_checkout"], case_fingerprints["safety_inspection"])
        print(f"F03_W06_BENCHMARK cases=2 runs={total_runs} valid={total_valid} valid_appspec_rate={total_valid / total_runs:.3f}")

    def test_cases_are_materially_different_without_production_branching(self) -> None:
        cases = dict(appspec_generalization_document_irs())
        equipment = synthesize_validated_app_spec(cases["equipment_checkout"])
        safety = synthesize_validated_app_spec(cases["safety_inspection"])

        equipment_fields = {field.field_id: field for field in equipment.entities[0].fields}
        safety_fields = {field.field_id: field for field in safety.entities[0].fields}
        self.assertNotEqual(set(equipment_fields), set(safety_fields))
        self.assertNotIn("severity", equipment_fields)
        self.assertIn("severity", safety_fields)
        self.assertIs(safety_fields["severity"].field_type, FieldType.ENUM)
        self.assertEqual(safety_fields["severity"].options, ("Low", "Medium", "High"))

        self.assertEqual(equipment.workflows, ())
        self.assertEqual(len(safety.workflows), 1)
        workflow = safety.workflows[0]
        self.assertEqual([state.display_name for state in workflow.states], ["Low", "Medium", "High"])
        self.assertEqual(len(workflow.transitions), 2)
        self.assertNotIn(Capability.BASIC_WORKFLOW, equipment.capabilities)
        self.assertIn(Capability.BASIC_WORKFLOW, safety.capabilities)

        allowed_values = next(
            validation
            for validation in safety.validations
            if validation.field_id == "severity" and validation.kind is ValidationRuleKind.ALLOWED_VALUES
        )
        self.assertEqual(allowed_values.value, ("Low", "Medium", "High"))

    def test_original_unresolved_safety_golden_remains_fail_closed(self) -> None:
        with self.assertRaises(AppSpecValidationError) as caught:
            synthesize_validated_app_spec(safety_inspection_golden().document_ir)
        self.assertIs(caught.exception.report.status, AppSpecValidationStatus.FAIL)

    def test_production_source_contains_no_demo_specific_synthesis_branch(self) -> None:
        source_root = Path(__file__).resolve().parents[1] / "src" / "paper2app"
        production_text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(source_root.rglob("*.py"))).casefold()
        forbidden = (
            "equipment_checkout",
            "equipment checkout",
            "safety_inspection",
            "safety inspection",
            "safety / inspection",
        )
        self.assertEqual([marker for marker in forbidden if marker in production_text], [])


if __name__ == "__main__":
    unittest.main()
