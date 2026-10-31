from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2app.understanding import NormalizedBox, VisualObservationBatch
from paper2app.understanding.providers import (
    OCRObservationBatch,
    OCRTextObservation,
    ProviderCallPolicy,
    ProviderError,
    ProviderFailureCode,
    ProviderIdentity,
    ProviderImage,
    ProviderKind,
    run_ocr_provider,
    run_vision_provider,
)


VISION_IDENTITY = ProviderIdentity(
    kind=ProviderKind.VISION,
    provider_name="fake-vision",
    adapter_version="1.0",
    model_id="fake-vision-model",
    prompt_version="vision-prompt-v1",
)

OCR_IDENTITY = ProviderIdentity(
    kind=ProviderKind.OCR,
    provider_name="fake-ocr",
    adapter_version="1.0",
    model_id="fake-ocr-model",
)

IMAGE = ProviderImage(
    source_id="src_123",
    normalized_sha256="a" * 64,
    media_type="image/png",
    width=1200,
    height=800,
    content=b"canonical-png-bytes",
)

OCR_BATCH = OCRObservationBatch(
    page_count=1,
    observations=(
        OCRTextObservation(
            observation_id="ocr_1",
            page_index=0,
            bbox=NormalizedBox(0.1, 0.2, 0.3, 0.05),
            raw_text="DATE :",
            normalized_text="Date",
            provider_confidence=0.94,
        ),
    ),
)


class StaticVisionProvider:
    identity = VISION_IDENTITY

    def __init__(self, response: object = None) -> None:
        self.response = response if response is not None else VisualObservationBatch(page_count=1)
        self.calls = 0

    def analyze(self, image: ProviderImage) -> object:
        self.calls += 1
        return self.response


class StaticOCRProvider:
    identity = OCR_IDENTITY

    def __init__(self, response: object = None) -> None:
        self.response = response if response is not None else OCR_BATCH
        self.calls = 0

    def extract(self, image: ProviderImage) -> object:
        self.calls += 1
        return self.response


class RetryVisionProvider:
    identity = VISION_IDENTITY

    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    def analyze(self, image: ProviderImage) -> VisualObservationBatch:
        self.calls += 1
        if self.calls <= self.failures:
            raise ProviderError(
                ProviderFailureCode.VISION_FAILED,
                "temporary vision failure",
                retryable=True,
            )
        return VisualObservationBatch(page_count=1)


class RetryOCRProvider:
    identity = OCR_IDENTITY

    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    def extract(self, image: ProviderImage) -> OCRObservationBatch:
        self.calls += 1
        if self.calls <= self.failures:
            raise ProviderError(
                ProviderFailureCode.OCR_FAILED,
                "temporary OCR failure",
                retryable=True,
            )
        return OCR_BATCH


class NonRetryableVisionProvider:
    identity = VISION_IDENTITY

    def __init__(self) -> None:
        self.calls = 0

    def analyze(self, image: ProviderImage) -> VisualObservationBatch:
        self.calls += 1
        raise ProviderError(
            ProviderFailureCode.VISION_FAILED,
            "permanent vision failure",
            retryable=False,
        )


class ExplodingOCRProvider:
    identity = OCR_IDENTITY

    def __init__(self) -> None:
        self.calls = 0

    def extract(self, image: ProviderImage) -> OCRObservationBatch:
        self.calls += 1
        raise RuntimeError("provider-specific secret failure")


class WrongKindProvider:
    identity = OCR_IDENTITY

    def analyze(self, image: ProviderImage) -> VisualObservationBatch:
        return VisualObservationBatch(page_count=1)


