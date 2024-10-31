import streamlit as st
import requests
from PIL import Image

# Configuración de la URL del endpoint
URL = "https://chat-with-your-data-api.azurewebsites.net"

def image_to_base64(image):
        import io
        import base64
        buf = io.BytesIO()
        image.save(buf, format='PNG')
        byte_data = buf.getvalue()
        return base64.b64encode(byte_data).decode()

def authentication():

    image = Image.open("assets/DataVerse.png")

    st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="data:image/png;base64,{image_to_base64(image)}" alt="DataVerse Logo" width="350">
    </div>
    """,
    unsafe_allow_html=True
    )

    st.title("Chat with your data through DataVerse: Interactive & Efficient Chat")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    if st.button("Login"):
        if username and password:
            credentials = {
                'username': username,
                'password': password
            }
            response = requests.post(URL + "/api/Account/Login", json=credentials)

            if response.status_code == 200:
                st.success("Login successful!")
                id = response.json().get('id')  
                password_hash = response.json().get('passwordHash')
                tokens_available = response.json().get('tokensAvailable')
                st.session_state.id = id  
                st.session_state.username = username
                st.session_state.password_hash = password_hash
                st.session_state.tokens_available = tokens_available
                st.rerun()  # Recargar la aplicación para mostrar la página de chat
            else:
                st.error("Username or password is incorrect")
        else:
            st.warning("Username and password required")
