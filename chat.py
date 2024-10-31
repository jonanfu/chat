import streamlit as st
import requests
import pandas as pd
from PIL import Image

BASE_URL = "https://chat-with-your-data-api.azurewebsites.net"

def image_to_base64(image):
        import io
        import base64
        buf = io.BytesIO()
        image.save(buf, format='PNG')
        byte_data = buf.getvalue()
        return base64.b64encode(byte_data).decode()

def chat():
    # Inicialización del estado de la sesión
    if 'initialized' not in st.session_state:
        st.session_state.total_cost = 0
        st.session_state.initialized = True
        st.session_state.prompt = None
        st.session_state.db_type = None
        st.session_state.tokens_used = None
        st.session_state.retail_price = None
        st.session_state.show_buttons = False
        st.session_state.process_query = False
        # Inicializar el historial del chat
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! 👋 How can I help you today?"}
        ]

    st.set_page_config(page_title="DataVerse", page_icon="📎")

    st.write('<h1 style="text-align:center;">Chat with your data through DataVerse: Interactive & Efficient Chat</h1>', unsafe_allow_html=True)

    # Sidebar

    image = Image.open("assets/DataVerse.png")

    st.sidebar.markdown(
    f"""
    <div style="text-align: center;">
        <img src="data:image/png;base64,{image_to_base64(image)}" alt="DataVerse Logo" width="300">
    </div>
    """,
    unsafe_allow_html=True
    )

    st.sidebar.title(f"Welcome: {st.session_state.username}!")
    st.sidebar.write(f"Total tokens: {st.session_state.tokens_available}")
    st.sidebar.write(f"Total cost of the conversation: ${st.session_state.total_cost:.4f}")

    # Mostrar todo el historial del chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Si el mensaje tiene código SQL, mostrarlo
            if "sql" in message:
                st.code(message["sql"], language="sql")
            # Si el mensaje tiene una tabla, mostrarla
            if "table" in message:
                st.write('Your data result:')
                st.table(message["table"])


    # Input del usuario
    prompt = st.chat_input("Tell me, what is your question?")

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
            token_message = (f"The approximate number of tokens that you are going to use are: {tokens_used} with a price of: ${retail_price:.4f} dollars.  \n"
                             f"Do you want to make the request?")
            st.session_state.messages.append({"role": "assistant", "content": token_message})
            
            st.rerun()

    # Mostrar botones si es necesario
    if st.session_state.show_buttons and not st.session_state.process_query:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm", key="accept_button", use_container_width=True):
                st.session_state.process_query = True
                st.session_state.show_buttons = False
                st.rerun()
        with col2:
            if st.button("Cancel", key="cancel_button", use_container_width=True):
                st.session_state.show_buttons = False
                st.session_state.prompt = None
                # Agregar mensaje de cancelación al historial
                st.session_state.messages.append({"role": "assistant", "content": "Request annulment."})
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
                        "content": "SQL query generated successfully:",
                        "sql": query,
                        "table": df
                    })
                else:
                    # Agregar mensaje de no resultados al historial
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "No results found"
                    })
        else:
            # Agregar mensaje de tokens insuficientes al historial
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Insufficient tokens available to make the request"
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
    elif response.status_code == 400:
        st.session_state.messages.append({
                "role": "assistant",
                "content": "No se encontro una base de datos que cumple con su consulta"
            })
        return None, None, None
    else:
        st.error("Error to get token consumption")
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
        retail_price = round(data.get("retailPrice", 0), 4)
        
        tokens_consumed = token_count_inp + token_count_outp
        st.session_state.tokens_available -= tokens_consumed
        st.session_state.total_cost += retail_price

        # Agregar información de tokens al historial
        token_info = (
            f"Tokens input: {token_count_inp}  \n"  # Usar dos espacios para un salto de línea
            f"Tokens output: {token_count_outp}  \n"
            f"Tokens consumed: {tokens_consumed}  \n"
            f"Retail price USD: {retail_price}"
        )
        st.session_state.messages.append({
            "role": "assistant",
            "content": token_info
        })
        
        return generated_sql_query
    else:
        st.error("Error generating sql query")
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
        st.error("Error executing sql query")
        return None
