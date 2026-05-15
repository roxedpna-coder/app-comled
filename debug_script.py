import sys
sys.path.append('backend')
from extraer_imagenes_proveedor import *
import json

print("Todas las imagenes info:")
for info in todas_las_imagenes:
    print(info["ruta"], "w:", info["width"], "h:", info["height"], "tecnica:", info["imagen_tecnica"])
