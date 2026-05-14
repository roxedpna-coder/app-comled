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

print("1/9 Extrayendo imágenes del PDF...")
subprocess.run(
    ["python3", "backend/extraer_imagenes_pdf.py"],
    check=True
)

print("2/9 Extrayendo datos técnicos...")
subprocess.run(
    ["python3", "backend/extraer_datos.py"],
    check=True
)

print("3/9 Preparando imagen del producto...")
subprocess.run(
    ["python3", "backend/preparar_producto.py"],
    check=True
)

# -------------------------
# NUEVO PASO IA
# -------------------------

print("4/9 Mejorando producto con IA...")
subprocess.run(
    ["python3", "backend/mejorar_producto_ia.py"],
    check=True
)

print("5/9 Generando fotometría...")
subprocess.run(
    ["python3", "backend/generar_fotometria.py"],
    check=True
)

print("6/9 Validando imágenes...")
subprocess.run(
    ["python3", "backend/validar_imagenes.py"],
    check=True
)

# -------------------------
# REPORTE
# -------------------------

print("7/9 Generando reporte de control...")
subprocess.run(
    ["python3", "backend/reporte_prueba.py"],
    check=True
)

print("8/9 Generando ficha PowerPoint...")
subprocess.run(
    ["python3", "backend/main.py"],
    check=True
)

print("9/9 Exportando PDF final...")
subprocess.run(
    ["python3", "backend/exportar_pdf.py"],
    check=True
)

print("Ficha COM.LED final generada correctamente")