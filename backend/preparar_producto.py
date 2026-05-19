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
    manuales = sorted(manuales, key=os.path.getmtime, reverse=True)
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
brillo_fondo = np.mean(color_fondo)
variacion_fondo = np.std(esquinas)

fondo_blanco = brillo_fondo > 235 and variacion_fondo < 18

if fondo_blanco:
    print("Fondo blanco puro detectado: Omitiendo recorte IA para evitar daños en la luminaria.")
    procesada = img
else:
    # -------------------------
    # REMOVER FONDO CON IA (REMBG)
    # -------------------------
    try:
        from rembg import remove
        from scipy.ndimage import binary_fill_holes
        print("Fondo complejo detectado. Iniciando recorte inteligente con IA (rembg)...")
        
        # Extraer solo la máscara para poder repararla matemáticamente
        mask_img = remove(img, only_mask=True)
        mask_arr = np.array(mask_img)
        
        # Rellenar huecos internos (reflejos que la IA confundió con fondo)
        mask_filled = binary_fill_holes(mask_arr > 128)
        final_mask = np.where(mask_filled, 255, 0).astype(np.uint8)
        
        # Aplicar la máscara reparada a la imagen original intacta
        procesada = img.copy()
        procesada.putalpha(Image.fromarray(final_mask))
        arr = np.array(procesada)
        print("Recorte IA aplicado y reparado con éxito.")
    except ImportError:
        print("Advertencia: rembg no está instalado. Usando recorte básico por color...")
        fondo_gris_uniforme = (120 < brillo_fondo < 235 and variacion_fondo < 25)
        if fondo_gris_uniforme:
            distancia = np.linalg.norm(rgb - color_fondo, axis=2)
            mascara_fondo = distancia < 18
            alpha[mascara_fondo] = 0
            arr[:, :, 3] = alpha
            procesada = Image.fromarray(arr)
        else:
            procesada = img

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