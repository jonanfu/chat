import streamlit as st
from authentication import authentication  # Importar la función de autenticación
from chat import chat  # Importar la interfaz de chat

#st.session_state.id = "a3c09d9b-4baf-4c8a-92f1-1d33cb65e4f8"
#st.session_state.username = "alice"
#st.session_state.tokens_available = 4544
#Verificar si el usuario ya está autenticado
if 'id' in st.session_state:
    chat()  # Si está autenticado, mostrar la interfaz de chat
else:
    authentication()  # Si no está autenticado, mostrar la pantalla de inicio de sesión
