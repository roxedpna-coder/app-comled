from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import fitz
import glob

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

pdfs_encontrados = glob.glob("pdfs/*.pdf") + glob.glob("pdfs/*.png") + glob.glob("pdfs/*.jpg") + glob.glob("pdfs/*.jpeg")

if not pdfs_encontrados:
    print("ERROR CRÍTICO: No se encontró ningún archivo (.pdf, .png, .jpg) en la carpeta 'pdfs/'.")
    print("Por favor, asegúrate de colocar el PDF del proveedor en la carpeta correcta antes de ejecutar.")
    exit(1)

pdf_path = max(pdfs_encontrados, key=os.path.getmtime)
print("PDF más reciente seleccionado (Proveedor):", pdf_path)

texto_pdf = ""
base64_image = None
es_imagen = pdf_path.lower().endswith(('.png', '.jpg', '.jpeg'))

if es_imagen:
    print("Captura de pantalla detectada. Activando OpenAI Vision...")
    import base64
    with open(pdf_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
else:
    doc = fitz.open(pdf_path)
    for pagina in doc:
        texto_pdf += pagina.get_text()
    doc.close()
    print("PDF leído correctamente")

# Cargar configuracion opcional ingresada por el usuario (si existe)
nombre_deseado = ""
codigo_deseado = ""
instalacion_deseada = ""
if os.path.exists("entradas/config_proveedor.json"):
    try:
        with open("entradas/config_proveedor.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            nombre_deseado = config.get("nombre_comled", "")
            codigo_deseado = config.get("codigo_comled", "")
            instalacion_deseada = config.get("instalacion_manual", "")
    except Exception:
        pass

instrucciones_nombre = f"""
- nombre_producto:
  Usa EXACTAMENTE este valor: {nombre_deseado}
""" if nombre_deseado else """
- nombre_producto:
  Extrae el nombre comercial o modelo que indica el proveedor.
"""

instrucciones_codigo = f"""
- codigo_comled:
  Usa EXACTAMENTE este valor: {codigo_deseado}
""" if codigo_deseado else """
- codigo_comled:
  Extrae el SKU, Item No., o código de producto del proveedor. Si no hay, usa "-".
"""

instrucciones_instalacion = f"""
- instalacion:
  El usuario indica que la instalación es de tipo "{instalacion_deseada}". Mapea ese concepto a UNA de las siguientes opciones estrictas:
  [carril, superficie, pared, sobremesa, downlight, empotrada, lineal, colgante, proyector, baliza, emergencia, señaletica, integracion, uplight].
""" if instalacion_deseada else """
- instalacion:
  Clasifica el tipo de instalación eligiendo ÚNICAMENTE UNA de estas opciones exactas:
  [carril, superficie, pared, sobremesa, downlight, empotrada, lineal, colgante, proyector, baliza, emergencia, señaletica, integracion, uplight].
  Aplica lógica: Si es para "calle", "poste" o iluminación vial, usa "baliza" o "proyector" (dependiendo de la foto).
"""

prompt = f"""
Actúa como extractor técnico experto de catálogos de iluminación de proveedores internacionales.

Lee el texto del PDF y extrae SOLO los datos reales.
El documento puede estar en inglés, chino o español. Traduce e interpreta los datos al español técnico.
Por ejemplo: "Beam angle" -> apertura_haz, "Power" -> potencia, "Input Voltage" -> tension_entrada.
NO inventes datos. Si un dato no aparece, usa "".

Devuelve SOLO JSON válido. NO uses markdown.

TEXTO DEL PDF:
{texto_pdf}

REGLAS:
{instrucciones_nombre}
{instrucciones_codigo}
{instrucciones_instalacion}

- descripcion_luminaria:
  Debe empezar SIEMPRE por "Luminaria LED".
  NO incluyas el nombre del modelo, marca ni códigos del proveedor.
  Debe tener entre 15 y 30 palabras.
  Describe únicamente el formato, uso y características físicas.

- apertura_haz:
  Usa una óptica principal. Si aparece "Diffuse", usa "Difusa".

- aperturas_disponibles:
  Si hay varias ópticas (ej. 15/24/36), sepáralas con " / " (ej. "15° / 24° / 36°").
  Si hay una sola, pon solo esa. Si no hay, pon "".

- ip debe ser tipo "IP20", "IP65", etc. (Mantenlo completo, ej: "IP67 & IP69K").
- ip_resumido: Resume el IP para que quepa en un círculo gráfico pequeño. Ej: "IP67 & IP69K" -> "IP67/69".
- ik debe ser tipo "IK02", "IK10", etc.
- cct debe mantener K y la lista completa (ej. "2700K / 3000K / 4000K / 6500K").
- cct_resumido: Si hay MÁS de 3 temperaturas, pon el rango (ej. "2700K hasta 6500K"). Si hay 1, 2 o 3 temperaturas, pon el mismo valor exacto que cct.
- potencia debe mantener W y la lista completa (ej. "30W / 60W / 80W").
- potencia_resumido: Si hay varias potencias, usa un rango (ej. "30W hasta 80W"). Si es 1 sola, pon el mismo valor exacto.
- flujo_luminoso debe mantener lm y la lista completa (ej. "4200lm / 8400lm / 13600lm").
- flujo_resumido: Si hay varios flujos, usa un rango (ej. "4200lm hasta 13600lm"). Si es 1 solo, pon el mismo valor exacto.
- eficacia_luminosa debe mantener lm/W y la lista completa (ej. "140lm/W / 170lm/W").
- eficacia_resumido: Si hay varias eficacias, usa un rango (ej. "140 hasta 170 lm/W"). Si es 1 sola, pon el mismo valor exacto.
- cri debe ser "80", "90", o ">90".

El JSON debe tener EXACTAMENTE estas claves:

nombre_producto
codigo_comled
descripcion_luminaria
potencia
potencia_resumido
flujo_luminoso
flujo_resumido
eficacia_luminosa
eficacia_resumido
cct
cri
ugr
ip
ip_resumido
ik
apertura_haz
aperturas_disponibles
instalacion
colores_disponibles
clase_aislamiento
tension_entrada
cct_resumido
material_carcasa: Resume el material para que sea MUY corto (máx 3-4 palabras). Ej: en vez de 'Aluminio lacado texturizado y vidrio templado', pon 'Aluminio y vidrio'.
img_producto
img_dimensiones
img_fotometria
img_instalacion
"""

if base64_image:
    mensajes = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                }
            ]
        }
    ]
