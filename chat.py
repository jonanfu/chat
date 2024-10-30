import streamlit as st
import requests
import pandas as pd

BASE_URL = "https://chat-with-your-data-api.azurewebsites.net"

def chat():
    st.session_state.id = "a3c09d9b-4baf-4c8a-92f1-1d33cb65e4f8"
    st.session_state.username = "alice"
    st.set_page_config(page_title="IRR Tutorial", page_icon="📎")

    st.write('<h1 style="text-align:center;">Habla con el chat</h1>', unsafe_allow_html=True)

    if 'generated' not in st.session_state:
        st.session_state['generated'] = []
    if 'past' not in st.session_state:
        st.session_state['past'] = []
    if 'cost' not in st.session_state:
        st.session_state['cost'] = []
    if 'total_tokens' not in st.session_state:
        st.session_state['total_tokens'] = []
    if 'total_cost' not in st.session_state:
        st.session_state['total_cost'] = 0.0

    st.sidebar.title("Aquí se muestran los controles")
    counter_placeholder = st.sidebar.empty()
    counter_placeholder.write(f"Total de tokens: ${st.session_state.tokens_available}")
    counter_placeholder.write(f"Coste total de la conversación: ${st.session_state['total_cost']:.5f}", key="clear")
    clear_button = st.sidebar.button("Limpiar conversación", key="clear")


    if clear_button:
        st.session_state['past'] = []
        st.session_state['cost'] = []
        st.session_state['total_cost'] = 0.0
        counter_placeholder.write(f"Coste total de la conversación: ${st.session_state['total_cost']:.5f}")

    response_container = st.container()
    prompt = st.chat_input("Dime, cual es tu consulta")

    if prompt:
        db_type, total_tokens, retail_price = get_token_comsuption(prompt)

        st.session_state['past'].append(prompt)
        st.session_state['cost'].append(retail_price)
        st.session_state['total_tokens'].append(total_tokens)

        if total_tokens < st.session_state.tokens_available:
            query = generate_sql_query(prompt, db_type)
            results = execute_sql_query(query=query, db_type=db_type)
            st.session_state['total_tokens'].append(total_tokens)
        else :
            st.warning("No tiene sufiente tokens")
        st.session_state['generated'].append(results)
    
    if st.session_state['generated']:
        with response_container:
            for i in range(len(st.session_state['generated'])):
                st.write(f"**Usuario:** {st.session_state['past'][i]}")
                if results:
                    # Procesar resultados para mostrar en una tabla
                    if len(results) > 0:
                        # Asumimos que el primer elemento es el encabezado
                        header = results[0].split(" | ")
                        data = [row.split(" | ") for row in results[1:]]  # Todos los demás son registros
                        
                        # Convertir a DataFrame para mostrar como tabla
                        df = pd.DataFrame(data, columns=header)
                        st.write("Resultados de la consulta SQL:")
                        st.table(df)  # Muestra la tabla
                    else:
                        st.write("No se encontraron resultados.")
                st.write(f"**Asistente:** {st.session_state['generated'][i]}")
               

            counter_placeholder.write(f"Coste total de la conversación: ${st.session_state['total_cost']:.5f}")


def get_token_comsuption(prompt):
    data = {
        "naturalLanguageQuery": prompt,
        "userId": st.session_state.id
    }

    url = f"{BASE_URL}/api/Query/GetTokensConsumption"
    response = requests.post( url, json=data)
    
    if response.status_code == 200:
        data = response.json().get("data")
        db_type = data.get("selectedDatabaseType")
        total_tokens = data.get("tokenCount")
        retail_price = data.get("retailPrice")
        return db_type, total_tokens, retail_price
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