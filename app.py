"""Single-file Streamlit QR Code Generator Application (app.py).

Features:
- Instant real-time QR generation.
- High-definition image scaling & Vector SVG export.
- Center-aligned UI.
"""

from io import BytesIO, StringIO
import logging
from typing import Final
from urllib.parse import urlparse

from PIL import Image
import qrcode
import qrcode.image.svg
import streamlit as st

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("QRCodeApp")


# --- Helper Functions ---
def validate_url(url: str) -> bool:
    """Checks if the given string is a valid HTTP/HTTPS URL structure."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def generate_png_qr(data: str, target_size: int = 500) -> bytes:
    """Generates a PNG QR Code and resizes it cleanly to target resolution."""
    qr_img = qrcode.make(data)
    
    # Resize image to targeted resolution with high quality filtering
    if target_size != qr_img.size[0]:
        qr_img = qr_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
    
    with BytesIO() as buffer:
        qr_img.save(buffer, format="PNG")
        return buffer.getvalue()


def generate_svg_qr(data: str) -> str:
    """Generates an infinite-scale Vector SVG string."""
    factory = qrcode.image.svg.SvgPathImage
    svg_img = qrcode.make(data, image_factory=factory)
    
    with BytesIO() as buffer:
        svg_img.save(buffer)
        return buffer.getvalue().decode("utf-8")


def inject_custom_css() -> None:
    """Injects custom CSS to stretch download button across parent container."""
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
def main() -> None:
    st.set_page_config(page_title="High-Res QR Code Generator", page_icon="🔗", layout="centered")
    inject_custom_css()

    st.title("URL to QR Code Generator 🔗")
    st.caption("High-Resolution Vector & Raster Image Support")

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

        col_res, col_fmt = st.columns(2)
        with col_res:
            resolution = st.select_slider(
                "PNG Resolution (ความคมชัด):",
                options=["Standard (500px)", "High HD (1000px)", "Ultra 4K (2000px)"],
                value="High HD (1000px)",
            )
        with col_fmt:
            file_format = st.radio(
                "Export File Format:",
                options=["PNG (Raster)", "SVG (Vector - ไม่แตก)"],
                horizontal=True,
            )

        # Map options to pixel dimensions
        dimension_map = {
            "Standard (500px)": 500,
            "High HD (1000px)": 1000,
            "Ultra 4K (2000px)": 2000,
        }
        target_px = dimension_map[resolution]

        try:
            # Preview QR Code (Lightweight)
            preview_bytes = generate_png_qr(clean_url, target_size=400)

            st.markdown("---")
            
            # Center alignment layout
            _, center_col, _ = st.columns([1, 2, 1])

            with center_col:
                st.image(preview_bytes, caption="Your Generated QR Code", use_container_width=True)

                if "SVG" in file_format:
                    svg_data = generate_svg_qr(clean_url)
                    st.download_button(
                        label="📥 Download Vector (SVG)",
                        data=svg_data,
                        file_name="qr_code.svg",
                        mime="image/svg+xml",
                        type="primary",
                    )
                else:
                    png_hd_bytes = generate_png_qr(clean_url, target_size=target_px)
                    st.download_button(
                        label=f"📥 Download PNG ({target_px}px)",
                        data=png_hd_bytes,
                        file_name=f"qr_code_{target_px}px.png",
                        mime="image/png",
                        type="primary",
                    )

        except Exception as err:
            logger.error("Failed to generate QR: %s", err)
            st.error("An error occurred while generating the QR code.")


if __name__ == "__main__":
    main()