else:
    mensajes = [{"role": "user", "content": prompt}]

respuesta = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=mensajes
)

contenido = respuesta.choices[0].message.content
contenido = contenido.replace("```json", "").replace("```", "").strip()

try:
    datos = json.loads(contenido)
    
    # 1. FORZAR NOMBRE Y CÓDIGO MANUALES (Evita alucinaciones de la IA)
    if nombre_deseado:
        datos["nombre_producto"] = nombre_deseado
    if codigo_deseado:
        datos["codigo_comled"] = codigo_deseado
        
    # 2. TRUNCAR TEXTOS EXCESIVAMENTE LARGOS EN LA TABLA TÉCNICA
    # Si las listas de versiones son muy largas, la fuente en PPTX se aplasta
    import re
    def aplicar_rango_si_largo(clave_original, clave_resumen, sufijo=""):
        val = str(datos.get(clave_original, ""))
        if len(val) > 25 and "/" in val:
            # Si hay una versión resumida generada por la IA que sea válida, usarla
            val_res = str(datos.get(clave_resumen, ""))
            if val_res and len(val_res) < 20 and "/" not in val_res:
                datos[clave_original] = val_res
            else:
                # Truncamiento matemático de emergencia
                numeros = re.findall(r"[\d]+", val.replace(".", "").replace(",", ""))
                nums = [int(n) for n in numeros if int(n) > 0]
                if nums:
                    datos[clave_original] = f"{min(nums)}-{max(nums)}{sufijo}"

    aplicar_rango_si_largo("potencia", "potencia_resumido", "W")
    aplicar_rango_si_largo("flujo_luminoso", "flujo_resumido", "lm")
    aplicar_rango_si_largo("eficacia_luminosa", "eficacia_resumido", "lm/W")
    aplicar_rango_si_largo("cct", "cct_resumido", "K")

except Exception as e:
    print("ERROR AL LEER JSON:")
    print(e)
    print("\nRESPUESTA IA:\n")
    print(contenido)
    exit()

# Lógica de imágenes según instalación
instalacion = str(datos.get("instalacion", "")).lower()
descripcion = str(datos.get("descripcion_luminaria", "")).lower()
texto_tipo = instalacion + " " + descripcion

if "carril" in texto_tipo:
    datos["img_instalacion"] = "imagenes/de-carril.png"
elif "pared" in texto_tipo:
    datos["img_instalacion"] = "imagenes/de-pared.png"
elif "superficie" in texto_tipo:
    datos["img_instalacion"] = "imagenes/de-superficie.png"
elif "sobremesa" in texto_tipo:
    datos["img_instalacion"] = "imagenes/de-sobremesa.png"
elif "downlight" in texto_tipo or "empotr" in texto_tipo or "recessed" in texto_tipo:
    datos["img_instalacion"] = "imagenes/downlights.png"
elif "lineal" in texto_tipo or "linear" in texto_tipo:
    datos["img_instalacion"] = "imagenes/lineales.png"
elif "colg" in texto_tipo or "suspend" in texto_tipo:
    datos["img_instalacion"] = "imagenes/colgantes.png"
else:
    datos["img_instalacion"] = "imagenes/tecnicas.png"

datos["img_producto"] = "imagenes/producto_final.png"
datos["img_dimensiones"] = "imagenes/dimensiones.png"
datos["img_fotometria"] = "imagenes/fotometria_generada.png"

# Limpieza de valores nulos o - para la interfaz
for k, v in datos.items():
    if v == "-" or v == "N/A" or v == None:
        datos[k] = ""

with open("entradas/datos.json", "w", encoding="utf-8") as archivo:
    json.dump(datos, archivo, indent=2, ensure_ascii=False)

print("datos.json (proveedor) generado correctamente")
