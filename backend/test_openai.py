from openai import OpenAI
from dotenv import load_dotenv
import os

# Cargar archivo .env
load_dotenv()

# Leer API key
api_key = os.getenv("OPENAI_API_KEY")

# Crear cliente OpenAI
client = OpenAI(api_key=api_key)

# Hacer prueba
respuesta = client.chat.completions.create(
    model="gpt-4.1-mini",

    messages=[
        {
            "role": "user",
            "content": "Dame un JSON de una luminaria LED colgante."
        }
    ]
)

# Mostrar respuesta
print(respuesta.choices[0].message.content)