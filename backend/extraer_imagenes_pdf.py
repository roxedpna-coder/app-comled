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
print("PDF más reciente seleccionado:", pdf_path)

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

for img in pagina.get_images(full=True):
    xref = img[0]
    base_image = doc.extract_image(xref)

    image_bytes = base_image["image"]
    image_ext = base_image["ext"]

    ruta = os.path.join(temp_folder, f"img_{contador}.{image_ext}")

    with open(ruta, "wb") as f:
        f.write(image_bytes)

    print("Imagen extraída:", ruta)

    imagenes_extraidas.append(ruta)
    contador += 1


# -------------------------
# ANALIZAR IMAGEN
# -------------------------

def analizar_imagen(ruta):
    try:
        img = Image.open(ruta).convert("RGB")

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
        porcentaje_blanco = blancos / pixeles_totales

        imagen_tecnica = porcentaje_blanco > 0.92

        return {
            "ruta": ruta,
            "width": width,
            "height": height,
            "area": area,
            "brillo": brillo,
            "dominante_verde": dominante_verde,
            "imagen_tecnica": imagen_tecnica
        }

    except:
        return None


# -------------------------
# PRODUCTO MANUAL O AUTOMÁTICO
# -------------------------

manuales_producto = []
manuales_producto.extend(glob.glob("imagenes/manual/producto.*"))
manuales_producto.extend(glob.glob("imagenes/manual/*producto*.*"))

if manuales_producto:
    shutil.copy(manuales_producto[0], "imagenes/producto.png")
    print("Producto manual copiado:", manuales_producto[0])

else:
    candidatas_producto = []

    for ruta in imagenes_extraidas:
        info = analizar_imagen(ruta)

        if not info:
            continue

        if info["width"] < 80 or info["height"] < 80:
            continue

        if info["brillo"] < 25:
            continue

        if info["dominante_verde"]:
            continue

        if info["imagen_tecnica"]:
            continue

        candidatas_producto.append(info)

    candidatas_producto = sorted(
        candidatas_producto,
        key=lambda x: x["area"],
        reverse=True
    )

    if candidatas_producto:
        producto = candidatas_producto[0]["ruta"]
        shutil.copy(producto, "imagenes/producto.png")
        print("Producto detectado:", producto)

    else:
        print("Producto no detectado como imagen embebida")
        print("Intentando recortes automáticos del área de producto...")

        page_width = pagina.rect.width
        page_height = pagina.rect.height

        zonas_producto = [
            # Zona superior derecha: habitual en fichas COM.LED antiguas
            fitz.Rect(
                page_width * 0.56,
                page_height * 0.05,
                page_width * 0.98,
                page_height * 0.34
            ),

            # Zona superior izquierda/media: segundo intento
            fitz.Rect(
                page_width * 0.03,
                page_height * 0.10,
                page_width * 0.58,
                page_height * 0.46
            ),

            # Zona izquierda media: tercer intento
            fitz.Rect(
                page_width * 0.03,
                page_height * 0.15,
                page_width * 0.52,
                page_height * 0.55
            ),
        ]

        mejor_crop = None
        mejor_score = 0

        for i, rect_producto in enumerate(zonas_producto):

            ruta_temp_producto = f"imagenes/temp/producto_recorte_{i}.png"

            pix_producto = pagina.get_pixmap(
                matrix=fitz.Matrix(4, 4),
                clip=rect_producto,
                alpha=False
            )

            pix_producto.save(ruta_temp_producto)

            img_crop = Image.open(ruta_temp_producto).convert("RGB")
            gris = img_crop.convert("L")
            arr = np.array(gris)

            # Detectar contenido no blanco
            mask = arr < 245

            filas = np.where(mask.sum(axis=1) > 10)[0]
            cols = np.where(mask.sum(axis=0) > 10)[0]

            if len(filas) > 0 and len(cols) > 0:

                margen = 35

                left = max(cols[0] - margen, 0)
                top = max(filas[0] - margen, 0)
                right = min(cols[-1] + margen, img_crop.width)
                bottom = min(filas[-1] + margen, img_crop.height)

                producto_crop = img_crop.crop(
                    (left, top, right, bottom)
                )

                # Score: contenido útil, evitando recortes gigantes vacíos
                contenido = mask.sum()
                area_crop = producto_crop.width * producto_crop.height

                if area_crop == 0:
                    continue

                densidad = contenido / area_crop

                score = contenido * densidad

                if score > mejor_score:
                    mejor_score = score
                    mejor_crop = producto_crop

        if mejor_crop:
            mejor_crop.save("imagenes/producto.png")
            print("Producto extraído mediante mejor recorte automático")
        else:
            print("No se pudo extraer producto automáticamente")


