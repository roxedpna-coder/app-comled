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

# Si la imagen es decente (> 250x250), la IA generativa la va a arruinar.
# Aplicamos mejoras fotográficas tradicionales (nitidez y contraste).
if area > 62500:
    print("Imagen de calidad aceptable. Aplicando mejora fotográfica profesional sin IA generativa...")
    
    # Separar alpha para no afectar la transparencia
    r, g, b, a = img.split()
    rgb_img = Image.merge("RGB", (r, g, b))
    
    # Mejorar Contraste suavemente (1.15x)
    enhancer_contrast = ImageEnhance.Contrast(rgb_img)
    rgb_img = enhancer_contrast.enhance(1.15)
    
    # Mejorar Nitidez (1.5x) para bordes de catálogo
    enhancer_sharpness = ImageEnhance.Sharpness(rgb_img)
    rgb_img = enhancer_sharpness.enhance(1.5)
    
    # Reensamblar con transparencia
    r2, g2, b2 = rgb_img.split()
    final_img = Image.merge("RGBA", (r2, g2, b2, a))
    final_img.save(output_path)
    print("Producto mejorado algorítmicamente.")
    
else:
    # 2. SOLO SI ES MUY PEQUEÑA O MALA, USAMOS OPENAI
    print("Imagen de baja calidad detectada. Ejecutando IA Generativa...")
    client = OpenAI()
    
    prompt = """
    Aumenta sutilmente la resolución de esta luminaria técnica.
    REGLA DE ORO: NO pintes, NO inventes reflejos blancos exagerados, NO alteres el metal.
    Mantén la textura realista 100% fiel al original. Solo elimina ruido y mejora nitidez de los bordes.
    Fondo transparente.
    """
    
    with open(input_path, "rb") as image_file:
        try:
            result = client.images.edit(
                model="dall-e-2", # gpt-image-1 no es un modelo estandar
                image=image_file,
                prompt=prompt,
                size="1024x1024"
            )
            
            image_base64 = result.data[0].b64_json
            
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(image_base64))
                
            print("Producto mejorado con IA generativa correctamente.")
        except Exception as e:
            print(f"La IA generativa falló (o fue rechazada por la API). Se mantiene original. Error: {e}")