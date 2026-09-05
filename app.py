import streamlit as st
import qrcode
from io import BytesIO

st.title("Online QR Code Generator 🔗")
st.write("Built with Python and Streamlit")

user_link = st.text_input("Enter your link here:", "")

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