import io
import logging
from pathlib import PurePosixPath
from typing import Optional

import vercel_blob
from django.conf import settings
from django.core.files.base import ContentFile, File
from django.core.files.storage import Storage

logger = logging.getLogger(__name__)


class VercelBlobStorage(Storage):
    """
    Minimal Django storage backend that uploads files to Vercel Blob.

    It saves the blob URL as the stored name so `field.url` simply returns that
    public URL. Reads download the content on demand. Deletions are best effort.
    """

    def __init__(
        self,
        base_path: Optional[str] = None,
        token: Optional[str] = None,
        add_random_suffix: Optional[bool] = None,
    ):
        self.base_path = base_path or getattr(settings, "VERCEL_BLOB_BASE_PATH", "uploads")
        self.token = token or getattr(settings, "VERCEL_BLOB_TOKEN", None)
        self.add_random_suffix = (
            getattr(settings, "VERCEL_BLOB_ADD_RANDOM_SUFFIX", True)
            if add_random_suffix is None
            else add_random_suffix
        )

    # Django API
    def _open(self, name, mode="rb"):
        """Download the blob into a ContentFile."""

        import requests

        url = self.url(name)
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        content = ContentFile(resp.content)
        return content

    def _save(self, name: str, content: File):
        """Upload the file and return the blob URL as the stored name."""

        data = content.read()
        data, converted_to_jpeg = self.compress(name, data)
        if converted_to_jpeg and name.lower().endswith(".mpo"):
            name = str(PurePosixPath(name).with_suffix(".jpg"))
        path = self._build_blob_path(name)
        options = self._build_options()

        result = vercel_blob.put(path, data, options=options)
        url = result.get("url") or result.get("pathname")
        if not url:
            logger.warning("vercel_blob.put did not return a url; falling back to path")
            url = path
        return url

    def delete(self, name):
        """Best-effort delete of the blob."""

        url = self.url(name)
        try:
            vercel_blob.delete(url, options=self._build_options())
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to delete blob %s: %s", url, exc)

    def exists(self, name):
        """
        Always return False so Django won't try name deduping.
        Blob handles overwrites based on allowOverwrite option.
        """

        return False

    def url(self, name):
        """Return the stored name if it is already a URL; otherwise build it."""

        if name.startswith("http://") or name.startswith("https://"):
            return name

        base_url = getattr(settings, "VERCEL_BLOB_PUBLIC_BASE_URL", None)
        if base_url:
            return f"{base_url.rstrip('/')}/{name.lstrip('/')}"
        return name

    # Helpers
    def compress(self, name: str, data: bytes) -> tuple[bytes, bool]:
        """Compress image and normalize MPO """

        if not data:
            return data, False
        if not getattr(settings, "VERCEL_BLOB_COMPRESS_IMAGES", False):
            logger.warning("Image compression failed config")
            return data, False

        try:
            from PIL import Image, ImageOps, UnidentifiedImageError
        except Exception:
            logger.warning("Image compression failed import")
            return data, False

        try:
            with Image.open(io.BytesIO(data)) as image:
                image_format = (image.format or "").upper()
                name_lower = (name or "").lower()
                is_mpo = image_format == "MPO" or name_lower.endswith(".mpo")
                output_format = "JPEG" if is_mpo else image_format
                if output_format not in {"JPEG", "JPG", "PNG", "WEBP"}:
                    logger.debug("type", image_format)
                    return data, False
                if is_mpo:
                    try:
                        image.seek(0)
                    except EOFError:
                        logger.warning("Failed to seek to first frame in MPO")
                        pass
                image = ImageOps.exif_transpose(image)
                max_w = int(getattr(settings, "VERCEL_BLOB_MAX_WIDTH", 1920))
                max_h = int(getattr(settings, "VERCEL_BLOB_MAX_HEIGHT", 1080))
                max_w = max(1, max_w)
                max_h = max(1, max_h)
                if image.width > max_w or image.height > max_h:
                    resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
                    image.thumbnail((max_w, max_h), resample)
                output = io.BytesIO()
                save_kwargs = {"optimize": True}
                if output_format in {"JPEG", "JPG"}:
                    quality = int(getattr(settings, "VERCEL_BLOB_IMAGE_QUALITY", 70))
                    quality = max(10, min(95, quality))
                    subsampling = int(getattr(settings, "VERCEL_BLOB_JPEG_SUBSAMPLING", 2))
                    subsampling = max(0, min(2, subsampling))
                    if image.mode not in {"RGB", "L"}:
                        image = image.convert("RGB")
                    save_kwargs.update(
                        {
                            "quality": quality,
                            "progressive": True,
                            "subsampling": subsampling,
                        }
                    )
                elif output_format == "PNG":
                    level = int(getattr(settings, "VERCEL_BLOB_PNG_COMPRESS_LEVEL", 9))
                    level = max(0, min(9, level))
                    save_kwargs.update({"compress_level": level})
                elif output_format == "WEBP":
                    quality = int(getattr(settings, "VERCEL_BLOB_IMAGE_QUALITY", 70))
                    quality = max(10, min(95, quality))
                    method = int(getattr(settings, "VERCEL_BLOB_WEBP_METHOD", 6))
                    method = max(0, min(6, method))
                    save_kwargs.update({"quality": quality, "method": method})
                image.save(output, format=output_format, **save_kwargs)
                compressed = output.getvalue()
                if compressed and (is_mpo or len(compressed) < len(data)):
                    logger.debug("Compressed image %s from %d to %d bytes", name, len(data), len(compressed))
                    return compressed, is_mpo
        except UnidentifiedImageError as exc:
            logger.warning("Image compression failed")
            return data, False
        except Exception as exc:  # noqa: BLE001
            logger.warning("Image compression failed for %s: %s", name, exc)
        return data, False

    def _build_blob_path(self, name: str) -> str:
        safe = str(PurePosixPath(name).as_posix()).lstrip("/")
        if self.base_path:
            return f"{self.base_path.rstrip('/')}/{safe}"
        return safe

    def _build_options(self) -> dict:
        options = {}
        if self.token:
            options["token"] = self.token
        if self.add_random_suffix:
            options["addRandomSuffix"] = "true"
        return options
