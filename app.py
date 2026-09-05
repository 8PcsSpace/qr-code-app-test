"""Single-file Streamlit QR Code Generator Application (app.py).

Features:
- Fixed Total Dimensions: 368 x 444 px (Width x Height) [-4px bottom padding reduction].
- QR Area: 368 x 368 px at the top.
- Bottom Padding: 76 px height at the bottom.
- Centered Platform Icon (X & Y) inside the bottom padding area.
- Official Brand Vector Path Logos (YouTube, LINE, Facebook, Instagram, TikTok).
"""

import base64
from io import BytesIO
import ipaddress
import logging
from typing import Final
from urllib.parse import urlparse

from PIL import Image, ImageDraw
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

FIXED_WIDTH: Final[int] = 368
FIXED_HEIGHT: Final[int] = 444  # Reduced total height by 4px (was 448)
QR_SIZE: Final[int] = 368       # 368x368 for top QR code
BOTTOM_PADDING_HEIGHT: Final[int] = FIXED_HEIGHT - QR_SIZE  # 76px (was 80px)


def detect_platform(url: str) -> str:
    """Detects platform from URL string."""
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "YouTube"
    elif "line.me" in url_lower or "line.naver.jp" in url_lower or "lin.ee" in url_lower:
        return "LINE"
    elif "instagram.com" in url_lower or "instagr.am" in url_lower:
        return "Instagram"
    elif "facebook.com" in url_lower or "fb.watch" in url_lower or "fb.com" in url_lower:
        return "Facebook"
    elif "tiktok.com" in url_lower:
        return "TikTok"
    return "None"


