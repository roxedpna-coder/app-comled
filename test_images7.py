import sys
sys.path.append('backend')
from extraer_imagenes_proveedor import analizar_imagen

# We need to simulate the extraction to temp
import fitz
import os
doc = fitz.open("pdfs/TUB 4.pdf")
base_image = doc.extract_image(92) # xref 92 is img_3 (wait, earlier I said xref 34 is tube, xref 92 is img_3 on page 1)
with open("imagenes/temp/test_dim.png", "wb") as f:
    f.write(base_image["image"])

print(analizar_imagen("imagenes/temp/test_dim.png"))
