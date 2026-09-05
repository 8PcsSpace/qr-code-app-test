"""Single-file Streamlit QR Code Generator Application (app.py).

Focused exclusively on URL/Text-to-QR Code generation.
Optimized for high performance, type safety, and low memory usage.
"""

from dataclasses import dataclass
from io import BytesIO
import logging
from typing import Final, Optional
from urllib.parse import urlparse

import qrcode
from qrcode.main import QRCode
import streamlit as st

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("QRCodeApp")


# --- Custom Exceptions ---
class QRAppException(Exception):
    """Base Exception for application domain."""


class InvalidInputError(QRAppException):
    """Raised when URL input validation fails."""


class QRCodeGenerationError(QRAppException):
    """Raised when QR generation fails."""


# --- Domain Models ---
@dataclass(frozen=True, slots=True)
class QRCodeConfig:
    version: int = 1
    error_correction: int = qrcode.constants.ERROR_CORRECT_M
    box_size: int = 10
    border: int = 4
    fill_color: str = "black"
    back_color: str = "white"


# --- Service Layer ---
class QRCodeEngine:
    """Engine responsible for rendering QR code image bytes."""

    def __init__(self, config: Optional[QRCodeConfig] = None) -> None:
        self._config = config or QRCodeConfig()

    def generate_qr(self, data: str) -> bytes:
        if not data.strip():
            raise InvalidInputError("Payload data cannot be empty.")

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


# --- Helper Functions ---
def validate_url(url: str) -> bool:
    """Checks if the given string is a valid HTTP/HTTPS URL structure."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


# --- Streamlit Application ---
@st.cache_resource
def get_qr_engine() -> QRCodeEngine:
    return QRCodeEngine()


def main() -> None:
    st.set_page_config(page_title="URL to QR Code Generator", page_icon="🔗")
    st.title("URL to QR Code Generator 🔗")
    st.caption("Fast & Secure QR Code Generator")

    qr_engine = get_qr_engine()

    raw_url = st.text_input(
        "Enter your link here:",
        placeholder="https://example.com",
        help="Type or paste a valid web address starting with http:// or https://"
    )

    if raw_url:
        clean_url = raw_url.strip()
        
        if not validate_url(clean_url):
            st.warning("⚠️ Please enter a valid URL (e.g., https://example.com)")
            return

        try:
            qr_bytes = qr_engine.generate_qr(clean_url)
            
            st.markdown("---")
            st.image(qr_bytes, caption="Your Generated QR Code", width=250)
            
            st.download_button(
                label="📥 Download QR Code",
                data=qr_bytes,
                file_name="qr_code.png",
                mime="image/png",
                type="primary",
            )
        except QRCodeGenerationError as err:
            st.error(f"Error: {err}")


if __name__ == "__main__":
    main()
