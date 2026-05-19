from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import fitz
import glob
import re

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

pdfs_encontrados = glob.glob("pdfs/*.pdf")

if not pdfs_encontrados:
    print("No se encontró ningún PDF en la carpeta pdfs")
    exit()

pdf_path = max(pdfs_encontrados, key=os.path.getmtime)
print("PDF más reciente seleccionado:", pdf_path)

texto_pdf = ""

doc = fitz.open(pdf_path)

for pagina in doc:
    texto_pdf += pagina.get_text()

doc.close()

print("PDF leído correctamente")


def detectar_nombre_y_codigo(texto):
    lineas = texto.splitlines()

    for linea in lineas:
        linea_limpia = linea.strip()

        if "|" in linea_limpia and re.search(r"CL\s*[-–]?\s*\d+", linea_limpia.upper()):

            partes = linea_limpia.split("|")

            nombre = partes[0].strip()
            resto = partes[1].strip()

            codigo_match = re.search(
                r"CL\s*[-–]?\s*(\d+)",
                resto.upper()
            )

            codigo = codigo_match.group(1) if codigo_match else "-"

            nombre = nombre.replace("ESPECIFICACIONES TÉCNICAS", "").strip()
            nombre = nombre.replace("ESPECIFICACIONES TECNICAS", "").strip()

            return nombre, codigo

    codigo_match = re.search(r"CL\s*[-–]?\s*(\d+)", texto.upper())
    codigo = codigo_match.group(1) if codigo_match else "-"

    return "-", codigo


nombre_detectado, codigo_detectado = detectar_nombre_y_codigo(texto_pdf)

print("Nombre detectado:", nombre_detectado)
print("Código detectado:", codigo_detectado)

instrucciones_nombre = f"""
- nombre_producto:
  Usa EXACTAMENTE este valor: {nombre_detectado}
""" if nombre_detectado != "-" else """
- nombre_producto:
  Extrae el nombre comercial CORTO de la luminaria (Ej: "TUB 88", "DOWNLIGHT", "CARRIL").
  MÁXIMO 4 PALABRAS. NUNCA incluyas frases largas ni la descripción del producto.
"""

prompt = f"""
Actúa como extractor técnico COM.LED.

Lee el texto del PDF y extrae SOLO los datos reales.
NO inventes datos.
Si un dato no aparece, usa "-".

Devuelve SOLO JSON válido.
NO uses markdown.

TEXTO DEL PDF:
{texto_pdf}

REGLAS:

{instrucciones_nombre}

- codigo_comled:
  Usa EXACTAMENTE este valor:
  {codigo_detectado}

- descripcion_luminaria:
  Debe empezar SIEMPRE por "Luminaria LED".
  Debe tener entre 20 y 35 palabras.
  Debe indicar el tipo o instalación: carril, colgante, superficie, lineal, downlight, empotrada, etc.
  Debe describir aplicación, diseño o uso recomendado.

- instalacion:
  Detecta el tipo real: carril, colgante, superficie, lineal, empotrada, downlight, pared, sobremesa, integrado, etc.

- apertura_haz:
  Usa una óptica principal. Si aparece Difusa, usa "Difusa".

- aperturas_disponibles:
  Si hay varias ópticas, sepáralas con " / ".
  Si hay una sola, pon solo esa.
  Si aparece Difusa, usa "Difusa".

- ip debe ser tipo "IP20", "IP65", etc.
- ik debe ser tipo "IK02", "IK10", etc.
- cct debe mantener K.
- potencia debe mantener W.
- flujo_luminoso debe mantener lm.
- eficacia_luminosa debe mantener lm/W.

El JSON debe tener EXACTAMENTE estas claves:

nombre_producto
codigo_comled
descripcion_luminaria
potencia
flujo_luminoso
eficacia_luminosa
cct
cri
ugr
ip
ik
apertura_haz
aperturas_disponibles
instalacion
colores_disponibles
clase_aislamiento
tension_entrada
material_carcasa
img_producto
img_dimensiones
img_fotometria
img_instalacion
"""

respuesta = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}]
)

contenido = respuesta.choices[0].message.content
contenido = contenido.replace("```json", "").replace("```", "").strip()

try:
    datos = json.loads(contenido)
except Exception as e:
    print("ERROR AL LEER JSON:")
    print(e)
    print("\nRESPUESTA IA:\n")
    print(contenido)
    exit()

if nombre_detectado != "-":
    datos["nombre_producto"] = nombre_detectado
datos["codigo_comled"] = codigo_detectado

instalacion = datos.get("instalacion", "").lower()
descripcion = datos.get("descripcion_luminaria", "").lower()
nombre = datos.get("nombre_producto", "").lower()

texto_tipo = instalacion + " " + descripcion + " " + nombre

if "carril" in texto_tipo:
    datos["img_instalacion"] = "imagenes/de-carril.png"
elif "pared" in texto_tipo:
    datos["img_instalacion"] = "imagenes/de-pared.png"
elif "superficie" in texto_tipo:
    datos["img_instalacion"] = "imagenes/de-superficie.png"
elif "sobremesa" in texto_tipo:
    datos["img_instalacion"] = "imagenes/de-sobremesa.png"
elif "downlight" in texto_tipo or "empotr" in texto_tipo:
    datos["img_instalacion"] = "imagenes/downlights.png"
elif "lineal" in texto_tipo:
    datos["img_instalacion"] = "imagenes/lineales.png"
elif "colg" in texto_tipo:
    datos["img_instalacion"] = "imagenes/colgantes.png"
else:
    datos["img_instalacion"] = "imagenes/tecnicas.png"

datos["img_producto"] = "imagenes/producto_final.png"
datos["img_dimensiones"] = "imagenes/dimensiones.png"
datos["img_fotometria"] = "imagenes/fotometria_generada.png"

with open("entradas/datos.json", "w", encoding="utf-8") as archivo:
    json.dump(datos, archivo, indent=2, ensure_ascii=False)

print("datos.json generado correctamente")