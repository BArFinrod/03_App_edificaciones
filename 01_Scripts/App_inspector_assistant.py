from openai import OpenAI
import requests
import base64
import streamlit as st
import json
import neo4j
import pandas as pd
from PIL import Image
from pathlib import Path

key_ = st.secrets["key_"]
ast1 = st.secrets['ast1']
ast2 = st.secrets['ast2']
ast3 = st.secrets['ast3']
uri = st.secrets['uri']
auth1 = st.secrets['auth1']
auth2 = st.secrets['auth2']

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {key_}"
    }

@st.cache_data(ttl=1200)
def _get_completion(payload):
    response_raw = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    identificados_raw = response_raw.json()['choices'][0]['message']['content']
    identificados_raw = identificados_raw.replace('`','').replace('json','')
    identificados = json.loads(identificados_raw)
    ident = identificados['objetos']
    query = ast1 + str(ident) + ast2
    driverDB = neo4j.GraphDatabase.driver(uri, auth=(auth1, auth2))
    df = driverDB.execute_query(query, result_transformer_= neo4j.Result.to_df)
    return df

path_str = Path(__file__).parent.parent
image = Image.open(path_str / '00_Data/Logo_iaxta.jpeg')
#### titulos
st.image(image, width=200)
st.title("Asistente inteligente para inspeccionar su establecimiento")
st.subheader("Certificado ITSE (antes Certificado de Defensa Civil)")
st.markdown("Esta App facilita las Inspecciones de Seguridad en los establecimiento para obtener el certificado ITSE y asegurar las condiciones mínimas de seguridad, que son obligatorias para el funcionamiento de cualquier establecimiento en Perú")
        
st.markdown("Problemática: para presentar la declaración jurada ante la municipalidad, se deben revisar los **67** puntos del [formulario oficial del Anexo 4 del REGLAMENTO DE INSPECCIONES TÉCNICAS DE SEGURIDAD EN EDIFICACIONES](https://www.gob.pe/institucion/munibarranco/informes-publicaciones/4757843-itse-formularios); sin embargo, estos puntos se refiere a diferentes objetos, que van desde instalaciones eléctricas hasta salidas de emergencia.")
    
st.markdown("Solución: La App identifica los objetos en la foto, revisa los **67** puntos del formulario oficial y elige únicamente los relacionados a los objetos en la foto para que puedan ser verificados por usted fácilmente.")
st.markdown("""
            **Instrucciones:**
            1. Tomar una foto a la parte del establecimiento en la que se desea inspeccionar las condiciones de seguridad.
            2. Debajo se mostrará una lista de verificación que debe tener en cuenta para completar la DECLARACIÓN JURADA DE CUMPLIMIENTO DE LAS CONDICIONES DE SEGURIDAD EN LA EDIFICACIÓN.
            """)

img_file_buffer = st.camera_input("Presione en 'Take photo' para tomar la foto")

if img_file_buffer is not None:
    bytes_data = img_file_buffer.getvalue()
    base64_image = base64.b64encode(bytes_data).decode('utf-8')

    payload = {
    "model": "gpt-4o",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text":  ast3
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    "max_tokens": 2000
    }

    df = _get_completion(payload).drop_duplicates().fillna(" ")

    dim1_unique = df["o.Dim1"].unique()

    # Iterar sobre el primer nivel de la jerarquía
    # st.table(df)
    for dim1 in dim1_unique:
        # with st.container():
        st.markdown(f"<div style='font-size:24px; font-weight:bold'>{dim1}</div>", unsafe_allow_html=True)
        dim2_filtered = df[df["o.Dim1"] == dim1]["o.Dim2"].unique()
        for dim2 in dim2_filtered:
            st.markdown(f"<div style='margin-left:20px; font-size:20px; font-weight:bold'>{dim2}</div>", unsafe_allow_html=True)
            dim3_filtered = df[(df["o.Dim1"] == dim1) & (df["o.Dim2"] == dim2)]["o.Dim3"].unique()
            for dim3 in dim3_filtered:
                st.markdown(f"<div style='margin-left:40px; font-size:18px;'>{dim3}</div>", unsafe_allow_html=True)
                dim4_filtered = df[(df["o.Dim1"] == dim1) & (df["o.Dim2"] == dim2) & (df["o.Dim3"] == dim3)]
                for _, row in dim4_filtered.iterrows():
                    st.checkbox(f"      {row['o.item_desc']}")
                #       