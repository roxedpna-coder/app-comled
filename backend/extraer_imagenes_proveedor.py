import fitz
import os
import shutil
import glob
from PIL import Image, ImageStat, ImageChops
import numpy as np

# -------------------------
# BUSCAR PDF MÁS RECIENTE
# -------------------------
pdfs_encontrados = glob.glob("pdfs/*.pdf")

if not pdfs_encontrados:
    print("No se encontró ningún PDF en la carpeta pdfs")
    exit()

pdf_path = max(pdfs_encontrados, key=os.path.getmtime)
print("PDF más reciente seleccionado (Proveedor):", pdf_path)

# -------------------------
# CARPETAS
# -------------------------
temp_folder = "imagenes/temp"
os.makedirs(temp_folder, exist_ok=True)
for archivo in os.listdir(temp_folder):
    os.remove(os.path.join(temp_folder, archivo))

# -------------------------
# ABRIR PDF
# -------------------------
doc = fitz.open(pdf_path)
pagina = doc[0]

# -------------------------
# EXTRAER IMÁGENES EMBEBIDAS
# -------------------------
imagenes_extraidas = []
contador = 0

for num_pagina, pagina_doc in enumerate(doc):
    for img in pagina_doc.get_images(full=True):
        xref = img[0]
        try:
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            ruta = os.path.join(temp_folder, f"img_{contador}.{image_ext}")
            with open(ruta, "wb") as f:
                f.write(image_bytes)
            imagenes_extraidas.append(ruta)
            contador += 1
        except Exception as e:
            pass

# -------------------------
# ANALIZAR IMAGEN
# -------------------------
def analizar_imagen(ruta):
    try:
        img_original = Image.open(ruta)
        
        # Si tiene canal alfa (transparente), poner fondo blanco para no leerlo como negro
        if img_original.mode in ('RGBA', 'LA') or (img_original.mode == 'P' and 'transparency' in img_original.info):
            img = Image.new("RGB", img_original.size, (255, 255, 255))
            img.paste(img_original, mask=img_original.convert('RGBA').split()[3])
        else:
            img = img_original.convert("RGB")
            
        width, height = img.size
        area = width * height
        stat = ImageStat.Stat(img)
        brillo = sum(stat.mean) / 3
        r, g, b = stat.mean
        dominante_verde = g > r * 1.4 and g > b * 1.4
        
        gris = img.convert("L")
        histograma = gris.histogram()
        pixeles_totales = sum(histograma)
        blancos = sum(histograma[225:256])
        porcentaje_blanco = blancos / pixeles_totales if pixeles_totales > 0 else 0
        imagen_tecnica = porcentaje_blanco > 0.85

        return {
            "ruta": ruta, "width": width, "height": height, "area": area,
            "brillo": brillo, "dominante_verde": dominante_verde, "imagen_tecnica": imagen_tecnica
        }
    except:
        return None

# -------------------------
# PRODUCTO
# -------------------------
producto_detectado = False

# Primero revisar si el usuario lo puso manual
manuales_producto = glob.glob("imagenes/manual/producto.*") + glob.glob("imagenes/manual/*producto*.*")
if manuales_producto:
    shutil.copy(manuales_producto[0], "imagenes/producto.png")
    print("Producto manual copiado:", manuales_producto[0])
    producto_detectado = True
else:
    todas_las_imagenes = []
    candidatas_producto = []
    candidatas_tecnicas = []

    for ruta in imagenes_extraidas:
        info = analizar_imagen(ruta)
        if not info: continue
        
        todas_las_imagenes.append(info)

        if info["width"] < 80 or info["height"] < 80: continue
        if info["brillo"] < 25: continue
        if info["dominante_verde"]: continue
        
        if info["imagen_tecnica"]:
            candidatas_tecnicas.append(info)
            continue
        
        # Filtro de proporción geométrica (aspect ratio) para ignorar logos alargados o banners
        # Excepción: si la imagen es GIGANTE (>100000 px), podría ser un tubo lineal, así que la dejamos pasar.
        ratio = info["width"] / info["height"]
        if (ratio > 1.9 or ratio < 0.4) and info["area"] < 100000:
            continue

        candidatas_producto.append(info)

    candidatas_producto = sorted(candidatas_producto, key=lambda x: x["area"], reverse=True)
    candidatas_tecnicas = sorted(candidatas_tecnicas, key=lambda x: x["area"], reverse=True)

    if candidatas_producto:
        producto = candidatas_producto[0]["ruta"]
        shutil.copy(producto, "imagenes/producto.png")
        print("Producto detectado (embebido):", producto)
        producto_detectado = True
    else:
        # Nota: Al ser proveedor, evitar hacer recortes "a ciegas" por coordenadas estáticas
        # Si no detectamos imagen incrustada de producto, fallamos con elegancia para que el UI lo pida.
        print("Advertencia: No se detectó imagen de producto automáticamente. El usuario deberá aportarla.")
        # Se genera archivo dummy transparente para que el pipeline no colapse
        img_vacia = Image.new('RGBA', (500, 500), (255, 255, 255, 0))
        img_vacia.save("imagenes/producto.png")

