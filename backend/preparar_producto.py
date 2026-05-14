from PIL import Image
import os
import glob
import numpy as np

# -------------------------
# BUSCAR IMAGEN MANUAL O EXTRAÍDA
# -------------------------

manuales = []
manuales.extend(glob.glob("imagenes/manual/producto.*"))
manuales.extend(glob.glob("imagenes/manual/*producto*.*"))

if manuales:
    input_path = manuales[0]
    print("Usando imagen manual:", input_path)
else:
    input_path = "imagenes/producto.png"
    print("Usando imagen extraída:", input_path)

output_path = "imagenes/producto_final.png"

if not os.path.exists(input_path):
    print("No existe imagen de producto:", input_path)
    exit()

# -------------------------
# ABRIR IMAGEN
# -------------------------

img = Image.open(input_path).convert("RGBA")
arr = np.array(img)

rgb = arr[:, :, :3]
alpha = arr[:, :, 3]

# -------------------------
# DETECTAR COLOR DE FONDO
# -------------------------

esquinas = np.concatenate([
    rgb[:40, :40].reshape(-1, 3),
    rgb[:40, -40:].reshape(-1, 3),
    rgb[-40:, :40].reshape(-1, 3),
    rgb[-40:, -40:].reshape(-1, 3),
])

color_fondo = np.mean(esquinas, axis=0)

r, g, b = color_fondo
brillo_fondo = np.mean(color_fondo)
variacion_fondo = np.std(esquinas)

print("Color fondo detectado:", color_fondo)
print("Brillo fondo:", brillo_fondo)
print("Variación fondo:", variacion_fondo)

# -------------------------
# DECIDIR SI TOCAR FONDO
# -------------------------

fondo_blanco = brillo_fondo > 235 and variacion_fondo < 18
fondo_gris_uniforme = (
    120 < brillo_fondo < 235
    and abs(r - g) < 15
    and abs(g - b) < 15
    and variacion_fondo < 25
)

if fondo_blanco:
    print("Fondo blanco detectado: no se modifica el fondo")

elif fondo_gris_uniforme:
    print("Fondo gris uniforme detectado: convirtiendo a transparente")

    distancia = np.linalg.norm(rgb - color_fondo, axis=2)

    mascara_fondo = distancia < 45
    alpha[mascara_fondo] = 0

    arr[:, :, 3] = alpha

else:
    print("Fondo no uniforme: no se modifica automáticamente")

# -------------------------
# RECORTAR TRANSPARENCIA / CONTENIDO
# -------------------------

procesada = Image.fromarray(arr)

bbox = procesada.getbbox()

if bbox:
    producto = procesada.crop(bbox)
else:
    producto = procesada

# -------------------------
# AÑADIR MARGEN
# -------------------------

margen = 20

canvas = Image.new(
    "RGBA",
    (producto.width + margen * 2, producto.height + margen * 2),
    (255, 255, 255, 0)
)

canvas.paste(producto, (margen, margen), producto)

canvas.save(output_path)

print("Producto final generado:", output_path)