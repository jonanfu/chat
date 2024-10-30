import streamlit as st
import requests

# Configuración de la URL del endpoint
URL = "https://chat-with-your-data-api.azurewebsites.net"

def authentication():
    st.title("Autenticación en Streamlit")
    st.write(st.session_state.to_dict())
    username = st.text_input("Nombre de usuario")
    password = st.text_input("Contraseña", type='password')

    if st.button("Iniciar sesión"):
        if username and password:
            credentials = {
                'username': username,
                'password': password
            }
            response = requests.post(URL + "/api/Account/Login", json=credentials)

            if response.status_code == 200:
                st.success("Autenticación exitosa!")
                id = response.json().get('id')  
                password_hash = response.json().get('passwordHash')
                tokens_available = response.json().get('tokensAvailable')
                st.session_state.id = id  
                st.session_state.username = username
                st.session_state.password_hash = password_hash
                st.session_state.tokens_available = tokens_available
                st.rerun()  # Recargar la aplicación para mostrar la página de chat
            else:
                st.error("Error en la autenticación: Revise sus credenciales")
        else:
            st.warning("Por favor, introduce tu nombre de usuario y contraseña.")
