import streamlit as st
import qrcode
from io import BytesIO
import requests
from PIL import Image

st.title("Online QR Code Generator 🔗")
st.write("Built with Python and Streamlit")

option = st.radio("Select input type:", ["URL Link", "Upload Image"])

user_link = ""

if option == "URL Link":
    user_link = st.text_input("Enter your link here:", "")

elif option == "Upload Image":
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Preview Image", width=200)
        
        if st.button("Generate QR from Image"):
            with st.spinner("Processing & Uploading image..."):
                try:
                    # 1. ย่อขนาดรูปภาพเพื่อลดขนาดไฟล์
                    img_pil = Image.open(uploaded_file)
                    img_pil.thumbnail((1024, 1024))  # ย่อไม่ให้เกิน 1024px
                    
                    img_byte_arr = BytesIO()
                    img_pil.save(img_byte_arr, format='JPEG', quality=85)
                    img_bytes = img_byte_arr.getvalue()

                    # 2. อัปโหลดไปยัง Catbox.moe
                    files = {
                        'reqtype': (None, 'fileupload'),
                        'fileToUpload': ('image.jpg', img_bytes, 'image/jpeg')
                    }
                    response = requests.post("https://catbox.moe/user/api.php", files=files)
                    
                    if response.status_code == 200 and response.text.startswith("http"):
                        user_link = response.text.strip()
                        st.success("Image uploaded successfully!")
                    else:
                        st.error("Failed to upload image. Please try again.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ส่วนสร้าง QR Code
if user_link:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(user_link)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()
    
    st.image(byte_im, caption="Your QR Code is ready!", width=300)
    
    st.download_button(
        label="📥 Download QR Code",
        data=byte_im,
        file_name="generated_qr.png",
        mime="image/png"
    )