class ProviderPortTests(unittest.TestCase):
    def test_provider_identity_preserves_version_and_prompt_metadata(self) -> None:
        self.assertEqual(VISION_IDENTITY.kind, ProviderKind.VISION)
        self.assertEqual(VISION_IDENTITY.adapter_version, "1.0")
        self.assertEqual(VISION_IDENTITY.model_id, "fake-vision-model")
        self.assertEqual(VISION_IDENTITY.prompt_version, "vision-prompt-v1")

    def test_provider_image_requires_canonical_png(self) -> None:
        with self.assertRaises(ValueError):
            ProviderImage(
                source_id="src_x",
                normalized_sha256="a" * 64,
                media_type="image/jpeg",
                width=1,
                height=1,
                content=b"x",
            )

    def test_provider_image_requires_sha256_shape(self) -> None:
        with self.assertRaises(ValueError):
            ProviderImage(
                source_id="src_x",
                normalized_sha256="not-a-sha",
                media_type="image/png",
                width=1,
                height=1,
                content=b"x",
            )

    def test_ocr_observation_preserves_raw_and_normalized_text(self) -> None:
        observation = OCR_BATCH.observations[0]
        self.assertEqual(observation.raw_text, "DATE :")
        self.assertEqual(observation.normalized_text, "Date")
        self.assertEqual(observation.provider_confidence, 0.94)

    def test_ocr_observation_rejects_invalid_confidence(self) -> None:
        with self.assertRaises(ValueError):
            OCRTextObservation(
                observation_id="ocr_bad",
                page_index=0,
                bbox=NormalizedBox(0.0, 0.0, 0.1, 0.1),
                raw_text="x",
                provider_confidence=1.5,
            )

    def test_ocr_batch_rejects_duplicate_ids(self) -> None:
        observation = OCR_BATCH.observations[0]
        with self.assertRaises(ValueError):
            OCRObservationBatch(page_count=1, observations=(observation, observation))

    def test_ocr_batch_rejects_page_reference_outside_batch(self) -> None:
        observation = OCRTextObservation(
            observation_id="ocr_2",
            page_index=1,
            bbox=NormalizedBox(0.0, 0.0, 0.1, 0.1),
            raw_text="x",
        )
        with self.assertRaises(ValueError):
            OCRObservationBatch(page_count=1, observations=(observation,))

    def test_call_policy_is_bounded_to_three_attempts(self) -> None:
        with self.assertRaises(ValueError):
            ProviderCallPolicy(max_attempts=4)
        with self.assertRaises(ValueError):
            ProviderCallPolicy(max_attempts=0)

    def test_vision_success_returns_identity_observations_and_attempt_count(self) -> None:
        provider = StaticVisionProvider()
        result = run_vision_provider(provider, IMAGE)
        self.assertEqual(result.provider, VISION_IDENTITY)
        self.assertEqual(result.observations.page_count, 1)
        self.assertEqual(result.attempts, 1)
        self.assertEqual(provider.calls, 1)

    def test_ocr_success_returns_identity_observations_and_attempt_count(self) -> None:
        provider = StaticOCRProvider()
        result = run_ocr_provider(provider, IMAGE)
        self.assertEqual(result.provider, OCR_IDENTITY)
        self.assertEqual(result.observations, OCR_BATCH)
        self.assertEqual(result.attempts, 1)
        self.assertEqual(provider.calls, 1)

    def test_retryable_vision_failure_retries_then_succeeds(self) -> None:
        provider = RetryVisionProvider(failures=1)
        result = run_vision_provider(provider, IMAGE, ProviderCallPolicy(max_attempts=2))
        self.assertEqual(result.attempts, 2)
        self.assertEqual(provider.calls, 2)

    def test_retryable_ocr_failure_stops_at_max_attempts(self) -> None:
        provider = RetryOCRProvider(failures=5)
        with self.assertRaises(ProviderError) as context:
            run_ocr_provider(provider, IMAGE, ProviderCallPolicy(max_attempts=2))
        self.assertEqual(context.exception.code, ProviderFailureCode.OCR_FAILED)
        self.assertTrue(context.exception.retryable)
        self.assertEqual(provider.calls, 2)

    def test_nonretryable_failure_is_not_retried(self) -> None:
        provider = NonRetryableVisionProvider()
        with self.assertRaises(ProviderError):
            run_vision_provider(provider, IMAGE, ProviderCallPolicy(max_attempts=3))
        self.assertEqual(provider.calls, 1)

    def test_unexpected_provider_exception_is_normalized_without_raw_message(self) -> None:
        provider = ExplodingOCRProvider()
        with self.assertRaises(ProviderError) as context:
            run_ocr_provider(provider, IMAGE)
        self.assertEqual(context.exception.code, ProviderFailureCode.OCR_FAILED)
        self.assertFalse(context.exception.retryable)
        self.assertNotIn("secret", context.exception.message)
        self.assertEqual(provider.calls, 1)

    def test_vision_invalid_response_type_fails_closed(self) -> None:
        provider = StaticVisionProvider(response="not-a-batch")
        with self.assertRaises(ProviderError) as context:
            run_vision_provider(provider, IMAGE)
        self.assertEqual(context.exception.code, ProviderFailureCode.VISION_FAILED)

    def test_ocr_invalid_response_type_fails_closed(self) -> None:
        provider = StaticOCRProvider(response="not-a-batch")
        with self.assertRaises(ProviderError) as context:
            run_ocr_provider(provider, IMAGE)
        self.assertEqual(context.exception.code, ProviderFailureCode.OCR_FAILED)

    def test_vision_rejects_multi_page_response_for_single_image_v1(self) -> None:
        provider = StaticVisionProvider(response=VisualObservationBatch(page_count=2))
        with self.assertRaises(ProviderError):
            run_vision_provider(provider, IMAGE)

    def test_provider_identity_kind_must_match_port(self) -> None:
        with self.assertRaises(ValueError):
            run_vision_provider(WrongKindProvider(), IMAGE)

    def test_mismatched_controlled_failure_code_is_normalized_to_port_owner(self) -> None:
        class BadVisionProvider:
            identity = VISION_IDENTITY

            def analyze(self, image: ProviderImage) -> VisualObservationBatch:
                raise ProviderError(
                    ProviderFailureCode.OCR_FAILED,
                    "wrong boundary",
                    retryable=True,
                )

        with self.assertRaises(ProviderError) as context:
            run_vision_provider(BadVisionProvider(), IMAGE)
        self.assertEqual(context.exception.code, ProviderFailureCode.VISION_FAILED)
        self.assertFalse(context.exception.retryable)

    def test_runner_rejects_non_provider_image_before_call(self) -> None:
        provider = StaticVisionProvider()
        with self.assertRaises(TypeError):
            run_vision_provider(provider, object())  # type: ignore[arg-type]
        self.assertEqual(provider.calls, 0)

    def test_runner_rejects_non_policy_before_call(self) -> None:
        provider = StaticOCRProvider()
        with self.assertRaises(TypeError):
            run_ocr_provider(provider, IMAGE, object())  # type: ignore[arg-type]
        self.assertEqual(provider.calls, 0)


if __name__ == "__main__":
    unittest.main()
