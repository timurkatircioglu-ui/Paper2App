from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2app.runtime.record_validation import (
    RecordValidationError,
    RecordValidationIssueCode,
    require_valid_record_payload,
    validate_record_payload,
)
from paper2app.runtime.registry import AppSpecRegistry, RuntimeFailureCode
from paper2app.specification.app_spec import (
    AppEntity,
    AppField,
    AppIdentity,
    AppSpec,
    AppValidation,
    Capability,
    FieldType,
    PersistenceRequirement,
    ValidationRuleKind,
)


def _registered():
    fields = (
        AppField("name", "Name", FieldType.STRING, default_value="Guest"),
        AppField("age", "Age", FieldType.INTEGER),
        AppField("score", "Score", FieldType.DECIMAL),
        AppField("active", "Active", FieldType.BOOLEAN),
        AppField("day", "Day", FieldType.DATE),
        AppField("clock", "Clock", FieldType.TIME),
        AppField("stamp", "Stamp", FieldType.DATETIME),
        AppField("color", "Color", FieldType.ENUM, options=("red", "blue", "green")),
        AppField("tags", "Tags", FieldType.MULTI_ENUM, options=("x", "y", "z")),
        AppField("email", "Email", FieldType.EMAIL),
        AppField("phone", "Phone", FieldType.PHONE),
        AppField("code", "Code", FieldType.IDENTIFIER),
        AppField("notes", "Notes", FieldType.MULTILINE_STRING),
        AppField("signature", "Signature", FieldType.SIGNATURE),
    )
    validations = (
        AppValidation("v_required_name", "record", "name", ValidationRuleKind.REQUIRED),
        AppValidation("v_name_min", "record", "name", ValidationRuleKind.MIN_LENGTH, 2),
        AppValidation("v_name_max", "record", "name", ValidationRuleKind.MAX_LENGTH, 10),
        AppValidation("v_age_min", "record", "age", ValidationRuleKind.MIN, 18),
        AppValidation("v_age_max", "record", "age", ValidationRuleKind.MAX, 99),
        AppValidation("v_color", "record", "color", ValidationRuleKind.ALLOWED_VALUES, ("red", "blue")),
        AppValidation("v_tags", "record", "tags", ValidationRuleKind.ALLOWED_VALUES, ("x", "y")),
        AppValidation("v_email", "record", "email", ValidationRuleKind.FORMAT, "email"),
        AppValidation("v_phone", "record", "phone", ValidationRuleKind.FORMAT, "phone"),
        AppValidation("v_code", "record", "code", ValidationRuleKind.FORMAT, "identifier"),
    )
    app_spec = AppSpec(
        app=AppIdentity("record_app", "Record App", "Runtime validation fixture.", "record"),
        entities=(AppEntity("record", "Record", fields),),
        views=(),
        actions=(),
        workflows=(),
        validations=validations,
        capabilities=(Capability.MULTI_CHOICE, Capability.SIGNATURE_CAPTURE),
        persistence=PersistenceRequirement(required=False, survive_reload=False),
        provenance=(),
        uncertainties=(),
    )
    return AppSpecRegistry().register(app_spec)


class RecordValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registered = _registered()

    def test_valid_payload_normalizes_in_entity_field_order_and_applies_default(self) -> None:
        result = require_valid_record_payload(
            self.registered,
            "record",
            {"active": True, "age": 21, "color": "red", "tags": ["x", "y"]},
        )
        self.assertEqual(result.registration_id, self.registered.registration_id)
        self.assertEqual(result.app_id, "record_app")
        self.assertEqual(result.entity_id, "record")
        self.assertEqual(
            result.values,
            (("name", "Guest"), ("age", 21), ("active", True), ("color", "red"), ("tags", ("x", "y"))),
        )
        self.assertEqual(result.as_dict()["tags"], ["x", "y"])

    def test_optional_missing_field_remains_absent(self) -> None:
        result = require_valid_record_payload(self.registered, "record", {"age": 22})
        self.assertNotIn("notes", result.as_dict())
        self.assertEqual(result.as_dict()["name"], "Guest")

    def test_unknown_field_is_rejected(self) -> None:
        report = validate_record_payload(self.registered, "record", {"age": 22, "rogue": "x"})
        self.assertFalse(report.valid)
        self.assertIn(RecordValidationIssueCode.UNKNOWN_FIELD, {issue.code for issue in report.issues})

    def test_unknown_entity_is_rejected(self) -> None:
        report = validate_record_payload(self.registered, "missing", {})
        self.assertEqual(report.issues[0].code, RecordValidationIssueCode.ENTITY_NOT_FOUND)

    def test_strict_integer_and_boolean_types(self) -> None:
        report = validate_record_payload(self.registered, "record", {"age": True, "active": 1})
        self.assertEqual(
            [issue.code for issue in report.issues].count(RecordValidationIssueCode.INVALID_FIELD_TYPE),
            2,
        )

    def test_decimal_must_be_finite(self) -> None:
        report = validate_record_payload(self.registered, "record", {"score": float("inf")})
        self.assertIn(RecordValidationIssueCode.INVALID_FIELD_TYPE, {issue.code for issue in report.issues})

    def test_iso_date_time_datetime_are_canonicalized(self) -> None:
        result = require_valid_record_payload(
            self.registered,
            "record",
            {"day": "2026-01-02", "clock": "09:30:00", "stamp": "2026-01-02 09:30:00"},
        )
        values = result.as_dict()
        self.assertEqual(values["day"], "2026-01-02")
        self.assertEqual(values["clock"], "09:30:00")
        self.assertEqual(values["stamp"], "2026-01-02T09:30:00")

    def test_invalid_iso_value_is_rejected(self) -> None:
        report = validate_record_payload(self.registered, "record", {"day": "not-a-date"})
        self.assertIn(RecordValidationIssueCode.INVALID_FIELD_TYPE, {issue.code for issue in report.issues})

    def test_enum_choice_is_checked_against_field_options(self) -> None:
        report = validate_record_payload(self.registered, "record", {"color": "purple"})
        self.assertIn(RecordValidationIssueCode.INVALID_CHOICE, {issue.code for issue in report.issues})

    def test_multi_enum_accepts_json_list_and_rejects_duplicates(self) -> None:
        valid = require_valid_record_payload(self.registered, "record", {"tags": ["x", "y"]})
        self.assertEqual(valid.values[-1], ("tags", ("x", "y")))
        invalid = validate_record_payload(self.registered, "record", {"tags": ["x", "x"]})
        self.assertIn(RecordValidationIssueCode.DUPLICATE_CHOICE, {issue.code for issue in invalid.issues})

    def test_required_rejects_none_and_blank(self) -> None:
        for payload in ({"name": None}, {"name": "   "}):
            with self.subTest(payload=payload):
                report = validate_record_payload(self.registered, "record", payload)
                self.assertIn(RecordValidationIssueCode.REQUIRED_FIELD_MISSING, {issue.code for issue in report.issues})

    def test_min_and_max_rules_are_authoritative(self) -> None:
        for age in (17, 100):
            with self.subTest(age=age):
                report = validate_record_payload(self.registered, "record", {"age": age})
                self.assertIn(RecordValidationIssueCode.VALIDATION_RULE_FAILED, {issue.code for issue in report.issues})

    def test_min_and_max_length_rules_are_authoritative(self) -> None:
        for name in ("A", "01234567890"):
            with self.subTest(name=name):
                report = validate_record_payload(self.registered, "record", {"name": name})
                self.assertIn(RecordValidationIssueCode.VALIDATION_RULE_FAILED, {issue.code for issue in report.issues})

    def test_allowed_values_can_be_narrower_than_field_options(self) -> None:
        color = validate_record_payload(self.registered, "record", {"color": "green"})
        tags = validate_record_payload(self.registered, "record", {"tags": ["z"]})
        self.assertIn(RecordValidationIssueCode.VALIDATION_RULE_FAILED, {issue.code for issue in color.issues})
        self.assertIn(RecordValidationIssueCode.VALIDATION_RULE_FAILED, {issue.code for issue in tags.issues})

    def test_email_phone_identifier_formats_are_bounded(self) -> None:
        valid = require_valid_record_payload(
            self.registered,
            "record",
            {"email": "a@example.com", "phone": "+90 (555) 123-4567", "code": "FORM-01:A"},
        )
        self.assertEqual(valid.as_dict()["code"], "FORM-01:A")
        invalid = validate_record_payload(
            self.registered,
            "record",
            {"email": "bad", "phone": "12", "code": "bad code"},
        )
        self.assertEqual(
            [issue.code for issue in invalid.issues].count(RecordValidationIssueCode.VALIDATION_RULE_FAILED),
            3,
        )

    def test_optional_none_skips_non_required_rules(self) -> None:
        result = require_valid_record_payload(self.registered, "record", {"email": None, "age": None})
        self.assertIsNone(result.as_dict()["email"])
        self.assertIsNone(result.as_dict()["age"])

    def test_require_valid_raises_stable_runtime_failure(self) -> None:
        with self.assertRaises(RecordValidationError) as caught:
            require_valid_record_payload(self.registered, "record", {"rogue": True})
        self.assertEqual(caught.exception.code, RuntimeFailureCode.RECORD_VALIDATION_FAILED)
        self.assertIn("UNKNOWN_FIELD:rogue", caught.exception.details)

    def test_input_mapping_order_does_not_change_normalized_payload(self) -> None:
        first = require_valid_record_payload(self.registered, "record", {"age": 30, "active": False})
        second = require_valid_record_payload(self.registered, "record", {"active": False, "age": 30})
        self.assertEqual(first.values, second.values)


if __name__ == "__main__":
    unittest.main()
