from openai import OpenAI
from dotenv import load_dotenv
import base64
import os
from PIL import Image, ImageEnhance

load_dotenv()

input_path = "imagenes/producto_final.png"
output_path = "imagenes/producto_final.png"

if not os.path.exists(input_path):
    print("No existe imagen de producto para mejorar")
    exit()

# 1. EVALUAR CALIDAD DE LA IMAGEN
img = Image.open(input_path).convert("RGBA")
width, height = img.size
area = width * height

print("Aplicando motor de mejora matemática avanzada (Súper-resolución Lanczos y Anti-Aliasing)...")

# 1. Escalar con filtro LANCZOS (súper-resolución algorítmica) para suavizar píxeles
target_size = 1000
ratio = target_size / max(width, height)

if ratio > 1.0:
    new_size = (int(width * ratio), int(height * ratio))
    img = img.resize(new_size, Image.Resampling.LANCZOS)
    print("Resolución aumentada con interpolación de alta calidad.")

# 2. Separar canales
r, g, b, a = img.split()
rgb_img = Image.merge("RGB", (r, g, b))

# 3. Suavizar para eliminar ruido de compresión JPG y "reflejos feos/cuadriculados"
# Solo se aplica si la imagen original es de baja resolución (< 600px) para evitar difuminar imágenes HD
from PIL import ImageFilter
if max(width, height) < 600:
    rgb_img = rgb_img.filter(ImageFilter.SMOOTH)
    print("Aplicado suavizado para reducción de ruido.")

# 4. Mejorar Contraste para darle más "punch" profesional (1.15x)
enhancer_contrast = ImageEnhance.Contrast(rgb_img)
rgb_img = enhancer_contrast.enhance(1.15)

# 5. Nitidez más fuerte (1.6x) para recuperar detalles y texturas finas
enhancer_sharpness = ImageEnhance.Sharpness(rgb_img)
rgb_img = enhancer_sharpness.enhance(1.7 if max(width, height) >= 1000 else 1.6)


# 6. Reensamblar con transparencia intacta
r2, g2, b2 = rgb_img.split()
final_img = Image.merge("RGBA", (r2, g2, b2, a))

final_img.save(output_path)
print("Producto mejorado algorítmicamente y guardado.")