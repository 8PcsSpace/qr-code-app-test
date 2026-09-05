# test_app.py
import pytest
from unittest.mock import MagicMock, patch
import httpx

from app import (
    QRCodeEngine,
    ImgurUploaderService,
    validate_url,
    validate_image_stream,
    InvalidInputError,
    ImageUploadError,
)

# --- Unit Tests for Validation ---
def test_validate_url_valid():
    assert validate_url("https://www.python.org") is True
    assert validate_url("http://localhost:8000") is True


def test_validate_url_invalid():
    assert validate_url("ftp://invalid-scheme.com") is False
    assert validate_url("not-a-url") is False
    assert validate_url("") is False


def test_validate_image_stream_oversized():
    huge_fake_bytes = b"0" * (6 * 1024 * 1024)  # 6 MB
    with pytest.raises(InvalidInputError, match="exceeds limit"):
        validate_image_stream(huge_fake_bytes)


# --- Unit Tests for QR Engine ---
def test_qr_code_generation_success():
    engine = QRCodeEngine()
    result_bytes = engine.generate_qr("https://example.com")
    
    assert isinstance(result_bytes, bytes)
    assert len(result_bytes) > 0
    assert result_bytes.startswith(b"\x89PNG")  # PNG Magic Bytes Check


def test_qr_code_generation_empty_data():
    engine = QRCodeEngine()
    with pytest.raises(InvalidInputError):
        engine.generate_qr("   ")


# --- Unit Tests for Uploader Service (Mocked) ---
@patch("httpx.Client.post")
def test_imgur_upload_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": True,
        "data": {"link": "https://i.imgur.com/test.png"}
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    service = ImgurUploaderService(client_id="dummy_id")
    url = service.upload_image(b"fake_image_bytes")

    assert url == "https://i.imgur.com/test.png"
    mock_post.assert_called_once()


@patch("httpx.Client.post")
def test_imgur_upload_http_failure(mock_post):
    mock_post.side_effect = httpx.HTTPStatusError(
        "Forbidden",
        request=MagicMock(),
        response=MagicMock(status_code=403)
    )

    service = ImgurUploaderService(client_id="dummy_id")
    with pytest.raises(ImageUploadError, match="HTTP status 403"):
        service.upload_image(b"fake_image_bytes")
