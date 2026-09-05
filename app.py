"""Single-file Streamlit QR Code Generator Application (app.py).

Comprehensive production release featuring:
- Instant real-time QR generation.
- Dynamic Preview synced with chosen resolution & style.
- Security warnings (SSRF / Data length checks).
- HTML/JS Clipboard Copying component.
- Vector SVG & HD PNG exports.
"""

from io import BytesIO
import ipaddress
import logging
from typing import Final
from urllib.parse import urlparse

from PIL import Image
import qrcode
import qrcode.image.svg
import streamlit as st
import streamlit.components.v1 as components

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("QRCodeApp")

# Error Correction Mapping
ERROR_CORRECTION_MAP: Final[dict[str, int]] = {
    "Low (7%)": qrcode.constants.ERROR_CORRECT_L,
    "Medium (15%)": qrcode.constants.ERROR_CORRECT_M,
    "Quartile (25%)": qrcode.constants.ERROR_CORRECT_Q,
    "High (30% - Best for print)": qrcode.constants.ERROR_CORRECT_H,
}


# --- Helper Functions & Security Checks ---
def validate_url(url: str) -> bool:
    """Checks if the given string is a valid HTTP/HTTPS URL structure."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def check_security_warnings(url: str) -> list[str]:
    """Inspects URL for potential security or usability issues (SSRF / Data Length)."""
    warnings = []
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""

        # Check for Private IP / Localhost (SSRF Prevention)
        if hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
            warnings.append("⚠️ ลิงก์นี้ชี้ไปที่ Localhost/Internal Network อาจไม่สามารถสแกนจากอุปกรณ์ภายนอกได้")
        else:
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private:
                    warnings.append("⚠️ ลิงก์นี้ชี้ไปที่ Private IP Address (Internal Network)")
            except ValueError:
                pass

        # Check Data Length
        if len(url) > 100:
            warnings.append("💡 ลิงก์มีความยาวมาก อาจทำให้ลาย QR Code ถี่และสแกนยากขึ้น แนะนำให้ย่อลิงก์ก่อน")

    except Exception as exc:
        logger.warning("Security check warning: %s", exc)

    return warnings


@st.cache_data(show_spinner=False)
def generate_png_qr(
    data: str,
    target_size: int = 500,
    fill_color: str = "#000000",
    back_color: str = "#FFFFFF",
    error_correction_key: str = "Medium (15%)",
) -> bytes:
    """Generates a PNG QR Code with custom colors and resolution."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECTION_MAP.get(error_correction_key, qrcode.constants.ERROR_CORRECT_M),
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGB")

    if target_size != qr_img.size[0]:
        qr_img = qr_img.resize((target_size, target_size), Image.Resampling.LANCZOS)

    with BytesIO() as buffer:
        qr_img.save(buffer, format="PNG")
        return buffer.getvalue()


@st.cache_data(show_spinner=False)
def generate_svg_qr(
    data: str,
    fill_color: str = "#000000",
    error_correction_key: str = "Medium (15%)",
) -> str:
    """Generates an infinite-scale Vector SVG string."""
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECTION_MAP.get(error_correction_key, qrcode.constants.ERROR_CORRECT_M),
        box_size=10,
        border=4,
        image_factory=factory,
    )
    qr.add_data(data)
    qr.make(fit=True)

    svg_img = qr.make_image(fill_color=fill_color)
    with BytesIO() as buffer:
        svg_img.save(buffer)
        return buffer.getvalue().decode("utf-8")


def render_copy_button(text_to_copy: str) -> None:
    """Renders a JavaScript-powered Copy to Clipboard button component."""
    html_code = f"""
    <button id="copyBtn" onclick="copyToClipboard()" style="
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        font-weight: bold;
    ">📋 Copy URL to Clipboard</button>

    <script>
    function copyToClipboard() {{
        navigator.clipboard.writeText("{text_to_copy}").then(function() {{
            var btn = document.getElementById('copyBtn');
            btn.innerText = '✅ Copied!';
            btn.style.backgroundColor = '#2E7D32';
            setTimeout(function() {{
                btn.innerText = '📋 Copy URL to Clipboard';
                btn.style.backgroundColor = '#4CAF50';
            }}, 2000);
        }});
    }}
    </script>
    """
    components.html(html_code, height=45)


def inject_custom_css() -> None:
    """Injects custom CSS to align download buttons and styling."""
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
    st.caption("High-Resolution Vector & Raster Image Support with Full Security Checks")

    raw_url = st.text_input(
        "Enter your link here:",
        placeholder="https://example.com",
        help="Type or paste a valid web address",
        key="url_input",
    )

    clean_url = raw_url.strip()

    if clean_url:
        if not validate_url(clean_url):
            st.warning("⚠️ Please enter a valid URL (e.g., https://example.com)")
            return

        # 1. Security & Error Resilience Warnings
        sec_warnings = check_security_warnings(clean_url)
        for warn in sec_warnings:
            st.warning(warn)

        # Style Customization Accordion
        with st.expander("🎨 Customize QR Code Style & Quality", expanded=False):
            col_fg, col_bg = st.columns(2)
            with col_fg:
                fill_color = st.color_picker("QR Color (จุด QR)", "#000000")
            with col_bg:
                back_color = st.color_picker("Background Color (พื้นหลัง)", "#FFFFFF")

            error_correction = st.selectbox(
                "Error Correction (ความสามารถในการฟื้นฟูข้อมูล):",
                options=list(ERROR_CORRECTION_MAP.keys()),
                index=1,
                help="ระดับสูงขึ้นจะช่วยให้สแกนได้แม้อยู่บนพื้นผิวที่ไม่เรียบหรือชำรุด",
            )

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

        dimension_map = {
            "Standard (500px)": 500,
            "High HD (1000px)": 1000,
            "Ultra 4K (2000px)": 2000,
        }
        target_px = dimension_map[resolution]

        try:
            # 2. Dynamic Preview: Generates preview according to target size and chosen colors
            display_png_bytes = generate_png_qr(
                clean_url,
                target_size=target_px,
                fill_color=fill_color,
                back_color=back_color,
                error_correction_key=error_correction,
            )

            st.markdown("---")

            # Center alignment layout
            _, center_col, _ = st.columns([1, 2, 1])

            with center_col:
                st.image(
                    display_png_bytes,
                    caption=f"Preview ({target_px}px x {target_px}px)",
                    use_container_width=True,
                )

                # 3. Copy to Clipboard Component
                render_copy_button(clean_url)

                if "SVG" in file_format:
                    svg_data = generate_svg_qr(
                        clean_url,
                        fill_color=fill_color,
                        error_correction_key=error_correction,
                    )
                    st.download_button(
                        label="📥 Download Vector (SVG)",
                        data=svg_data,
                        file_name="qr_code.svg",
                        mime="image/svg+xml",
                        type="primary",
                    )
                else:
                    st.download_button(
                        label=f"📥 Download PNG ({target_px}px)",
                        data=display_png_bytes,
                        file_name=f"qr_code_{target_px}px.png",
                        mime="image/png",
                        type="primary",
                    )

        except Exception as err:
            logger.error("Failed to generate QR: %s", err)
            st.error("An error occurred while generating the QR code.")


if __name__ == "__main__":
    main()
