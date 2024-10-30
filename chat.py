import streamlit as st
import requests
import pandas as pd

BASE_URL = "https://chat-with-your-data-api.azurewebsites.net"

def chat():
    st.session_state.id = "a3c09d9b-4baf-4c8a-92f1-1d33cb65e4f8"
    st.session_state.username = "alice"
    total_tokens = st.session_state.tokens_available
    st.session_state.total_cost = 12.3
    
    st.set_page_config(page_title="Asistente de RR:HH", page_icon="📎")

    st.write('<h1 style="text-align:center;">Habla con el chat</h1>', unsafe_allow_html=True)

    st.sidebar.title(f"Bienvenid@ : {st.session_state.username}")
    counter_placeholder = st.sidebar.empty()
    counter_placeholder.write(f"Total de tokens: ${total_tokens}")
    counter_placeholder.write(f"Coste total de la conversación: ${st.session_state['total_cost']:.5f}", key="clear")

    prompt = st.chat_input("Dime, cual es tu consulta")

    with st.chat_message("Asistente"):
        st.write("¡Hola! 👋 ¿cómo puedo ayudarte?")
    
    if prompt:
        with st.chat_message("Usuario"):
            st.write(prompt)
        db_type, tokens_used, retail_price = get_token_comsuption(prompt)

        with st.chat_message("Asistente"):
            st.write(f"El total de tokens que va a utilizar son: {tokens_used} con un precio de: {retail_price}")
            st.write("¿Desea realizar la petición?")

        # Aquí se introduce un estado para esperar la respuesta del usuario
        if "user_response" not in st.session_state:
            col1, col2 = st.columns(2)  # Crear dos columnas para los botones
            with col1:
                if st.button("Aceptar", use_container_width=True):
                    st.session_state.user_response = "Aceptar"  # Guardar la respuesta
                    st.rerun()  # Volver a cargar la app para evaluar la respuesta
            with col2:
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.user_response = "Cancelar"  # Guardar la respuesta
                    st.rerun()  # Volver a cargar la app para evaluar la respuesta

            st.stop()  # Detener el código hasta que se haga clic en un botón

    # Verificar la respuesta del usuario
    if 'user_response' in st.session_state:
        if st.session_state.user_response == "Aceptar":
            if total_tokens >= tokens_used:
                query = generate_sql_query(prompt, db_type)
                results = execute_sql_query(query=query, db_type=db_type)
                if results:
                    # Procesar resultados para mostrar en una tabla
                    if len(results) > 0:
                        header = results[0].split(" | ")
                        data = [row.split(" | ") for row in results[1:]]  # Todos los demás son registros
                        
                        # Convertir a DataFrame para mostrar como tabla
                        df = pd.DataFrame(data, columns=header)
                        
                        with st.chat_message("Asistente"):
                            st.write("Esta es tu query en SQL:")
                            st.code(query, language="sql")
                            st.write("Resultados de la consulta SQL:")
                            st.table(df)  # Muestra la tabla
                    else:
                        st.write("No se encontraron resultados.")
            else:
                st.write("No tiene suficientes tokens.")
        else:
            with st.chat_message("Asistente"):
                st.write("No se puede realizar la solicitud.")

def get_token_comsuption(prompt):
    data = {
        "naturalLanguageQuery": prompt,
        "userId": st.session_state.id
    }

    url = f"{BASE_URL}/api/Query/GetTokensConsumption"
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        data = response.json().get("data")
        db_type = data.get("selectedDatabaseType")
        tokens_used = data.get("tokenCount")
        retail_price = data.get("retailPrice")
        return db_type, tokens_used, retail_price
    else:
        st.error("Error al obtener consumo de tokens")
        return None
    
def generate_sql_query(prompt, db_type):
    url = f"{BASE_URL}/api/Query/GenerateSqlQuery"
    response = requests.post(url, json={"naturalLanguageQuery": prompt, "selectedDatabaseType": db_type, "userId": st.session_state.id})
    
    if response.status_code == 200:
        data = response.json().get("data", {})
        generated_sql_query = data.get("generatedSqlQuery")
        token_count_inp = data.get("tokenCountInp", 0)
        token_count_outp = data.get("tokenCountOutp", 0)
        
        # Resta los tokens consumidos del total disponible
        tokens_consumed = token_count_inp + token_count_outp
        st.session_state.tokens_available -= tokens_consumed

        st.write(f"Tokens consumidos: {tokens_consumed}")
        st.write(f"Tokens restantes: {st.session_state.tokens_available}")
        
        return generated_sql_query
    else:
        st.error("Error al generar la consulta SQL")
        return None

def execute_sql_query(query, db_type):
    url = f"{BASE_URL}/api/Query/ExecuteSqlQuery"
    response = requests.post(url, json={"generatedSqlQuery": query, "selectedDatabaseType": db_type})

    if response.status_code == 200:
        data = response.json().get("data", {})
        return data.get("results", [])
    else:
        st.error("Error al ejecutar la consulta SQL")
        return None 
