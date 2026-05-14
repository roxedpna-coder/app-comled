from openai import OpenAI
from dotenv import load_dotenv
import base64
import os

load_dotenv()

client = OpenAI()

input_path = "imagenes/producto_final.png"
output_path = "imagenes/producto_final.png"

if not os.path.exists(input_path):
    print("No existe imagen de producto para mejorar")
    exit()

prompt = """
Mejora esta imagen de luminaria técnica para una ficha COM.LED.

Reglas estrictas:
- Mantén exactamente la misma luminaria.
- No cambies forma, proporciones, óptica, carril, lente, color ni materiales.
- No inventes piezas nuevas.
- No cambies el ángulo de vista.
- Elimina fondo gris, sucio o con ruido.
- Deja fondo blanco limpio o transparente.
- Mejora nitidez, resolución, bordes y calidad visual.
- Resultado profesional tipo catálogo técnico.
"""

with open(input_path, "rb") as image_file:
    result = client.images.edit(
        model="gpt-image-1",
        image=image_file,
        prompt=prompt,
        size="1024x1024"
    )

image_base64 = result.data[0].b64_json

with open(output_path, "wb") as f:
    f.write(base64.b64decode(image_base64))

print("Producto mejorado con IA correctamente")