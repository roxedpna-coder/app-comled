import subprocess
import os
import json

print("=======================================")
print("🚀 INICIANDO: FLUJO COMPLETO PROVEEDOR")
print("=======================================\n")

# Preguntar datos clave al usuario antes de empezar
nombre_input = input("Introduce el Nombre para esta luminaria (Deja vacío si no sabes): ")
codigo_input = input("Introduce el Código COM.LED (Deja vacío si no sabes): ")
instalacion_input = input("Introduce el Tipo de Instalación (ej. empotrada, carril, colgante... Deja vacío para auto-detectar): ")

config = {}
if nombre_input.strip():
    config["nombre_comled"] = nombre_input.strip()
if codigo_input.strip():
    config["codigo_comled"] = codigo_input.strip()
if instalacion_input.strip():
    config["instalacion_manual"] = instalacion_input.strip()

with open("entradas/config_proveedor.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("\n--- COMENZANDO PROCESO ---\n")

# 1. Extracción (Backend nuevo)
print("1/10 Extrayendo datos técnicos con IA...")
subprocess.run(["python3", "backend/extraer_datos_proveedor.py"], check=True)

print("2/10 Extrayendo imágenes (Producto y Dimensiones)...")
subprocess.run(["python3", "backend/extraer_imagenes_proveedor.py"], check=True)

print("3/10 Validando extracción...")
subprocess.run(["python3", "backend/validar_extraccion_proveedor.py"], check=True)

# Revisar estado para mostrar aviso
try:
    with open("entradas/estado.json", "r") as f:
        estado = json.load(f)
        if not estado.get("listo_para_generar", True):
            print("\n⚠️ AVISO: Faltan datos (simulando que el usuario pulsa 'Generar de todos modos').")
            print(f"Faltan: {estado.get('datos_faltantes')} | {estado.get('imagenes_faltantes')}\n")
except Exception:
    pass

# 2. Procesamiento de imágenes (Reutilizando backend original)
print("4/10 Preparando imagen del producto (limpiando fondo)...")
subprocess.run(["python3", "backend/preparar_producto.py"], check=True)

print("5/10 Mejorando producto (Filtros Algorítmicos / IA)...")
subprocess.run(["python3", "backend/mejorar_producto_ia.py"], check=True)

print("6/10 Generando curva fotométrica...")
subprocess.run(["python3", "backend/generar_fotometria.py"], check=True)

print("7/10 Validando y ajustando imágenes finales...")
subprocess.run(["python3", "backend/validar_imagenes.py"], check=True)

# 3. Generación final
print("8/10 Generando reporte rápido...")
subprocess.run(["python3", "backend/reporte_prueba.py"], check=True)

print("9/10 Creando plantilla PowerPoint...")
subprocess.run(["python3", "backend/main.py"], check=True)

print("10/10 Exportando a PDF final...")
subprocess.run(["python3", "backend/exportar_pdf.py"], check=True)

print("\n=======================================")
print("✅ FICHA GENERADA EXITOSAMENTE")
print("Revisa la carpeta 'salidas/' para ver el PDF.")
print("=======================================")
