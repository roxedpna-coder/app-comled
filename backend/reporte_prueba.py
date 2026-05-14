import json
import os
from PIL import Image

with open("entradas/datos.json", "r", encoding="utf-8") as f:
    datos = json.load(f)

def estado(valor):
    if not valor or str(valor).strip() == "-":
        return "REVISAR"
    return "OK"

def revisar_imagen(ruta):
    if not ruta or not os.path.exists(ruta):
        return "NO EXISTE"

    img = Image.open(ruta)
    w, h = img.size

    if w < 250 or h < 250:
        return f"REVISAR tamaño pequeño ({w}x{h})"

    return f"OK ({w}x{h})"

print("\nREPORTE DE FICHA COM.LED")
print("-" * 35)

campos = [
    "nombre_producto",
    "codigo_comled",
    "descripcion_luminaria",
    "potencia",
    "flujo_luminoso",
    "eficacia_luminosa",
    "cct",
    "ip",
    "ik",
    "apertura_haz",
    "aperturas_disponibles",
    "instalacion"
]

for campo in campos:
    valor = datos.get(campo, "-")
    print(f"{campo}: {valor} [{estado(valor)}]")

print("\nIMÁGENES")
print("-" * 35)

for campo in [
    "img_producto",
    "img_dimensiones",
    "img_fotometria",
    "img_instalacion"
]:
    ruta = datos.get(campo, "")
    print(f"{campo}: {ruta} [{revisar_imagen(ruta)}]")

print("\nFIN DEL REPORTE\n")