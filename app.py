import streamlit as st
import qrcode
from io import BytesIO
import requests

st.title("Online QR Code Generator 🔗")
st.write("Built with Python and Streamlit")

# ให้ผู้ใช้เลือกว่าจะใช้ Link หรือ Image
option = st.radio("Select input type:", ["URL Link", "Upload Image"])

user_link = ""

if option == "URL Link":
    user_link = st.text_input("Enter your link here:", "")

elif option == "Upload Image":
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Preview Image", width=200)
        
        if st.button("Generate QR from Image"):
            with st.spinner("Uploading image..."):
                # ฝากรูปภาพไว้ที่ Imgur (Anonymous Client-ID)
                headers = {"Authorization": "Client-ID 544ba571c172d7e"}
                files = {"image": uploaded_file.getvalue()}
                response = requests.post("https://api.imgur.com/3/image", headers=headers, files=files)
                
                if response.status_code == 200:
                    user_link = response.json()["data"]["link"]
                    st.success("Image uploaded successfully!")
                else:
                    st.error("Failed to upload image. Please try again.")

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
