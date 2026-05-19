import fitz
import os
import shutil
import glob
from PIL import Image, ImageStat, ImageChops
import numpy as np

# -------------------------
# BUSCAR PDF MÁS RECIENTE
# -------------------------
pdfs_encontrados = glob.glob("pdfs/*.pdf") + glob.glob("pdfs/*.png") + glob.glob("pdfs/*.jpg") + glob.glob("pdfs/*.jpeg")

if not pdfs_encontrados:
    print("ERROR CRÍTICO: No se encontró ningún archivo (.pdf, .png, .jpg) en la carpeta 'pdfs/'.")
    print("Por favor, asegúrate de colocar el PDF del proveedor en la carpeta correcta antes de ejecutar.")
    exit(1)

pdf_path = max(pdfs_encontrados, key=os.path.getmtime)
print("PDF más reciente seleccionado (Proveedor):", pdf_path)

# -------------------------
# CARPETAS
# -------------------------
temp_folder = "imagenes/temp"
os.makedirs(temp_folder, exist_ok=True)
for archivo in os.listdir(temp_folder):
    os.remove(os.path.join(temp_folder, archivo))

imagenes_extraidas = []
es_imagen = pdf_path.lower().endswith(('.png', '.jpg', '.jpeg'))
doc = None

if es_imagen:
    print("Captura de pantalla detectada. Omitiendo extracción PDF y analizando la imagen directamente...")
    ext = pdf_path.split('.')[-1]
    ruta_copia = os.path.join(temp_folder, f"img_0.{ext}")
    shutil.copy(pdf_path, ruta_copia)
    # Almacenamos la tupla (ruta, num_pagina)
    imagenes_extraidas.append((ruta_copia, 0))
else:
    # -------------------------
    # ABRIR PDF Y EXTRAER IMÁGENES EMBEBIDAS
    # -------------------------
    doc = fitz.open(pdf_path)
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
                # Almacenamos la tupla (ruta, num_pagina)
                imagenes_extraidas.append((ruta, num_pagina))
                contador += 1
            except Exception as e:
                pass

# -------------------------
# ANALIZAR IMAGEN
# -------------------------
def analizar_imagen(ruta, num_pagina):
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
        # Umbral rebajado a 0.80 para capturar planos de cotas con líneas/textos finos
        imagen_tecnica = porcentaje_blanco > 0.80
        
        midtones = sum(histograma[50:200])
        porcentaje_midtones = midtones / pixeles_totales if pixeles_totales > 0 else 0
        es_logo = porcentaje_midtones < 0.05
        
        # Evaluar variación del fondo esquina por esquina de forma individual
        # Esto evita que logos o textos en una sola esquina descarten una foto de estudio real.
        arr = np.array(img.convert("RGB"))
        h, w = arr.shape[:2]
        if h > 40 and w > 40:
            c1 = arr[:20, :20].reshape(-1, 3)
            c2 = arr[:20, -20:].reshape(-1, 3)
            c3 = arr[-20:, :20].reshape(-1, 3)
            c4 = arr[-20:, -20:].reshape(-1, 3)
            stds = [float(np.std(c)) for c in [c1, c2, c3, c4]]
            esquinas_uniformes = sum(1 for s in stds if s < 10)
        else:
            esquinas_uniformes = 0

        return {
            "ruta": ruta, "width": width, "height": height, "area": area,
            "brillo": brillo, "dominante_verde": dominante_verde, "imagen_tecnica": imagen_tecnica,
            "es_logo": es_logo, "porcentaje_blanco": porcentaje_blanco, 
            "esquinas_uniformes": esquinas_uniformes, "pagina": num_pagina
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

    for ruta, num_pagina in imagenes_extraidas:
        info = analizar_imagen(ruta, num_pagina)
        if not info: continue
        
        todas_las_imagenes.append(info)

        if info["width"] < 80 or info["height"] < 80: continue
        if info["brillo"] < 25: continue
        if info["dominante_verde"]: continue
        if info.get("es_logo", False): continue
        
        # Al menos 2 de las 4 esquinas deben ser uniformes (fondo liso/estudio)
        # Esto filtra fotos complejas de ambiente (sofás, oficinas) pero mantiene fotos de estudio reales
        if info.get("esquinas_uniformes", 0) < 2: continue
        
        if info["imagen_tecnica"]:
            candidatas_tecnicas.append(info)
            continue
        
        # Filtro de proporción geométrica (aspect ratio) para ignorar logos alargados o banners
        # Excepción: si la imagen es GIGANTE (>100000 px), podría ser un tubo lineal, así que la dejamos pasar.
        ratio = info["width"] / info["height"]
        if (ratio > 1.9 or ratio < 0.4) and info["area"] < 100000:
            continue

        candidatas_producto.append(info)

    # SISTEMA DE PUNTUACIÓN SEMÁNTICA PARA DIBUJOS TÉCNICOS / COTAS
    # Evita elegir esquemas de cableado (DMX, drivers) en lugar de cotas reales
    keywords_dim_positivos = ["LIGHT SIZE", "DIMENSIONAL DRAWING", "DIMENSION DRAWING", "DIMENSIONS", "MEDIDAS", "CROQUIS", "ESQUEMA", "UNIT: MM", "SIZE"]
    keywords_dim_negativos = ["CONTROLLER", "WIRING", "CONNECTION", "CONEXION", "DMX", "WIRING DIAGRAM", "PROJECT CASE", "CASE", "CONTROL", "SISTEMA DE CONTROL"]

    for info in candidatas_tecnicas:
        score = 0
        if doc:  # Solo si proviene de un PDF (para imágenes no hay doc/páginas de texto)
            try:
                text = doc[info["pagina"]].get_text().upper()
                if any(p in text for p in keywords_dim_positivos):
                    score += 100
                if any(n in text for n in keywords_dim_negativos):
                    score -= 300
            except:
                pass
        info["score"] = score

    candidatas_producto = sorted(candidatas_producto, key=lambda x: x["area"], reverse=True)
    candidatas_tecnicas = sorted(candidatas_tecnicas, key=lambda x: (x.get("score", 0), x["area"]), reverse=True)

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
        
        # Umbral muy sensible: 252 detectará cualquier gris anti-aliasing sin coger blanco puro
        mask = arr < 252
        filas = np.where(mask.sum(axis=1) > 0)[0]
        cols = np.where(mask.sum(axis=0) > 0)[0]
        
        if len(filas) == 0 or len(cols) == 0:
            img.save(salida_path)
            return

        x0, x1 = cols[0], cols[-1]
        y0, y1 = filas[0], filas[-1]
        
        margen = 25
        left = max(x0 - margen, 0)
        top = max(y0 - margen, 0)
        right = min(x1 + margen, img.width)
        bottom = min(y1 + margen, img.height)

        recorte = img.crop((left, top, right, bottom))
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
    
    keywords_dim = ["DIMENSIONAL DRAWING", "DIMENSION DRAWING", "DIMENSIONS", "MEDIDAS", "DRAWING", "UNIT: MM", "ESQUEMA", "CROQUIS"]
    
    for kw in keywords_dim:
        pass
        
    if doc:
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
        # Abarcar todo el ancho de la página para no cortar nada
        rect_dimensiones = fitz.Rect(0, top, page_width, bottom)
            
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

if doc:
    doc.close()
print("Proceso de extracción de imágenes completado (Proveedor)")