# -------------------------
# FUNCIÓN: RECORTAR SOLO DIBUJO TÉCNICO
# -------------------------

def recortar_dibujo_tecnico(imagen_path, salida_path):
    try:
        img = Image.open(imagen_path).convert("RGB")
        gris = img.convert("L")
        arr = np.array(gris)
        
        mask = arr < 252
        filas = np.where(mask.sum(axis=1) > 0)[0]
        cols = np.where(mask.sum(axis=0) > 0)[0]
        
        if len(filas) == 0 or len(cols) == 0:
            img.save(salida_path)
            return

        col_counts = mask.sum(axis=0)
        columnas_activas = np.where(col_counts > 0)[0]

        grupos = []
        if len(columnas_activas) > 0:
            inicio = columnas_activas[0]
            anterior = columnas_activas[0]

            for c in columnas_activas[1:]:
                # 200 píxeles es un margen seguro para agrupar las cotas con el dibujo en alta resolución
                if c - anterior > 200:
                    grupos.append((inicio, anterior))
                    inicio = c
                anterior = c

            grupos.append((inicio, anterior))

        if grupos:
            ancho_img = img.width

            grupos_filtrados = [
                g for g in grupos
                if g[1] > ancho_img * 0.35
            ]

            if not grupos_filtrados:
                grupos_filtrados = grupos

            def score_grupo(g):
                x0, x1 = g
                ancho = x1 - x0
                pixeles = col_counts[x0:x1].sum()
                posicion = x1 / ancho_img
                return pixeles + ancho * 10 + posicion * 500

            mejor_grupo = max(grupos_filtrados, key=score_grupo)
            x0, x1 = mejor_grupo

            margen_x = 45
            x0 = max(x0 - margen_x, 0)
            x1 = min(x1 + margen_x, img.width)

            submask = mask[:, x0:x1]
            filas_sub = np.where(submask.sum(axis=1) > 0)[0]

            if len(filas_sub) > 0:
                y0 = filas_sub[0]
                y1 = filas_sub[-1]
            else:
                y0 = filas[0]
                y1 = filas[-1]

        else:
            x0 = cols[0]
            x1 = cols[-1]
            y0 = filas[0]
            y1 = filas[-1]

        margen = 45
        left = max(x0 - margen, 0)
        top = max(y0 - margen, 0)
        right = min(x1 + margen, img.width)
        bottom = min(y1 + margen, img.height)

        recorte = img.crop((left, top, right, bottom))
        recorte.save(salida_path)
    except Exception as e:
        print("Error recortando dibujo tecnico:", e)


# -------------------------
# DIMENSIONES MANUALES O AUTOMÁTICAS
# -------------------------

manuales_dimensiones = []
manuales_dimensiones.extend(glob.glob("imagenes/manual/dimensiones.*"))
manuales_dimensiones.extend(glob.glob("imagenes/manual/*dimensiones*.*"))

if manuales_dimensiones:
    shutil.copy(manuales_dimensiones[0], "imagenes/dimensiones.png")
    print("Dimensiones manuales copiadas:", manuales_dimensiones[0])

else:
    bloques = pagina.get_text("blocks")

    bloque_dimensiones = None
    bloque_distribucion = None

    for bloque in bloques:
        x0, y0, x1, y1, texto, *_ = bloque
        texto_mayus = texto.upper()

        if "DIMENSIONES" in texto_mayus and x0 > pagina.rect.width * 0.40:
            bloque_dimensiones = bloque

        if "DISTRIBUCIÓN" in texto_mayus or "DISTRIBUCION" in texto_mayus:
            if x0 > pagina.rect.width * 0.40:
                bloque_distribucion = bloque
                break

    page_width = pagina.rect.width
    page_height = pagina.rect.height

    if bloque_dimensiones:
        x0, y0, x1, y1, texto, *_ = bloque_dimensiones

        top = y1 + 5

        if bloque_distribucion:
            bottom = bloque_distribucion[1] - 5
        else:
            bottom = y1 + page_height * 0.25

        rect_dimensiones = fitz.Rect(
            page_width * 0.35,
            top,
            page_width * 0.98,
            bottom
        )

    else:
        rect_dimensiones = fitz.Rect(
            page_width * 0.35,
            page_height * 0.23,
            page_width * 0.98,
            page_height * 0.52
        )

    pix = pagina.get_pixmap(
        matrix=fitz.Matrix(4, 4),
        clip=rect_dimensiones,
        alpha=False
    )

    ruta_temp_dim = "imagenes/temp/dimensiones_recorte_bruto.png"
    pix.save(ruta_temp_dim)

    recortar_dibujo_tecnico(
        ruta_temp_dim,
        "imagenes/dimensiones.png"
    )

    print("Dimensiones detectadas y recortadas al dibujo técnico")


doc.close()

print("Proceso completado")