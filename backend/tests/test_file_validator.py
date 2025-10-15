import pytest
from unittest.mock import patch

from utils.file_validator import FileValidator
from PIL import Image
import io
# No auth in application anymore


class FakeUploadFile:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content
        self._pointer = 0

    async def read(self) -> bytes:
        return self._content

    async def seek(self, pos: int):
        # Simulate seek without changing content; FileValidator only calls read() again
        self._pointer = pos


@pytest.mark.asyncio
async def test_validate_file_accepts_pdf_with_correct_mime():
    validator = FileValidator()
    content = b"%PDF-1.4 test pdf content"
    file = FakeUploadFile("test.pdf", content)

    with patch("utils.file_validator.magic", create=True) as mock_magic:
        mock_magic.from_buffer.return_value = "application/pdf"
        result = await validator.validate_file(file)

    assert result.is_valid is True
    assert result.file_type == "pdf"
    assert result.file_extension == "pdf"
    assert result.file_size == len(content)


@pytest.mark.asyncio
async def test_validate_file_rejects_size_mismatch_and_wrong_mime():
    validator = FileValidator()
    large_content = b"0" * (validator.max_file_size + 1)
    file = FakeUploadFile("oversize.png", large_content)

    # Size check takes precedence
    with patch("utils.file_validator.magic", create=True) as mock_magic:
        mock_magic.from_buffer.return_value = "image/png"
        result = await validator.validate_file(file)

    assert result.is_valid is False
    assert "exceeds" in (result.error_message or "").lower()

    # Now test wrong mime vs extension
    small_file = FakeUploadFile("image.png", b"fake")
    with patch("utils.file_validator.magic", create=True) as mock_magic:
        mock_magic.from_buffer.return_value = "image/jpeg"
        result = await validator.validate_file(small_file)

    assert result.is_valid is False
    # Accept either MIME mismatch or generic content mismatch wording
    msg = (result.error_message or "").lower()
    assert ("does not match mime type" in msg) or ("does not match expected" in msg)


@pytest.mark.asyncio
async def test_validate_image_dimension_limit(monkeypatch):
    monkeypatch.setenv("MAX_IMAGE_DIMENSION", "500")
    validator = FileValidator()

    # Create large image 1000x1000
    img = Image.new("RGB", (1000, 1000), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()

    file = FakeUploadFile("big.png", data)
    with patch("utils.file_validator.magic", create=True) as mock_magic:
        mock_magic.from_buffer.return_value = "image/png"
        result = await validator.validate_file(file)

    assert result.is_valid is False
    assert "dimensions too large" in (result.error_message or "").lower()
