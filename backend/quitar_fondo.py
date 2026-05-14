from rembg import remove
from PIL import Image

print("Iniciando eliminación de fondo...")

input_path = "imagenes/producto.png"
output_path = "imagenes/producto_sin_fondo.png"

input_image = Image.open(input_path)

output_image = remove(input_image)

output_image.save(output_path)

print("Fondo eliminado correctamente")
print("Imagen guardada en:")
print(output_path)