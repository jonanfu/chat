from openai import OpenAI
import streamlit as st
import os

INITIAL_STATE = "Eres un asistente de voz"

api_key = os.getenv("OPENAI_API_KEY")

#client = OpenAI(api_key=api_key)


# Acceder a los parámetros que necesites
name = st.query_params["name"]
role = st.query_params["role"]

st.set_page_config(page_title="IRR Tutorial", page_icon="📎")
st.write('<h1 style="text-align:center;">Habla con el chat</h1>', unsafe_allow_html=True)

if name:
    st.write(f"Has pasado el nombre con valor: {name}")
if role:
    st.write(f"Has pasado el role con valor: {role}")

if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{"role": "system", "content": INITIAL_STATE}]
if 'model_name' not in st.session_state:
    st.session_state['model_name'] = []
if 'cost' not in st.session_state:
    st.session_state['cost'] = []
if 'total_tokens' not in st.session_state:
    st.session_state['total_tokens'] = []
if 'total_cost' not in st.session_state:
    st.session_state['total_cost'] = 0.0

st.sidebar.title("Aquí se muestran los controles")
model_name = st.sidebar.radio("Elegir modelo", ("GPT-3.5", "GPT-4"))
counter_placeholder = st.sidebar.empty()
counter_placeholder.write(f"Coste total de la conversación: ${st.session_state['total_cost']:.5f}", key="clear")
clear_button = st.sidebar.button("Limpiar conversación", key="clear")

model = "gpt-3.5-turbo" if model_name == "GPT-3.5" else "gpt-4"

if clear_button:
    st.session_state['generated'] = []
    st.session_state['past'] = []
    st.session_state['messages'] = [{"role": "system", "content": INITIAL_STATE}]
    st.session_state['total_tokens'] = []
    st.session_state['model_name'] = []
    st.session_state['cost'] = []
    st.session_state['total_cost'] = 0.0
    counter_placeholder.write(f"Coste total de la conversación: ${st.session_state['total_cost']:.5f}")

def generate_response(prompt):
    st.session_state['messages'].append({"role": "user", "content": prompt})

    completion = "" #client.chat.completions.create(model=model, messages=st.session_state['messages'])
    response = completion.choices[0].message.content
    st.session_state['messages'].append({"role": "assistant", "content": response})

    total_tokens = completion.usage.total_tokens
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    return response, total_tokens, prompt_tokens, completion_tokens

response_container = st.container()
prompt = st.chat_input("Dime algo majo")

if prompt:
    output, total_tokens, prompt_tokens, completion_tokens = generate_response(prompt)
    st.session_state['past'].append(prompt)
    st.session_state['generated'].append(output)
    st.session_state['model_name'].append(model_name)
    st.session_state['total_tokens'].append(total_tokens)

    cost = (total_tokens * (0.002 if model_name == "GPT-3.5" else (0.03 * prompt_tokens + 0.06 * completion_tokens)) / 1000)
    
    st.session_state['cost'].append(cost)
    st.session_state['total_cost'] += cost

if st.session_state['generated']:
    with response_container:
        for i in range(len(st.session_state['generated'])):
            st.write(f"**Usuario:** {st.session_state['past'][i]}")
            st.write(f"**Asistente:** {st.session_state['generated'][i]}")
            st.write({
                "Modelo utilizado": st.session_state['model_name'][i],
                "Número de tokens": st.session_state['total_tokens'][i]
            })

        counter_placeholder.write(f"Coste total de la conversación: ${st.session_state['total_cost']:.5f}")
