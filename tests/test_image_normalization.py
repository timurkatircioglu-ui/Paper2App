from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PIL import Image

from paper2app.input import (
    ImageNormalizationError,
    InputFailureCode,
    NormalizationPolicy,
    RawImageInput,
    SupportedMediaType,
    decode_and_normalize_image,
)


def _image_bytes(
    size: tuple[int, int],
    *,
    format_name: str = "PNG",
    mode: str = "RGB",
    color: tuple[int, ...] | str = "white",
    exif_orientation: int | None = None,
) -> bytes:
    image = Image.new(mode, size, color)
    output = BytesIO()
    if exif_orientation is None:
        image.save(output, format=format_name)
    else:
        exif = Image.Exif()
        exif[274] = exif_orientation
        image.save(output, format=format_name, exif=exif)
    image.close()
    return output.getvalue()


class ImageNormalizationTests(unittest.TestCase):
    def test_valid_png_decodes_and_emits_canonical_png(self) -> None:
        raw = RawImageInput(content=_image_bytes((800, 600)), filename="form.png")

        result = decode_and_normalize_image(raw)

        self.assertIs(result.source.media_type, SupportedMediaType.PNG)
        self.assertEqual((result.original_width, result.original_height), (800, 600))
        self.assertEqual((result.normalized_width, result.normalized_height), (800, 600))
        self.assertFalse(result.orientation_applied)
        self.assertFalse(result.resized)
        self.assertIs(result.normalized_media_type, SupportedMediaType.PNG)
        self.assertTrue(result.normalized_content.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(
            result.normalized_sha256,
            hashlib.sha256(result.normalized_content).hexdigest(),
        )
        self.assertEqual(result.operations, ("decode", "canonical_png"))

    def test_large_image_resizes_to_bounded_long_edge(self) -> None:
        raw = RawImageInput(content=_image_bytes((3000, 1500)), filename="large.png")

        result = decode_and_normalize_image(raw)

        self.assertTrue(result.resized)
        self.assertEqual((result.normalized_width, result.normalized_height), (2048, 1024))
        self.assertIn("resize_long_edge", result.operations)

    def test_short_edge_below_minimum_is_rejected(self) -> None:
        raw = RawImageInput(content=_image_bytes((500, 200)), filename="tiny.png")

        with self.assertRaises(ImageNormalizationError) as context:
            decode_and_normalize_image(raw)

        self.assertIs(context.exception.code, InputFailureCode.IMAGE_TOO_SMALL)

    def test_exif_orientation_is_applied_before_output(self) -> None:
        raw = RawImageInput(
            content=_image_bytes(
                (600, 1000),
                format_name="JPEG",
                exif_orientation=6,
            ),
            filename="camera.jpg",
        )

        result = decode_and_normalize_image(raw)

        self.assertEqual((result.original_width, result.original_height), (600, 1000))
        self.assertEqual((result.normalized_width, result.normalized_height), (1000, 600))
        self.assertEqual(result.exif_orientation, 6)
        self.assertTrue(result.orientation_applied)
        self.assertIn("exif_transpose", result.operations)

    def test_transparent_png_is_flattened_to_white(self) -> None:
        raw = RawImageInput(
            content=_image_bytes((640, 480), mode="RGBA", color=(0, 0, 0, 0)),
            filename="transparent.png",
        )

        result = decode_and_normalize_image(raw)

        self.assertIn("flatten_alpha_white", result.operations)
        with Image.open(BytesIO(result.normalized_content)) as normalized:
            self.assertEqual(normalized.convert("RGB").getpixel((0, 0)), (255, 255, 255))

    def test_pixel_safety_limit_rejects_before_resize(self) -> None:
        raw = RawImageInput(content=_image_bytes((1000, 1000)), filename="huge-pixels.png")
        policy = NormalizationPolicy(
            min_short_edge=320,
            max_long_edge=2048,
            max_pixels=500_000,
        )

        with self.assertRaises(ImageNormalizationError) as context:
            decode_and_normalize_image(raw, normalization_policy=policy)

        self.assertIs(context.exception.code, InputFailureCode.INPUT_UNSUPPORTED)

    def test_signature_valid_but_undecodable_png_is_rejected(self) -> None:
        corrupt = (
            b"\x89PNG\r\n\x1a\n"
            + b"\x00\x00\x00\rIHDR"
            + (800).to_bytes(4, "big")
            + (600).to_bytes(4, "big")
            + (b"\x00" * 32)
        )
        raw = RawImageInput(content=corrupt, filename="broken.png")

        with self.assertRaises(ImageNormalizationError) as context:
            decode_and_normalize_image(raw)

        self.assertIs(context.exception.code, InputFailureCode.IMAGE_CORRUPT)

    def test_same_input_produces_same_normalized_identity(self) -> None:
        content = _image_bytes((960, 720), color="white")
        first = decode_and_normalize_image(RawImageInput(content=content, filename="a.png"))
        second = decode_and_normalize_image(RawImageInput(content=content, filename="b.png"))

        self.assertEqual(first.normalized_content, second.normalized_content)
        self.assertEqual(first.normalized_sha256, second.normalized_sha256)
        self.assertEqual(first.source.source_id, second.source.source_id)


if __name__ == "__main__":
    unittest.main()
