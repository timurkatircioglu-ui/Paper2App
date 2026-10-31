from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2app.input import (
    CaptureKind,
    InputFailureCode,
    InputGateError,
    InputGatePolicy,
    RawImageInput,
    SupportedMediaType,
    gate_image_input,
)


def _png_stub(width: int = 800, height: int = 600) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\r"
        + b"IHDR"
        + width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x02\x00\x00\x00"
        + b"\x00" * 24
    )


def _jpeg_stub() -> bytes:
    return b"\xff\xd8\xff\xe0" + (b"\x00" * 24) + b"\xff\xd9"


class InputGateTests(unittest.TestCase):
    def test_accepts_png_by_content_even_when_filename_extension_disagrees(self) -> None:
        content = _png_stub()
        accepted = gate_image_input(
            RawImageInput(content=content, filename="paper.jpg", capture_kind=CaptureKind.SCAN)
        )
        self.assertIs(accepted.media_type, SupportedMediaType.PNG)
        self.assertEqual(accepted.filename, "paper.jpg")
        self.assertIs(accepted.capture_kind, CaptureKind.SCAN)
        self.assertEqual(accepted.byte_size, len(content))

    def test_accepts_jpeg_and_preserves_upload_capture_kind(self) -> None:
        accepted = gate_image_input(
            RawImageInput(
                content=_jpeg_stub(),
                filename="form.jpeg",
                capture_kind=CaptureKind.UPLOAD,
            )
        )
        self.assertIs(accepted.media_type, SupportedMediaType.JPEG)
        self.assertIs(accepted.capture_kind, CaptureKind.UPLOAD)

    def test_source_identity_and_sha_are_deterministic(self) -> None:
        content = _png_stub(1024, 768)
        expected_digest = hashlib.sha256(content).hexdigest()
        first = gate_image_input(RawImageInput(content=content, filename="a.png"))
        second = gate_image_input(RawImageInput(content=content, filename="b.png"))
        self.assertEqual(first.sha256, expected_digest)
        self.assertEqual(second.sha256, expected_digest)
        self.assertEqual(first.source_id, f"src_{expected_digest[:24]}")
        self.assertEqual(second.source_id, first.source_id)

    def test_filename_is_reduced_to_safe_basename(self) -> None:
        accepted = gate_image_input(
            RawImageInput(content=_png_stub(), filename=r"C:\\private\\incoming\\form.png")
        )
        self.assertEqual(accepted.filename, "form.png")

    def test_rejects_unsupported_content_signature(self) -> None:
        with self.assertRaises(InputGateError) as context:
            gate_image_input(
                RawImageInput(content=b"GIF89a" + (b"x" * 32), filename="form.png")
            )
        self.assertIs(context.exception.code, InputFailureCode.INPUT_UNSUPPORTED)

    def test_rejects_png_with_missing_ihdr(self) -> None:
        corrupt = b"\x89PNG\r\n\x1a\n" + (b"x" * 40)
        with self.assertRaises(InputGateError) as context:
            gate_image_input(RawImageInput(content=corrupt, filename="broken.png"))
        self.assertIs(context.exception.code, InputFailureCode.IMAGE_CORRUPT)

    def test_rejects_jpeg_with_missing_end_marker(self) -> None:
        corrupt = b"\xff\xd8\xff\xe0" + (b"x" * 24)
        with self.assertRaises(InputGateError) as context:
            gate_image_input(RawImageInput(content=corrupt, filename="broken.jpg"))
        self.assertIs(context.exception.code, InputFailureCode.IMAGE_CORRUPT)

    def test_rejects_source_over_configured_byte_limit(self) -> None:
        content = _png_stub()
        policy = InputGatePolicy(max_bytes=len(content) - 1, min_bytes=16)
        with self.assertRaises(InputGateError) as context:
            gate_image_input(RawImageInput(content=content), policy=policy)
        self.assertIs(context.exception.code, InputFailureCode.INPUT_UNSUPPORTED)

    def test_policy_rejects_invalid_bounds(self) -> None:
        with self.assertRaises(ValueError):
            InputGatePolicy(max_bytes=8, min_bytes=16)


if __name__ == "__main__":
    unittest.main()
