"""Single-file Streamlit QR Code Generator Application (app.py).

Comprehensive production release featuring:
- Full-width strictly aligned action buttons (Download, Copy Image, Copy URL).
- Error Correction dropdown positioned directly underneath the Copy URL button.
- Side-by-side Layout: QR Preview on the Left, Controls & Actions on the Right.
- High-definition crisp QR rendering up to 4000px Ultra HD.
- Full security checks for URLs.
"""

import base64
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

        if hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
            warnings.append("⚠️ ลิงก์นี้ชี้ไปที่ Localhost/Internal Network อาจไม่สามารถสแกนจากอุปกรณ์ภายนอกได้")
        else:
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private:
                    warnings.append("⚠️ ลิงก์นี้ชี้ไปที่ Private IP Address (Internal Network)")
            except ValueError:
                pass

        if len(url) > 100:
            warnings.append("💡 ลิงก์มีความยาวมาก อาจทำให้ลาย QR Code ถี่และสแกนยากขึ้น แนะนำให้ย่อลิงก์ก่อน")

    except Exception as exc:
        logger.warning("Security check warning: %s", exc)

    return warnings


@st.cache_data(show_spinner=False)
def generate_raster_qr(
    data: str,
    target_size: int = 1000,
    fill_color: str = "#000000",
    back_color: str = "#FFFFFF",
    error_correction_key: str = "Medium (15%)",
    fmt: str = "PNG",
) -> bytes:
    """Generates ultra-crisp Raster QR Codes (PNG, JPG, WEBP)."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECTION_MAP.get(error_correction_key, qrcode.constants.ERROR_CORRECT_M),
        box_size=20,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGB")

    if target_size != qr_img.size[0]:
        qr_img = qr_img.resize((target_size, target_size), Image.Resampling.NEAREST)

    with BytesIO() as buffer:
        save_fmt = fmt.upper()
        if save_fmt == "JPG":
            save_fmt = "JPEG"
            qr_img.save(buffer, format=save_fmt, quality=100, subsampling=0)
        else:
            qr_img.save(buffer, format=save_fmt, quality=100)
            
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
        box_size=20,
        border=4,
        image_factory=factory,
    )
    qr.add_data(data)
    qr.make(fit=True)

    svg_img = qr.make_image(fill_color=fill_color)
    with BytesIO() as buffer:
        svg_img.save(buffer)
        return buffer.getvalue().decode("utf-8")


def render_copy_image_button(img_bytes: bytes) -> None:
    """Renders a custom HTML/JS button that copies the actual PNG image to system clipboard."""
    b64_img = base64.b64encode(img_bytes).decode("utf-8")
    
    html_code = f"""
    <style>
        body {{ margin: 0; padding: 0; background: transparent; }}
        .btn {{
            width: 100%;
            height: 45px;
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            box-shadow: 0px 2px 4px rgba(0,0,0,0.15);
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        .btn:hover {{ background-color: #1976D2; }}
    </style>

    <button id="copyImgBtn" class="btn" onclick="copyImageToClipboard()">🖼️ Copy Image</button>

    <script>
    async function copyImageToClipboard() {{
        const btn = document.getElementById('copyImgBtn');
        try {{
            const base64Data = "data:image/png;base64,{b64_img}";
            const response = await fetch(base64Data);
            const blob = await response.blob();

            await navigator.clipboard.write([
                new ClipboardItem({{ 'image/png': blob }})
            ]);

            btn.innerText = '✅ Image Copied!';
            btn.style.backgroundColor = '#2E7D32';
            setTimeout(() => {{
                btn.innerText = '🖼️ Copy Image';
                btn.style.backgroundColor = '#2196F3';
            }}, 2000);
        }} catch (err) {{
            console.error('Failed to copy image: ', err);
            btn.innerText = '❌ Failed';
            btn.style.backgroundColor = '#D32F2F';
            setTimeout(() => {{
                btn.innerText = '🖼️ Copy Image';
                btn.style.backgroundColor = '#2196F3';
            }}, 2000);
        }}
    }}
    </script>
    """
    components.html(html_code, height=50)


def render_copy_url_button(text_to_copy: str) -> None:
    """Renders a custom HTML/JS button that copies URL text to system clipboard."""
    html_code = f"""
    <style>
        body {{ margin: 0; padding: 0; background: transparent; }}
        .btn {{
            width: 100%;
            height: 45px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            box-shadow: 0px 2px 4px rgba(0,0,0,0.15);
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        .btn:hover {{ background-color: #388E3C; }}
    </style>

    <button id="copyUrlBtn" class="btn" onclick="copyUrlToClipboard()">🔗 Copy URL</button>

    <script>
    function copyUrlToClipboard() {{
        const btn = document.getElementById('copyUrlBtn');
        navigator.clipboard.writeText("{text_to_copy}").then(() => {{
            btn.innerText = '✅ URL Copied!';
            btn.style.backgroundColor = '#2E7D32';
            setTimeout(() => {{
                btn.innerText = '🔗 Copy URL';
                btn.style.backgroundColor = '#4CAF50';
            }}, 2000);
        }}).catch(err => {{
            btn.innerText = '❌ Failed';
            btn.style.backgroundColor = '#D32F2F';
            setTimeout(() => {{
                btn.innerText = '🔗 Copy URL';
                btn.style.backgroundColor = '#4CAF50';
            }}, 2000);
        }});
    }}
    </script>
    """
    components.html(html_code, height=50)


def inject_custom_css() -> None:
    """Injects strong custom CSS to force Streamlit download button to 100% width."""
    st.markdown(
        """
        <style>
        /* Force Download Button Wrapper and Button to 100% full width */
        div[data-testid="stDownloadButton"],
        div[data-testid="stDownloadButton"] > button,
        div.stDownloadButton,
        div.stDownloadButton > button {
            width: 100% !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            height: 45px !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            margin: 0 !important;
        }

        /* Image Display Crispness */
        div[data-testid="stImage"] > img {
            image-rendering: pixelated !important;
            image-rendering: -moz-crisp-edges !important;
            image-rendering: crisp-edges !important;
            border-radius: 8px;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.2);
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

    if "resolution_val" not in st.session_state:
        st.session_state.resolution_val = 1000

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

        sec_warnings = check_security_warnings(clean_url)
        for warn in sec_warnings:
            st.warning(warn)

        # Style Customization Expander (Color Picker only)
        with st.expander("🎨 Customize QR Colors", expanded=False):
            col_fg, col_bg = st.columns(2)
            with col_fg:
                fill_color = st.color_picker("QR Color (จุด QR)", "#000000")
            with col_bg:
                back_color = st.color_picker("Background Color (พื้นหลัง)", "#FFFFFF")

        # Centered Format Selector
        _, center_fmt_col, _ = st.columns([0.2, 2.6, 0.2])
        with center_fmt_col:
            file_format = st.radio(
                "Export File Format (ชนิดไฟล์):",
                options=["PNG", "JPG", "WEBP", "SVG (Vector)"],
                horizontal=True,
            )

        is_vector = "SVG" in file_format

        # Resolution Slider
        target_px = st.slider(
            "Resolution / ความละเอียดภาพ (px):",
            min_value=250,
            max_value=4000,
            key="resolution_val",
            step=50,
            disabled=is_vector,
            help="สำหรับ SVG จะถูก Fix คุณภาพไว้สูงสุดอัตโนมัติ ไม่จำเป็นต้องปรับขนาดพิกเซล" if is_vector else "ปรับขนาดความละเอียดพิกเซลภาพได้สูงสุดถึง 4000px Ultra HD",
        )

        try:
            st.markdown("---")

            # Initialize Error Correction key in session_state if missing
            if "ec_level" not in st.session_state:
                st.session_state.ec_level = "Medium (15%)"

            # Generate PNG binary specifically for Preview and Image Copying
            render_px = max(target_px, 1000) if not is_vector else 1000
            png_bytes_for_copy = generate_raster_qr(
                clean_url,
                target_size=render_px,
                fill_color=fill_color,
                back_color=back_color,
                error_correction_key=st.session_state.ec_level,
                fmt="PNG",
            )

            caption_text = "Preview (SVG Vector - Infinite Resolution)" if is_vector else f"Preview ({target_px}px x {target_px}px)"

            # Split Layout: Left Column (Preview) | Right Column (Buttons + Controls)
            col_left, col_right = st.columns([1.2, 1], gap="medium")

            # Left Column: Image Preview
            with col_left:
                st.image(
                    png_bytes_for_copy,
                    caption=caption_text,
                    use_container_width=True,
                )

            # Right Column: Stacked Buttons & Error Correction Underneath
            with col_right:
                st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)

                # 1. Download Button (Top)
                if is_vector:
                    svg_data = generate_svg_qr(
                        clean_url,
                        fill_color=fill_color,
                        error_correction_key=st.session_state.ec_level,
                    )
                    st.download_button(
                        label="📥 Download SVG",
                        data=svg_data,
                        file_name="qr_code.svg",
                        mime="image/svg+xml",
                        type="primary",
                        use_container_width=True,
                    )
                else:
                    mime_map = {
                        "PNG": "image/png",
                        "JPG": "image/jpeg",
                        "WEBP": "image/webp",
                    }
                    download_bytes = generate_raster_qr(
                        clean_url,
                        target_size=target_px,
                        fill_color=fill_color,
                        back_color=back_color,
                        error_correction_key=st.session_state.ec_level,
                        fmt=file_format,
                    )
                    st.download_button(
                        label=f"📥 Download {file_format}",
                        data=download_bytes,
                        file_name=f"qr_code_{target_px}px.{file_format.lower()}",
                        mime=mime_map.get(file_format, "image/png"),
                        type="primary",
                        use_container_width=True,
                    )

                st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)

                # 2. Copy Image Button (Middle)
                render_copy_image_button(png_bytes_for_copy)

                st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)

                # 3. Copy URL Button (Bottom)
                render_copy_url_button(clean_url)

                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

                # 4. Error Correction Dropdown (Positioned UNDER Copy URL)
                st.selectbox(
                    "Error Correction (การฟื้นฟูข้อมูล):",
                    options=list(ERROR_CORRECTION_MAP.keys()),
                    key="ec_level",
                    help="ระดับสูงขึ้นจะช่วยให้สแกนได้แม้อยู่บนพื้นผิวที่ไม่เรียบหรือชำรุด",
                )

        except Exception as err:
            logger.error("Failed to generate QR: %s", err)
            st.error("An error occurred while generating the QR code.")


if __name__ == "__main__":
    main()
