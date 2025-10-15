import pytest
from unittest.mock import patch, MagicMock
from services.document_processor import DocumentProcessor
# No auth in application anymore


@pytest.fixture
def document_processor():
    return DocumentProcessor()


@pytest.mark.asyncio
async def test_process_pdf(document_processor):
    mock_page = MagicMock()
    mock_page.get_text.return_value = "This is a test PDF file."
    mock_page.get_pixmap.return_value = MagicMock(tobytes=lambda x: b"dummy_png_bytes")

    mock_doc = MagicMock()
    mock_doc.__enter__.return_value = mock_doc
    mock_doc.__exit__.return_value = False
    mock_doc.__len__.return_value = 1
    mock_doc.load_page.return_value = mock_page

    with patch("fitz.open", return_value=mock_doc):
        with patch(
            "pytesseract.image_to_string", return_value="This is a test PDF file."
        ):
            with patch("os.path.exists", return_value=True):
                with patch("os.path.getsize", return_value=1000):
                    result = await document_processor.process_document(
                        "dummy.pdf", file_type="pdf"
                    )
                    assert result.success
                    assert "This is a test PDF file." in result.extracted_text
                    assert result.total_pages == 1


@pytest.mark.asyncio
async def test_process_image(document_processor):
    mock_image = MagicMock()
    mock_image.size = (100, 100)
    mock_image.convert.return_value = mock_image
    mock_image.filter.return_value = mock_image
    mock_image.resize.return_value = mock_image
    mock_image.enhance.return_value = mock_image

    with patch("PIL.Image.open", return_value=mock_image):
        with patch(
            "pytesseract.image_to_string", return_value="This is a test image file."
        ):
            with patch("os.path.exists", return_value=True):
                with patch("os.path.getsize", return_value=500):
                    result = await document_processor.process_document(
                        "dummy.png", file_type="image"
                    )
                    assert result.success
                    assert result.extracted_text == "This is a test image file."
                    assert result.total_pages == 1
