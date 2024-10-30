import streamlit as st
import requests
import pandas as pd

BASE_URL = "https://chat-with-your-data-api.azurewebsites.net"

def chat():
    # Inicialización del estado de la sesión
    if 'initialized' not in st.session_state:
        st.session_state.id = "a3c09d9b-4baf-4c8a-92f1-1d33cb65e4f8"
        st.session_state.username = "alice"
        st.session_state.tokens_available = 1000
        st.session_state.total_cost = 12.3
        st.session_state.initialized = True
        st.session_state.prompt = None
        st.session_state.db_type = None
        st.session_state.tokens_used = None
        st.session_state.retail_price = None
        st.session_state.show_buttons = False
        st.session_state.process_query = False
        # Inicializar el historial del chat
        st.session_state.messages = [
            {"role": "assistant", "content": "¡Hola! 👋 ¿cómo puedo ayudarte?"}
        ]

    st.set_page_config(page_title="Asistente de RR:HH", page_icon="📎")

    st.write('<h1 style="text-align:center;">Habla con el chat</h1>', unsafe_allow_html=True)

    # Sidebar
    st.sidebar.title(f"Bienvenid@ : {st.session_state.username}")
    counter_placeholder = st.sidebar.empty()
    counter_placeholder.write(f"Total de tokens: {st.session_state.tokens_available}")
    counter_placeholder.write(f"Coste total de la conversación: ${st.session_state.total_cost:.5f}")

    # Mostrar todo el historial del chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            # Si el mensaje tiene una tabla, mostrarla
            if "table" in message:
                st.table(message["table"])
            # Si el mensaje tiene código SQL, mostrarlo
            if "sql" in message:
                st.code(message["sql"], language="sql")

    # Input del usuario
    prompt = st.chat_input("Dime, cual es tu consulta")

    # Si hay un nuevo prompt, actualizar el estado
    if prompt and prompt != st.session_state.prompt:
        st.session_state.prompt = prompt
        st.session_state.show_buttons = False
        st.session_state.process_query = False
        
        # Agregar mensaje del usuario al historial
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Obtener información de tokens
        db_type, tokens_used, retail_price = get_token_comsuption(prompt)
        
        if db_type and tokens_used and retail_price:
            st.session_state.db_type = db_type
            st.session_state.tokens_used = tokens_used
            st.session_state.retail_price = retail_price
            st.session_state.show_buttons = True
            
            # Agregar mensaje del asistente sobre tokens al historial
            token_message = f"El total de tokens que va a utilizar son: {tokens_used} con un precio de: ${retail_price} dolares\n¿Desea realizar la petición?"
            st.session_state.messages.append({"role": "assistant", "content": token_message})
            
            st.rerun()

    # Mostrar botones si es necesario
    if st.session_state.show_buttons and not st.session_state.process_query:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Aceptar", key="accept_button", use_container_width=True):
                st.session_state.process_query = True
                st.session_state.show_buttons = False
                st.rerun()
        with col2:
            if st.button("Cancelar", key="cancel_button", use_container_width=True):
                st.session_state.show_buttons = False
                st.session_state.prompt = None
                # Agregar mensaje de cancelación al historial
                st.session_state.messages.append({"role": "assistant", "content": "Solicitud cancelada."})
                st.rerun()

    # Procesar la consulta si fue aceptada
    if st.session_state.process_query and st.session_state.prompt:
        if st.session_state.tokens_available >= st.session_state.tokens_used:
            query = generate_sql_query(st.session_state.prompt, st.session_state.db_type)
            
            if query:
                results = execute_sql_query(query=query, db_type=st.session_state.db_type)
                
                if results and len(results) > 0:
                    header = results[0].split(" | ")
                    data = [row.split(" | ") for row in results[1:]]
                    df = pd.DataFrame(data, columns=header)
                    
                    # Agregar resultados al historial
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Esta es tu query en SQL:",
                        "sql": query,
                        "table": df
                    })
                else:
                    # Agregar mensaje de no resultados al historial
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "No se encontraron resultados."
                    })
        else:
            # Agregar mensaje de tokens insuficientes al historial
            st.session_state.messages.append({
                "role": "assistant",
                "content": "No tiene suficientes tokens."
            })
        
        # Limpiar el estado para permitir nueva consulta
        st.session_state.process_query = False
        st.session_state.prompt = None
        st.session_state.show_buttons = False
        st.rerun()

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
        return None, None, None
    
def generate_sql_query(prompt, db_type):
    url = f"{BASE_URL}/api/Query/GenerateSqlQuery"
    response = requests.post(url, json={
        "naturalLanguageQuery": prompt,
        "selectedDatabaseType": db_type,
        "userId": st.session_state.id
    })
    
    if response.status_code == 200:
        data = response.json().get("data", {})
        generated_sql_query = data.get("generatedSqlQuery")
        token_count_inp = data.get("tokenCountInp", 0)
        token_count_outp = data.get("tokenCountOutp", 0)
        
        tokens_consumed = token_count_inp + token_count_outp
        st.session_state.tokens_available -= tokens_consumed

        # Agregar información de tokens al historial
        token_info = f"Tokens consumidos: {tokens_consumed}\nTokens restantes: {st.session_state.tokens_available}"
        st.session_state.messages.append({
            "role": "assistant",
            "content": token_info
        })
        
        return generated_sql_query
    else:
        st.error("Error al generar la consulta SQL")
        return None

def execute_sql_query(query, db_type):
    url = f"{BASE_URL}/api/Query/ExecuteSqlQuery"
    response = requests.post(url, json={
        "generatedSqlQuery": query,
        "selectedDatabaseType": db_type
    })

    if response.status_code == 200:
        data = response.json().get("data", {})
        return data.get("results", [])
    else:
        st.error("Error al ejecutar la consulta SQL")
        return None