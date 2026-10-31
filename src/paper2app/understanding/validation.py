"""Deterministic graph validation for Paper2App DocumentIR."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import string

from .document_ir import (
    DOCUMENT_IR_SCHEMA,
    DOCUMENT_IR_SCHEMA_VERSION,
    DocumentIR,
)


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class ValidationStatus(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    FAIL = "FAIL"


class ValidationIssueCode(str, Enum):
    DOCUMENT_TYPE_INVALID = "DOCUMENT_TYPE_INVALID"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    SCHEMA_VERSION_INVALID = "SCHEMA_VERSION_INVALID"
    SOURCE_HASH_INVALID = "SOURCE_HASH_INVALID"
    PAGE_SET_INVALID = "PAGE_SET_INVALID"
    SOURCE_PAGE_MISMATCH = "SOURCE_PAGE_MISMATCH"
    DUPLICATE_ID = "DUPLICATE_ID"
    PAGE_REFERENCE_INVALID = "PAGE_REFERENCE_INVALID"
    FIELD_TARGET_INVALID = "FIELD_TARGET_INVALID"
    RELATION_ENDPOINT_INVALID = "RELATION_ENDPOINT_INVALID"
    EVIDENCE_REFERENCE_INVALID = "EVIDENCE_REFERENCE_INVALID"
    DUPLICATE_REFERENCE = "DUPLICATE_REFERENCE"
    DOCUMENT_UNCERTAINTY = "DOCUMENT_UNCERTAINTY"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    severity: ValidationSeverity
    code: ValidationIssueCode
    path: str
    message: str


@dataclass(frozen=True, slots=True)
class DocumentIRValidationReport:
    status: ValidationStatus
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return self.status is not ValidationStatus.FAIL

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is ValidationSeverity.ERROR)

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is ValidationSeverity.WARNING)


class DocumentIRValidationError(ValueError):
    def __init__(self, report: DocumentIRValidationReport) -> None:
        super().__init__("DocumentIR failed deterministic validation")
        self.report = report


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in string.hexdigits for character in value)
    )


def _append_issue(
    issues: list[ValidationIssue],
    severity: ValidationSeverity,
    code: ValidationIssueCode,
    path: str,
    message: str,
) -> None:
    issues.append(ValidationIssue(severity=severity, code=code, path=path, message=message))


def _check_unique_references(
    values: tuple[str, ...],
    *,
    path: str,
    issues: list[ValidationIssue],
) -> None:
    if len(values) != len(set(values)):
        _append_issue(
            issues,
            ValidationSeverity.ERROR,
            ValidationIssueCode.DUPLICATE_REFERENCE,
            path,
            "Reference list contains duplicate IDs.",
        )


def validate_document_ir(document_ir: object) -> DocumentIRValidationReport:
    """Validate cross-object DocumentIR invariants without mutating the graph."""

    issues: list[ValidationIssue] = []
    if not isinstance(document_ir, DocumentIR):
        _append_issue(
            issues,
            ValidationSeverity.ERROR,
            ValidationIssueCode.DOCUMENT_TYPE_INVALID,
            "$",
            "Value is not a DocumentIR instance.",
        )
        return DocumentIRValidationReport(status=ValidationStatus.FAIL, issues=tuple(issues))

    if document_ir.schema != DOCUMENT_IR_SCHEMA:
        _append_issue(
            issues,
            ValidationSeverity.ERROR,
            ValidationIssueCode.SCHEMA_INVALID,
            "$.schema",
            "DocumentIR schema is not supported.",
        )
    if document_ir.schema_version != DOCUMENT_IR_SCHEMA_VERSION:
        _append_issue(
            issues,
            ValidationSeverity.ERROR,
            ValidationIssueCode.SCHEMA_VERSION_INVALID,
            "$.schema_version",
            "DocumentIR schema version is not supported.",
        )

    for attribute in ("source_sha256", "normalized_sha256"):
        if not _is_sha256(getattr(document_ir.source, attribute)):
            _append_issue(
                issues,
                ValidationSeverity.ERROR,
                ValidationIssueCode.SOURCE_HASH_INVALID,
                f"$.source.{attribute}",
                f"{attribute} must be a 64-character hexadecimal SHA-256 value.",
            )

    page_indices = [page.page_index for page in document_ir.pages]
    expected_page_indices = list(range(len(document_ir.pages)))
    if not document_ir.pages or sorted(page_indices) != expected_page_indices:
        _append_issue(
            issues,
            ValidationSeverity.ERROR,
            ValidationIssueCode.PAGE_SET_INVALID,
            "$.pages",
            "Page indices must be unique and contiguous from zero.",
        )

    page_index_set = set(page_indices)
    if len(document_ir.pages) == 1:
        page = document_ir.pages[0]
        if (
            page.width != document_ir.source.normalized_width
            or page.height != document_ir.source.normalized_height
        ):
            _append_issue(
                issues,
                ValidationSeverity.ERROR,
                ValidationIssueCode.SOURCE_PAGE_MISMATCH,
                "$.pages[0]",
                "Single-page dimensions must match normalized source dimensions.",
            )

    all_ids: dict[str, str] = {}

    def register(identifier: str, path: str) -> None:
        previous = all_ids.get(identifier)
        if previous is not None:
            _append_issue(
                issues,
                ValidationSeverity.ERROR,
                ValidationIssueCode.DUPLICATE_ID,
                path,
                f"ID {identifier!r} duplicates {previous}.",
            )
        else:
            all_ids[identifier] = path

    for index, region in enumerate(document_ir.regions):
        register(region.region_id, f"$.regions[{index}].region_id")
    for index, element in enumerate(document_ir.elements):
        register(element.element_id, f"$.elements[{index}].element_id")
        for evidence_index, evidence in enumerate(element.text_evidence):
            register(
                evidence.evidence_id,
                f"$.elements[{index}].text_evidence[{evidence_index}].evidence_id",
            )
    for index, candidate in enumerate(document_ir.field_candidates):
        register(candidate.candidate_id, f"$.field_candidates[{index}].candidate_id")
    for index, relation in enumerate(document_ir.relations):
        register(relation.relation_id, f"$.relations[{index}].relation_id")
    for index, uncertainty in enumerate(document_ir.uncertainties):
        register(uncertainty.uncertainty_id, f"$.uncertainties[{index}].uncertainty_id")

    region_ids = {region.region_id for region in document_ir.regions}
    element_ids = {element.element_id for element in document_ir.elements}
    structural_ids = region_ids | element_ids
    text_evidence_ids = {
        evidence.evidence_id
        for element in document_ir.elements
        for evidence in element.text_evidence
    }
    observable_evidence_ids = structural_ids | text_evidence_ids

    for index, region in enumerate(document_ir.regions):
        if region.page_index not in page_index_set:
            _append_issue(
                issues,
                ValidationSeverity.ERROR,
                ValidationIssueCode.PAGE_REFERENCE_INVALID,
                f"$.regions[{index}].page_index",
                "Region references a page that does not exist.",
            )
        _check_unique_references(region.evidence_ids, path=f"$.regions[{index}].evidence_ids", issues=issues)
        for evidence_id in region.evidence_ids:
            if evidence_id not in observable_evidence_ids:
                _append_issue(
                    issues,
                    ValidationSeverity.ERROR,
                    ValidationIssueCode.EVIDENCE_REFERENCE_INVALID,
                    f"$.regions[{index}].evidence_ids",
                    f"Evidence reference does not resolve: {evidence_id}",
                )

    for index, element in enumerate(document_ir.elements):
        if element.page_index not in page_index_set:
            _append_issue(
                issues,
                ValidationSeverity.ERROR,
                ValidationIssueCode.PAGE_REFERENCE_INVALID,
                f"$.elements[{index}].page_index",
                "Element references a page that does not exist.",
            )
        _check_unique_references(element.evidence_ids, path=f"$.elements[{index}].evidence_ids", issues=issues)
        for evidence_id in element.evidence_ids:
            if evidence_id not in observable_evidence_ids:
                _append_issue(
                    issues,
                    ValidationSeverity.ERROR,
                    ValidationIssueCode.EVIDENCE_REFERENCE_INVALID,
                    f"$.elements[{index}].evidence_ids",
                    f"Evidence reference does not resolve: {evidence_id}",
                )

    for index, candidate in enumerate(document_ir.field_candidates):
        if candidate.target_element_id not in element_ids:
            _append_issue(
                issues,
                ValidationSeverity.ERROR,
                ValidationIssueCode.FIELD_TARGET_INVALID,
                f"$.field_candidates[{index}].target_element_id",
                "Field candidate target must resolve to an element.",
            )
        _check_unique_references(candidate.evidence_ids, path=f"$.field_candidates[{index}].evidence_ids", issues=issues)
        for evidence_id in candidate.evidence_ids:
            if evidence_id not in observable_evidence_ids:
                _append_issue(
                    issues,
                    ValidationSeverity.ERROR,
                    ValidationIssueCode.EVIDENCE_REFERENCE_INVALID,
                    f"$.field_candidates[{index}].evidence_ids",
                    f"Evidence reference does not resolve: {evidence_id}",
                )

    for index, relation in enumerate(document_ir.relations):
        if relation.source_id not in structural_ids or relation.target_id not in structural_ids:
            _append_issue(
                issues,
                ValidationSeverity.ERROR,
                ValidationIssueCode.RELATION_ENDPOINT_INVALID,
                f"$.relations[{index}]",
                "Relation endpoints must resolve to region/element observations.",
            )
        _check_unique_references(relation.evidence_ids, path=f"$.relations[{index}].evidence_ids", issues=issues)
        for evidence_id in relation.evidence_ids:
            if evidence_id not in observable_evidence_ids:
                _append_issue(
                    issues,
                    ValidationSeverity.ERROR,
                    ValidationIssueCode.EVIDENCE_REFERENCE_INVALID,
                    f"$.relations[{index}].evidence_ids",
                    f"Evidence reference does not resolve: {evidence_id}",
                )

    for index, uncertainty in enumerate(document_ir.uncertainties):
        _check_unique_references(uncertainty.evidence_ids, path=f"$.uncertainties[{index}].evidence_ids", issues=issues)
        for evidence_id in uncertainty.evidence_ids:
            if evidence_id not in observable_evidence_ids:
                _append_issue(
                    issues,
                    ValidationSeverity.ERROR,
                    ValidationIssueCode.EVIDENCE_REFERENCE_INVALID,
                    f"$.uncertainties[{index}].evidence_ids",
                    f"Evidence reference does not resolve: {evidence_id}",
                )
        _append_issue(
            issues,
            ValidationSeverity.WARNING,
            ValidationIssueCode.DOCUMENT_UNCERTAINTY,
            f"$.uncertainties[{index}]",
            f"Explicit document uncertainty: {uncertainty.code.value}",
        )

    errors = [issue for issue in issues if issue.severity is ValidationSeverity.ERROR]
    warnings = [issue for issue in issues if issue.severity is ValidationSeverity.WARNING]
    if errors:
        status = ValidationStatus.FAIL
    elif warnings:
        status = ValidationStatus.PASS_WITH_WARNINGS
    else:
        status = ValidationStatus.PASS

    return DocumentIRValidationReport(status=status, issues=tuple(issues))


def require_valid_document_ir(document_ir: object) -> DocumentIR:
    """Return DocumentIR only when deterministic validation accepts it."""

    report = validate_document_ir(document_ir)
    if not report.is_valid:
        raise DocumentIRValidationError(report)
    assert isinstance(document_ir, DocumentIR)
    return document_ir
