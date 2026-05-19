from PIL import Image, ImageChops, ImageFilter
import os
import numpy as np

# -------------------------
# RUTAS
# -------------------------

producto_path = "imagenes/producto_final.png"
dimensiones_path = "imagenes/dimensiones.png"

# -------------------------
# RECORTAR TRANSPARENCIA
# -------------------------

def recortar_transparencia(img):
    bbox = img.getbbox()

    if bbox:
        return img.crop(bbox)

    return img


# -------------------------
# DETECTAR SI LA IMAGEN ES MUY CLARA
# -------------------------

def imagen_es_clara(img):
    img_rgb = img.convert("RGB")
    arr = np.array(img_rgb)

    brillo = np.mean(arr)

    return brillo > 180


# -------------------------
# RECORTAR FONDO CLARO SIN COMER PRODUCTO BLANCO
# -------------------------

def recortar_fondo_claro(img):
    img_rgba = img.convert("RGBA")
    
    # Si la imagen ya tiene fondo transparente (gracias a rembg en el paso 4),
    # simplemente la devolvemos sin aplicar filtros de color destructivos
    arr = np.array(img_rgba)
    alpha = arr[:, :, 3]
    if np.any(alpha < 50):
        print("Producto con fondo transparente detectado. Omitiendo limpieza destructiva.")
        return img_rgba

    if imagen_es_clara(img_rgba):
        print("Producto claro detectado: limpieza suave de fondo")

        img_rgb = img_rgba.convert("RGB")

        fondo = Image.new(
            "RGB",
            img_rgb.size,
            (255, 255, 255)
        )

        diff = ImageChops.difference(img_rgb, fondo)
        bbox = diff.getbbox()

        if bbox:
            margen = 25

            left = max(bbox[0] - margen, 0)
            top = max(bbox[1] - margen, 0)
            right = min(bbox[2] + margen, img_rgba.width)
            bottom = min(bbox[3] + margen, img_rgba.height)

            return img_rgba.crop((left, top, right, bottom))

        return img_rgba

    print("Producto oscuro detectado: limpieza fuerte de fondo")

    data = np.array(img_rgba)

    rgb = data[:, :, :3]
    alpha = data[:, :, 3]

    r = rgb[:, :, 0]
    g = rgb[:, :, 1]
    b = rgb[:, :, 2]

    fondo = (
        (r > 150) &
        (g > 150) &
        (b > 150)
    )

    alpha[fondo] = 0

    data[:, :, 3] = alpha

    img_limpia = Image.fromarray(data)

    bbox = img_limpia.getbbox()

    if bbox:
        img_limpia = img_limpia.crop(bbox)

    return img_limpia


# -------------------------
# MEJORAR CALIDAD PRODUCTO
# -------------------------

def mejorar_calidad_producto(img):
    img = img.convert("RGBA")

    ancho, alto = img.size
    lado_mayor = max(ancho, alto)

    # Si la imagen viene pequeña, la ampliamos antes de insertarla en PPT
    if lado_mayor < 900:
        factor = 3
        print("Producto pequeño detectado: aumentando resolución x3")

    elif lado_mayor < 1400:
        factor = 2
        print("Producto mediano detectado: aumentando resolución x2")

    else:
        factor = 1
        print("Producto con resolución suficiente")

    if factor > 1:
        img = img.resize(
            (
                img.width * factor,
                img.height * factor
            ),
            Image.LANCZOS
        )

    # Nitidez suave para evitar que se vea borroso
    img = img.filter(
        ImageFilter.UnsharpMask(
            radius=1.6,
            percent=145,
            threshold=3
        )
    )

    return img


# -------------------------
# RECORTAR BLANCO
# -------------------------

def recortar_blanco(img):
    img_rgba = img.convert("RGBA")
    img_rgb = img_rgba.convert("RGB")

    fondo = Image.new(
        "RGB",
        img_rgb.size,
        (255, 255, 255)
    )

    diff = ImageChops.difference(img_rgb, fondo)
    bbox = diff.getbbox()

    if bbox:
        margen = 35

        left = max(bbox[0] - margen, 0)
        top = max(bbox[1] - margen, 0)
        right = min(bbox[2] + margen, img_rgba.width)
        bottom = min(bbox[3] + margen, img_rgba.height)

        return img_rgba.crop((left, top, right, bottom))

    return img_rgba


# -------------------------
# VALIDAR PRODUCTO
# -------------------------

def validar_producto():
    if not os.path.exists(producto_path):
        print("No existe producto_final.png")
        return

    img = Image.open(producto_path).convert("RGBA")

    img = recortar_transparencia(img)
    img = recortar_fondo_claro(img)
    img = recortar_transparencia(img)

    # Mejorar resolución y nitidez antes de guardar
    img = mejorar_calidad_producto(img)

    margen = 25

    canvas = Image.new(
        "RGBA",
        (
            img.width + margen * 2,
            img.height + margen * 2
        ),
        (255, 255, 255, 0)
    )

    canvas.paste(
        img,
        (margen, margen),
        img
    )

    canvas.save(producto_path)

    print("Producto validado, ampliado y mejorado")


# -------------------------
# VALIDAR DIMENSIONES
# -------------------------

def validar_dimensiones():
    if not os.path.exists(dimensiones_path):
        print("No existe dimensiones.png")
        return

    img = Image.open(dimensiones_path).convert("RGBA")

    img = recortar_blanco(img)

    margen = 30

    canvas = Image.new(
        "RGBA",
        (
            img.width + margen * 2,
            img.height + margen * 2
        ),
        (255, 255, 255, 0)
    )

    canvas.paste(
        img,
        (margen, margen),
        img
    )

    canvas.save(dimensiones_path)

    print("Dimensiones validadas y recortadas")


# -------------------------
# EJECUTAR
# -------------------------

validar_producto()
validar_dimensiones()

print("Validación de imágenes completada")