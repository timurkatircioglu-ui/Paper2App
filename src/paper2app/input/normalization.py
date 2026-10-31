"""Deterministic image decode and normalization for Paper2App."""

from __future__ import annotations

from io import BytesIO
import hashlib

from PIL import Image, ImageOps, UnidentifiedImageError

from .contracts import (
    DEFAULT_INPUT_GATE_POLICY,
    DEFAULT_NORMALIZATION_POLICY,
    ImageNormalizationError,
    InputFailureCode,
    InputGatePolicy,
    NormalizationPolicy,
    NormalizedImage,
    RawImageInput,
    SupportedMediaType,
)
from .gate import gate_image_input

_EXIF_ORIENTATION_TAG = 274
_EXPECTED_PIL_FORMAT = {
    SupportedMediaType.JPEG: "JPEG",
    SupportedMediaType.PNG: "PNG",
}


def _raise_corrupt(message: str) -> None:
    raise ImageNormalizationError(InputFailureCode.IMAGE_CORRUPT, message)


def _decode_verified(
    content: bytes,
    media_type: SupportedMediaType,
    policy: NormalizationPolicy,
) -> Image.Image:
    expected_format = _EXPECTED_PIL_FORMAT[media_type]

    try:
        with Image.open(BytesIO(content)) as probe:
            if probe.format != expected_format:
                _raise_corrupt(
                    f"Decoded format {probe.format!r} does not match admitted media type {media_type.value!r}."
                )

            width, height = probe.size
            pixel_count = width * height
            if pixel_count > policy.max_pixels:
                raise ImageNormalizationError(
                    InputFailureCode.INPUT_UNSUPPORTED,
                    (
                        f"Decoded image contains {pixel_count} pixels, exceeding the configured "
                        f"{policy.max_pixels}-pixel safety limit."
                    ),
                )
            if min(width, height) < policy.min_short_edge:
                raise ImageNormalizationError(
                    InputFailureCode.IMAGE_TOO_SMALL,
                    (
                        f"Decoded image short edge is {min(width, height)} px; "
                        f"minimum is {policy.min_short_edge} px."
                    ),
                )
            probe.verify()

        image = Image.open(BytesIO(content))
        if image.format != expected_format:
            image.close()
            _raise_corrupt(
                f"Decoded format {image.format!r} does not match admitted media type {media_type.value!r}."
            )
        image.load()
        return image
    except ImageNormalizationError:
        raise
    except Image.DecompressionBombError as exc:
        raise ImageNormalizationError(
            InputFailureCode.INPUT_UNSUPPORTED,
            "Image dimensions exceed the decoder safety envelope.",
        ) from exc
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise ImageNormalizationError(
            InputFailureCode.IMAGE_CORRUPT,
            "Image bytes passed the input signature gate but could not be decoded safely.",
        ) from exc


def _flatten_to_rgb(image: Image.Image) -> tuple[Image.Image, bool]:
    if "A" not in image.getbands():
        return image.convert("RGB"), False

    rgba = image.convert("RGBA")
    background = Image.new("RGB", rgba.size, "white")
    background.paste(rgba, mask=rgba.getchannel("A"))
    return background, True


def _resize_if_needed(image: Image.Image, max_long_edge: int) -> tuple[Image.Image, bool]:
    width, height = image.size
    long_edge = max(width, height)
    if long_edge <= max_long_edge:
        return image, False

    ratio = max_long_edge / long_edge
    target = (max(1, round(width * ratio)), max(1, round(height * ratio)))
    return image.resize(target, Image.Resampling.LANCZOS), True


def decode_and_normalize_image(
    raw: RawImageInput,
    *,
    input_policy: InputGatePolicy = DEFAULT_INPUT_GATE_POLICY,
    normalization_policy: NormalizationPolicy = DEFAULT_NORMALIZATION_POLICY,
) -> NormalizedImage:
    """Decode an admitted source and emit a bounded canonical PNG representation.

    The original source identity remains attached to the result. The normalized
    representation is a separate payload with its own SHA-256 identity.
    """

    source = gate_image_input(raw, policy=input_policy)
    image = _decode_verified(raw.content, source.media_type, normalization_policy)

    try:
        original_width, original_height = image.size
        exif_orientation = image.getexif().get(_EXIF_ORIENTATION_TAG)
        orientation_applied = exif_orientation not in (None, 1)
        oriented = ImageOps.exif_transpose(image)

        working, alpha_flattened = _flatten_to_rgb(oriented)
        normalized, resized = _resize_if_needed(working, normalization_policy.max_long_edge)

        output = BytesIO()
        normalized.save(output, format="PNG", optimize=False, compress_level=6)
        normalized_content = output.getvalue()
        normalized_sha256 = hashlib.sha256(normalized_content).hexdigest()

        operations = ["decode"]
        if orientation_applied:
            operations.append("exif_transpose")
        if alpha_flattened:
            operations.append("flatten_alpha_white")
        if resized:
            operations.append("resize_long_edge")
        operations.append("canonical_png")

        return NormalizedImage(
            source=source,
            original_width=original_width,
            original_height=original_height,
            normalized_width=normalized.width,
            normalized_height=normalized.height,
            exif_orientation=exif_orientation,
            orientation_applied=orientation_applied,
            resized=resized,
            normalized_media_type=SupportedMediaType.PNG,
            normalized_sha256=normalized_sha256,
            normalized_content=normalized_content,
            operations=tuple(operations),
        )
    finally:
        image.close()