# -------------------------
# FUNCIÓN: RECORTAR SOLO DIBUJO TÉCNICO
# -------------------------
def recortar_dibujo_tecnico(imagen_path, salida_path):
    try:
        img = Image.open(imagen_path).convert("RGB")
        gris = img.convert("L")
        arr = np.array(gris)
        mask = arr < 225
        filas = np.where(mask.sum(axis=1) > 3)[0]
        cols = np.where(mask.sum(axis=0) > 3)[0]
        
        if len(filas) == 0 or len(cols) == 0:
            img.save(salida_path)
            return

        x0, x1 = cols[0], cols[-1]
        y0, y1 = filas[0], filas[-1]
        margen = 45
        left = max(x0 - margen, 0)
        top = max(y0 - margen, 0)
        right = min(x1 + margen, img.width)
        bottom = min(y1 + margen, img.height)

        recorte = img.crop((left, top, right, bottom))
        fondo = Image.new("RGB", recorte.size, (255, 255, 255))
        diff = ImageChops.difference(recorte, fondo)
        bbox = diff.getbbox()

        if bbox:
            left2 = max(bbox[0] - 25, 0)
            top2 = max(bbox[1] - 25, 0)
            right2 = min(bbox[2] + 25, recorte.width)
            bottom2 = min(bbox[3] + 25, recorte.height)
            recorte = recorte.crop((left2, top2, right2, bottom2))

        recorte.save(salida_path)
    except Exception as e:
        print("Error recortando dibujo tecnico:", e)

# -------------------------
# DIMENSIONES
# -------------------------
dimensiones_detectadas = False
manuales_dimensiones = glob.glob("imagenes/manual/dimensiones.*") + glob.glob("imagenes/manual/*dimensiones*.*")

if manuales_dimensiones:
    shutil.copy(manuales_dimensiones[0], "imagenes/dimensiones.png")
    print("Dimensiones manuales copiadas:", manuales_dimensiones[0])
    dimensiones_detectadas = True
else:
    bloque_dimensiones = None
    pagina_dimensiones = None
    
    keywords_dim = ["DIMENSIONES", "DIMENSIONS", "SIZE", "MEDIDAS", "DRAWING", "UNIT: MM", "DIMENSION"]
    
    for num_pagina, pagina_doc in enumerate(doc):
        bloques = pagina_doc.get_text("blocks")
        for bloque in bloques:
            x0, y0, x1, y1, texto, *_ = bloque
            texto_mayus = texto.upper()
            if any(kw in texto_mayus for kw in keywords_dim):
                bloque_dimensiones = bloque
                pagina_dimensiones = pagina_doc
                break
        if bloque_dimensiones:
            break
            
    if candidatas_tecnicas and candidatas_tecnicas[0]["area"] > 5000:
        tecnica = candidatas_tecnicas[0]["ruta"]
        shutil.copy(tecnica, "imagenes/dimensiones.png")
        print("Dimensiones detectadas por análisis de imagen técnica flotante")
        dimensiones_detectadas = True
    elif bloque_dimensiones:
        page_width = pagina_dimensiones.rect.width
        page_height = pagina_dimensiones.rect.height
        x0, y0, x1, y1, texto, *_ = bloque_dimensiones
        # Se recorta el area de debajo del titulo encontrado
        top = y1 + 5
        bottom = min(y1 + page_height * 0.35, page_height)
        # Asume que el dibujo esta en la mitad en la que se encontro el texto
        if x0 > page_width * 0.5:
            rect_dimensiones = fitz.Rect(page_width * 0.45, top, page_width * 0.98, bottom)
        else:
            rect_dimensiones = fitz.Rect(page_width * 0.02, top, page_width * 0.55, bottom)
            
        pix = pagina_dimensiones.get_pixmap(matrix=fitz.Matrix(4, 4), clip=rect_dimensiones, alpha=False)
        ruta_temp_dim = "imagenes/temp/dimensiones_recorte_bruto.png"
        pix.save(ruta_temp_dim)
        recortar_dibujo_tecnico(ruta_temp_dim, "imagenes/dimensiones.png")
        print("Dimensiones detectadas por keyword")
        dimensiones_detectadas = True
    else:
        print("Advertencia: No se detectó esquema de dimensiones. El usuario deberá aportarla.")
        img_vacia = Image.new('RGBA', (500, 500), (255, 255, 255, 0))
        img_vacia.save("imagenes/dimensiones.png")

# Guardar estado de imagenes para la UI
estado_img = {
    "producto_ok": producto_detectado,
    "dimensiones_ok": dimensiones_detectadas
}
import json
with open("entradas/estado_img.json", "w", encoding="utf-8") as f:
    json.dump(estado_img, f)

doc.close()
print("Proceso de extracción de imágenes completado (Proveedor)")
