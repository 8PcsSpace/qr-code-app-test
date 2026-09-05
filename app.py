"""Single-file Streamlit QR Code Generator Application (app.py).

Features:
- Instant real-time QR generation (No Enter required).
- High-definition image scaling & Vector format export (SVG/PNG).
- Center-aligned Streamlit UI layout.
"""

from dataclasses import dataclass
from io import BytesIO, StringIO
import logging
from typing import Final, Optional
from urllib.parse import urlparse

import qrcode
from qrcode.image.svg import SvgPathImage
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
    """Engine responsible for rendering high-res PNG and vector SVG QR codes."""

    def __init__(self, config: Optional[QRCodeConfig] = None) -> None:
        self._config = config or QRCodeConfig()

    def generate_png(self, data: str, box_size: int) -> bytes:
        """Renders high-definition PNG binary stream."""
        if not data.strip():
            raise InvalidInputError("Payload data cannot be empty.")

        try:
            qr = QRCode(
                version=self._config.version,
                error_correction=self._config.error_correction,
                box_size=box_size,
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
            logger.error("PNG QR Generation failed: %s", exc)
            raise QRCodeGenerationError("Failed to render PNG QR Code.") from exc

    def generate_svg(self, data: str) -> str:
        """Renders infinite-scale Vector SVG string."""
        if not data.strip():
            raise InvalidInputError("Payload data cannot be empty.")

        try:
            qr = QRCode(
                version=self._config.version,
                error_correction=self._config.error_correction,
                box_size=self._config.box_size,
                border=self._config.border,
                image_factory=SvgPathImage,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image()
            buffer = BytesIO()
            img.save(buffer)
            return buffer.getvalue().decode("utf-8")
        except Exception as exc:
            logger.error("SVG Vector Generation failed: %s", exc)
            raise QRCodeGenerationError("Failed to render SVG Vector QR Code.") from exc


# --- Helper Functions ---
def validate_url(url: str) -> bool:
    """Checks if the given string is a valid HTTP/HTTPS URL structure."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def inject_custom_css() -> None:
    """Injects custom CSS to center controls and elements properly."""
    st.markdown(
        """
        <style>
        .stDownloadButton > button {
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# --- Streamlit Application ---
@st.cache_resource
def get_qr_engine() -> QRCodeEngine:
    return QRCodeEngine()


def main() -> None:
    st.set_page_config(page_title="High-Res QR Code Generator", page_icon="🔗", layout="centered")
    inject_custom_css()

    st.title("URL to QR Code Generator 🔗")
    st.caption("High-Resolution Vector & Raster Image Support")

    qr_engine = get_qr_engine()

    raw_url = st.text_input(
        "Enter your link here:",
        placeholder="https://example.com",
        help="Type or paste a valid web address",
        key="url_input"
    )

    clean_url = raw_url.strip()

    if clean_url:
        if not validate_url(clean_url):
            st.warning("⚠️ Please enter a valid URL (e.g., https://example.com)")
            return

        # Settings Options for Resolution & Vector Output
        col_res, col_fmt = st.columns(2)
        with col_res:
            resolution = st.select_slider(
                "PNG Resolution (คมชัดสูงสุด):",
                options=["Standard (500px)", "High HD (1000px)", "Ultra 4K (2000px)"],
                value="High HD (1000px)",
            )
        with col_fmt:
            file_format = st.radio(
                "Export File Format:",
                options=["PNG (Raster)", "SVG (Vector - ไม่แตก)"],
                horizontal=True,
            )

        # Map selected resolution option to box sizes
        box_size_map = {
            "Standard (500px)": 10,
            "High HD (1000px)": 20,
            "Ultra 4K (2000px)": 40,
        }
        selected_box_size = box_size_map[resolution]

        try:
            # Generate previews and buffers
            png_preview_bytes = qr_engine.generate_png(clean_url, box_size=10)

            st.markdown("---")
            
            # Center Alignment using layout columns
            _, center_col, _ = st.columns([1, 2, 1])

            with center_col:
                st.image(png_preview_bytes, caption="Your Generated QR Code", use_container_width=True)

                if "SVG" in file_format:
                    svg_data = qr_engine.generate_svg(clean_url)
                    st.download_button(
                        label="📥 Download Vector (SVG)",
                        data=svg_data,
                        file_name="qr_code.svg",
                        mime="image/svg+xml",
                        type="primary",
                    )
                else:
                    png_hd_bytes = qr_engine.generate_png(clean_url, box_size=selected_box_size)
                    st.download_button(
                        label=f"📥 Download PNG ({resolution.split()[0]})",
                        data=png_hd_bytes,
                        file_name="qr_code.png",
                        mime="image/png",
                        type="primary",
                    )

        except QRCodeGenerationError as err:
            st.error(f"Error: {err}")


if __name__ == "__main__":
    main()
