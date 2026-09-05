"""Single-file Streamlit QR Code Generator Application (app.py).

Enterprise-ready implementation with SOLID principles, robust validation,
error handling, and memory-optimized architecture.
"""

from dataclasses import dataclass
from enum import Enum, auto
from io import BytesIO
import logging
import os
from typing import Final, Optional, Protocol
from urllib.parse import urlparse

import httpx
from PIL import Image, UnidentifiedImageError
import qrcode
from qrcode.main import QRCode
import streamlit as st

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("QRCodeApp")

# Application Constants
MAX_IMAGE_SIZE_BYTES: Final[int] = 5 * 1024 * 1024  # 5 MB Limit
HTTP_TIMEOUT_SECONDS: Final[float] = 10.0


# --- Custom Exceptions ---
class QRAppException(Exception):
    """Base Exception"""

class ImageUploadError(QRAppException):
    """Raised when external image upload fails"""

class InvalidInputError(QRAppException):
    """Raised when validation fails"""

class QRCodeGenerationError(QRAppException):
    """Raised when QR generation fails"""


# --- Domain Models & Protocols ---
class InputType(Enum):
    URL = auto()
    IMAGE = auto()


@dataclass(frozen=True, slots=True)
class QRCodeConfig:
    version: int = 1
    error_correction: int = qrcode.constants.ERROR_CORRECT_M
    box_size: int = 10
    border: int = 4
    fill_color: str = "black"
    back_color: str = "white"


class ImageUploaderService(Protocol):
    def upload_image(self, image_bytes: bytes) -> str:
        ...


# --- Service Implementations ---
class ImgurUploaderService:
    def __init__(self, client_id: str, timeout: float = HTTP_TIMEOUT_SECONDS) -> None:
        if not client_id:
            raise InvalidInputError("Imgur Client-ID is required.")
        self._client_id = client_id
        self._timeout = timeout

    def upload_image(self, image_bytes: bytes) -> str:
        headers = {"Authorization": f"Client-ID {self._client_id}"}
        files = {"image": image_bytes}

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    "https://api.imgur.com/3/image",
                    headers=headers,
                    files=files,
                )
                response.raise_for_status()
                payload = response.json()
                
                if not payload.get("success", False):
                    raise ImageUploadError("Imgur API returned unsuccessful response.")
                
                return str(payload["data"]["link"])
        except httpx.HTTPStatusError as exc:
            logger.error("HTTP error: %s", exc)
            raise ImageUploadError(f"Upload failed (HTTP {exc.response.status_code})") from exc
        except httpx.RequestError as exc:
            logger.error("Network error: %s", exc)
            raise ImageUploadError("Network connection error. Please try again.") from exc


class QRCodeEngine:
    def __init__(self, config: Optional[QRCodeConfig] = None) -> None:
        self._config = config or QRCodeConfig()

    def generate_qr(self, data: str) -> bytes:
        if not data.strip():
            raise InvalidInputError("Data payload cannot be empty.")

        try:
            qr = QRCode(
                version=self._config.version,
                error_correction=self._config.error_correction,
                box_size=self._config.box_size,
                border=self._config.border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(
                fill_color=self._config.fill_color,
                back_color=self._config.back_color,
            )

            with BytesIO() as buffer:
                img.save(buffer, format="PNG")
                return buffer.getvalue()
        except Exception as exc:
            logger.error("QR Generation failed: %s", exc)
            raise QRCodeGenerationError("Failed to render QR Code image.") from exc


# --- Validation Helpers ---
def validate_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def validate_image_stream(image_bytes: bytes) -> None:
    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise InvalidInputError(f"File size exceeds limit of {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB.")

    try:
        with Image.open(BytesIO(image_bytes)) as img:
            img.verify()
    except (UnidentifiedImageError, Exception) as exc:
        raise InvalidInputError("Uploaded file is not a valid image format.") from exc


# --- Streamlit Presentation Layer ---
@st.cache_resource
def get_qr_engine() -> QRCodeEngine:
    return QRCodeEngine()


@st.cache_resource
def get_uploader_service() -> ImageUploaderService:
    client_id = os.getenv("IMGUR_CLIENT_ID", "544ba571c172d7e")
    return ImgurUploaderService(client_id=client_id)


def main() -> None:
    st.set_page_config(page_title="Professional QR Code Generator", page_icon="🔗")
    st.title("Online QR Code Generator 🔗")
    st.caption("Enterprise-Ready Single-File Architecture")

    qr_engine = get_qr_engine()
    uploader_service = get_uploader_service()

    input_choice = st.radio(
        "Select input type:",
        options=[InputType.URL, InputType.IMAGE],
        format_func=lambda x: "URL Link" if x == InputType.URL else "Upload Image",
    )

    target_payload: str = ""

    match input_choice:
        case InputType.URL:
            raw_url = st.text_input("Enter your link here:", placeholder="https://example.com")
            if raw_url:
                if validate_url(raw_url):
                    target_payload = raw_url
                else:
                    st.warning("⚠️ Please enter a valid URL with http:// or https://")

        case InputType.IMAGE:
            uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
            if uploaded_file is not None:
                file_bytes = uploaded_file.getvalue()
                
                try:
                    validate_image_stream(file_bytes)
                    st.image(file_bytes, caption="Preview Image", width=200)

                    if st.button("Generate QR from Image", type="primary"):
                        with st.spinner("Uploading image securely..."):
                            target_payload = uploader_service.upload_image(file_bytes)
                            st.success("Image uploaded successfully!")
                except InvalidInputError as err:
                    st.error(f"Validation Error: {err}")
                except ImageUploadError as err:
                    st.error(f"Upload Error: {err}")

    if target_payload:
        try:
            qr_bytes = qr_engine.generate_qr(target_payload)
            st.markdown("---")
            st.image(qr_bytes, caption="Your Generated QR Code", width=300)
            
            st.download_button(
                label="📥 Download QR Code",
                data=qr_bytes,
                file_name="generated_qr.png",
                mime="image/png",
            )
        except QRCodeGenerationError as err:
            st.error(f"Rendering Error: {err}")


if __name__ == "__main__":
    main()