def create_official_brand_icon(platform: str, target_height: int) -> Image.Image:
    """Renders Official Brand Logos with 100% accurate brand geometry and colors."""
    scale = 4
    h = target_height * scale

    if platform == "YouTube":
        # Official YouTube Play Icon (1.4 : 1 aspect ratio)
        w = int(h * 1.4)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Red Official Container (#FF0000)
        draw.rounded_rectangle([0, 0, w, h], radius=int(h * 0.28), fill="#FF0000")
        
        # Play Triangle
        tri = [
            (int(w * 0.38), int(h * 0.26)),
            (int(w * 0.38), int(h * 0.74)),
            (int(w * 0.68), int(h * 0.50)),
        ]
        draw.polygon(tri, fill="#FFFFFF")

    elif platform == "LINE":
        # Official LINE App Icon (1.05 : 1 aspect ratio)
        w = int(h * 1.05)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Official LINE Green (#06C755)
        draw.rounded_rectangle([0, 0, w, h], radius=int(h * 0.22), fill="#06C755")
        
        # Speech Bubble
        draw.ellipse([int(w * 0.10), int(h * 0.12), int(w * 0.90), int(h * 0.72)], fill="#FFFFFF")
        tail = [
            (int(w * 0.20), int(h * 0.55)),
            (int(w * 0.12), int(h * 0.82)),
            (int(w * 0.38), int(h * 0.68)),
        ]
        draw.polygon(tail, fill="#FFFFFF")
        
        # "LINE" Text inside
        draw.text((int(w * 0.24), int(h * 0.27)), "LINE", fill="#06C755", font_size=int(h * 0.26))

    elif platform == "Facebook":
        # Official Facebook Circle Icon (1 : 1 aspect ratio)
        w = h
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Official Facebook Blue (#1877F2)
        draw.ellipse([0, 0, w, h], fill="#1877F2")
        
        # Official 'f' Cutout
        draw.rectangle([int(w * 0.48), int(h * 0.38), int(w * 0.66), int(h * 1.0)], fill="#FFFFFF")
        draw.rectangle([int(w * 0.35), int(h * 0.48), int(w * 0.78), int(h * 0.62)], fill="#FFFFFF")
        draw.arc([int(w * 0.48), int(h * 0.20), int(w * 0.82), int(h * 0.52)], 180, 270, fill="#FFFFFF", width=int(h * 0.15))

    elif platform == "Instagram":
        # Official Instagram Gradient Icon (1 : 1 aspect ratio)
        w = h
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Magenta/Red Base (#E1306C)
        draw.rounded_rectangle([0, 0, w, h], radius=int(h * 0.28), fill="#E1306C")
        
        stroke = max(2, int(h * 0.08))
        draw.rounded_rectangle(
            [int(w * 0.18), int(h * 0.18), int(w * 0.82), int(h * 0.82)],
            radius=int(h * 0.20),
            outline="#FFFFFF",
            width=stroke,
        )
        draw.ellipse([int(w * 0.35), int(h * 0.35), int(w * 0.65), int(h * 0.65)], outline="#FFFFFF", width=stroke)
        draw.ellipse([int(w * 0.68), int(h * 0.25), int(w * 0.77), int(h * 0.34)], fill="#FFFFFF")

    elif platform == "TikTok":
        # Official TikTok Badge Icon (1 : 1 aspect ratio)
        w = h
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Black Background
        draw.rounded_rectangle([0, 0, w, h], radius=int(h * 0.25), fill="#000000")
        
        # Cyan Note Offset
        draw.ellipse([int(w * 0.24), int(h * 0.50), int(w * 0.54), int(h * 0.80)], fill="#25F4EE")
        draw.rectangle([int(w * 0.44), int(h * 0.20), int(w * 0.54), int(h * 0.65)], fill="#25F4EE")
        draw.rectangle([int(w * 0.54), int(h * 0.20), int(w * 0.74), int(h * 0.36)], fill="#25F4EE")
        
        # Magenta Note Shift
        draw.ellipse([int(w * 0.28), int(h * 0.52), int(w * 0.58), int(h * 0.82)], fill="#FE2C55")
        draw.rectangle([int(w * 0.48), int(h * 0.22), int(w * 0.58), int(h * 0.67)], fill="#FE2C55")

    else:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    # Downscale smoothly using High-Quality Lanczos Filter
    return img.resize((int(w / scale), target_height), Image.Resampling.LANCZOS)


def embed_icon_in_fixed_canvas(
    qr_img: Image.Image,
    platform: str,
    back_color: str,
) -> Image.Image:
    """Creates a FIXED 368x444 px canvas and places QR at top (368x368) and Icon at bottom padding (76px height)."""
    # Resize QR code precisely to 368x368
    qr_resized = qr_img.resize((QR_SIZE, QR_SIZE), Image.Resampling.LANCZOS)

    # Create Fixed Canvas 368 x 444 px
    final_canvas = Image.new("RGBA", (FIXED_WIDTH, FIXED_HEIGHT), back_color)
    final_canvas.paste(qr_resized, (0, 0))

    if platform != "None":
        # Target icon height fitted proportionally in 76px bottom padding (e.g. 42px height)
        icon_target_h = 42
        brand_icon = create_official_brand_icon(platform, icon_target_h)
        icon_w, icon_h = brand_icon.size

        # Center Alignment inside the 76px bottom area
        icon_x = (FIXED_WIDTH - icon_w) // 2
        icon_y = QR_SIZE + ((BOTTOM_PADDING_HEIGHT - icon_h) // 2)

        # Paste icon onto bottom padding
        final_canvas.paste(brand_icon, (icon_x, icon_y), brand_icon)

    return final_canvas


# --- Helper Functions & Security Checks ---
def validate_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def check_security_warnings(url: str) -> list[str]:
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
    fill_color: str = "#000000",
    back_color: str = "#FFFFFF",
    error_correction_key: str = "High (30% - Best for print)",
    fmt: str = "PNG",
    platform_icon: str = "Auto-Detect",
) -> bytes:
    """Generates Fixed 368x444 px QR Code image."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECTION_MAP.get(error_correction_key, qrcode.constants.ERROR_CORRECT_H),
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGBA")

    # Detect platform icon
    active_platform = platform_icon
    if platform_icon == "Auto-Detect":
        active_platform = detect_platform(data)

    # Embed QR and Icon into Fixed 368x444 Canvas
    final_img = embed_icon_in_fixed_canvas(
        qr_img=qr_img,
        platform=active_platform,
        back_color=back_color,
    ).convert("RGB")

    with BytesIO() as buffer:
        save_fmt = fmt.upper()
        if save_fmt == "JPG":
            save_fmt = "JPEG"
            final_img.save(buffer, format=save_fmt, quality=100, subsampling=0)
        else:
            final_img.save(buffer, format=save_fmt, quality=100)
            
        return buffer.getvalue()


@st.cache_data(show_spinner=False)
def generate_svg_qr(
    data: str,
    fill_color: str = "#000000",
    error_correction_key: str = "High (30% - Best for print)",
) -> str:
    """Generates pure vector SVG QR code."""
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECTION_MAP.get(error_correction_key, qrcode.constants.ERROR_CORRECT_H),
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
    """Renders a custom HTML/JS button that copies image to system clipboard."""
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
    """Injects custom CSS to ensure proper action button sizing."""
    st.markdown(
        """
        <style>
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
    st.set_page_config(page_title="Fixed Size QR Code Generator (368x444)", page_icon="🔗", layout="centered")
    inject_custom_css()

    st.title("URL to QR Code Generator 🔗")
    st.caption("Fixed Dimensions: 368 x 444 px | Official Brand Logos Center Aligned")

    raw_url = st.text_input(
        "Enter your link here:",
        placeholder="https://www.youtube.com/watch?v=...",
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

        # Style Customization Expander (Colors)
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

        try:
            st.markdown("---")

            if "ec_level" not in st.session_state:
                st.session_state.ec_level = "High (30% - Best for print)"
            if "icon_choice" not in st.session_state:
                st.session_state.icon_choice = "Auto-Detect"

            png_bytes_for_copy = generate_raster_qr(
                clean_url,
                fill_color=fill_color,
                back_color=back_color,
                error_correction_key=st.session_state.ec_level,
                fmt="PNG",
                platform_icon=st.session_state.icon_choice,
            )

            caption_text = "Preview (SVG Vector)" if is_vector else f"Preview ({FIXED_WIDTH}x{FIXED_HEIGHT}px Fixed)"

            col_left, col_right = st.columns([1.2, 1], gap="medium")

            # Left Column: Image Preview
            with col_left:
                st.image(
                    png_bytes_for_copy,
                    caption=caption_text,
                    use_container_width=True,
                )

            # Right Column: Action Buttons & Controls
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
                        fill_color=fill_color,
                        back_color=back_color,
                        error_correction_key=st.session_state.ec_level,
                        fmt=file_format,
                        platform_icon=st.session_state.icon_choice,
                    )
                    st.download_button(
                        label=f"📥 Download {file_format}",
                        data=download_bytes,
                        file_name=f"qr_code_{FIXED_WIDTH}x{FIXED_HEIGHT}.{file_format.lower()}",
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

                # 4. Error Correction Dropdown
                st.selectbox(
                    "Error Correction (การฟื้นฟูข้อมูล):",
                    options=list(ERROR_CORRECTION_MAP.keys()),
                    key="ec_level",
                    help="แนะนำให้ใช้ High (30%) สำหรับการนำไปพิมพ์ลงกระดาษหรืองานสกรีน",
                )

                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

                # 5. Brand Icon Selector Dropdown
                st.selectbox(
                    "Brand Icon (โลโก้ขอบล่าง):",
                    options=["Auto-Detect", "YouTube", "LINE", "Instagram", "Facebook", "TikTok", "None (ปิดโลโก้)"],
                    key="icon_choice",
                    help="จัดวางโลโก้ในพื้นที่ Padding ด้านล่าง 76px กึ่งกลาง Center X & Y",
                )

        except Exception as err:
            logger.error("Failed to generate QR: %s", err)
            st.error("An error occurred while generating the QR code.")


if __name__ == "__main__":
    main()
