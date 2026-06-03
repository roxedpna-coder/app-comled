import json
import os

datos_path = "entradas/datos.json"
estado_img_path = "entradas/estado_img.json"
salida_estado = "entradas/estado.json"

# Campos obligatorios para la plantilla COM.LED
campos_obligatorios = [
    "nombre_producto",
    "codigo_comled",
    "descripcion_luminaria",
    "potencia",
    "flujo_luminoso",
    "eficacia_luminosa",
    "cct",
    "cri",
    "ugr",
    "ip",
    "ik",
    "apertura_haz",
    "instalacion",
    "clase_aislamiento",
    "tension_entrada"
]

datos_faltantes = []
imagenes_faltantes = []

# 1. Revisar JSON de datos
if os.path.exists(datos_path):
    with open(datos_path, "r", encoding="utf-8") as f:
        try:
            datos = json.load(f)
            for campo in campos_obligatorios:
                valor = datos.get(campo, "")
                if not valor or str(valor).strip() == "" or valor == "-":
                    datos_faltantes.append(campo)
        except Exception as e:
            print("Error leyendo datos.json:", e)
else:
    datos_faltantes = campos_obligatorios.copy()

# 2. Revisar JSON de imágenes
if os.path.exists(estado_img_path):
    with open(estado_img_path, "r", encoding="utf-8") as f:
        try:
            estado_img = json.load(f)
            if not estado_img.get("producto_ok", False):
                imagenes_faltantes.append("producto")
            if not estado_img.get("dimensiones_ok", False):
                imagenes_faltantes.append("dimensiones")
        except Exception as e:
            print("Error leyendo estado_img.json:", e)
else:
    imagenes_faltantes = ["producto", "dimensiones"]

# 3. Consolidar estado general
estado_final = {
    "datos_faltantes": datos_faltantes,
    "imagenes_faltantes": imagenes_faltantes,
    "listo_para_generar": len(datos_faltantes) == 0 and len(imagenes_faltantes) == 0
}

with open(salida_estado, "w", encoding="utf-8") as f:
    json.dump(estado_final, f, indent=2, ensure_ascii=False)

print("Estado de extracción validado:")
print(f"- Datos faltantes: {len(datos_faltantes)}")
print(f"- Imágenes faltantes: {len(imagenes_faltantes)}")
print(f"Archivo generado: {salida_estado}")
