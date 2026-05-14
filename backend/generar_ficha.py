import subprocess
import os

# -------------------------
# LIMPIAR ARCHIVOS ANTERIORES
# -------------------------

archivos_limpiar = [
    "imagenes/producto.png",
    "imagenes/producto_final.png",
    "imagenes/dimensiones.png",
    "imagenes/fotometria_generada.png",
    "salidas/ficha_final.pptx"
]

for archivo in archivos_limpiar:

    if os.path.exists(archivo):
        os.remove(archivo)

print("Archivos anteriores limpiados")

# -------------------------
# PIPELINE
# -------------------------

print("1/8 Extrayendo imágenes del PDF...")
subprocess.run(
    ["python3", "backend/extraer_imagenes_pdf.py"],
    check=True
)

print("2/8 Extrayendo datos técnicos...")
subprocess.run(
    ["python3", "backend/extraer_datos.py"],
    check=True
)

print("3/8 Preparando imagen del producto...")
subprocess.run(
    ["python3", "backend/preparar_producto.py"],
    check=True
)

print("4/8 Generando fotometría...")
subprocess.run(
    ["python3", "backend/generar_fotometria.py"],
    check=True
)

print("5/8 Validando imágenes...")
subprocess.run(
    ["python3", "backend/validar_imagenes.py"],
    check=True
)

# -------------------------
# REPORTE NUEVO
# -------------------------

print("6/8 Generando reporte de control...")
subprocess.run(
    ["python3", "backend/reporte_prueba.py"],
    check=True
)

print("7/8 Generando ficha PowerPoint...")
subprocess.run(
    ["python3", "backend/main.py"],
    check=True
)

print("8/8 Exportando PDF final...")
subprocess.run(
    ["python3", "backend/exportar_pdf.py"],
    check=True
)

print("Ficha COM.LED final generada correctamente")