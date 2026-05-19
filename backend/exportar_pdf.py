import subprocess
import os
import json
import re

# -------------------------
# LEER JSON
# -------------------------

with open("entradas/datos.json", "r", encoding="utf-8") as f:
    datos = json.load(f)

codigo = str(
    datos.get("codigo_comled", "000000")
).strip()

nombre = str(
    datos.get("nombre_producto", "")
).strip().upper()

potencia = str(
    datos.get("potencia", "")
).strip().upper()

# -------------------------
# LIMPIAR TEXTO
# -------------------------

def limpiar_nombre_archivo(texto):

    texto = texto.replace("/", "-")
    texto = texto.replace("\\", "-")
    texto = texto.replace(":", "")
    texto = texto.replace("*", "")
    texto = texto.replace("?", "")
    texto = texto.replace('"', "")
    texto = texto.replace("<", "")
    texto = texto.replace(">", "")
    texto = texto.replace("|", "")

    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()

nombre = limpiar_nombre_archivo(nombre)
potencia = limpiar_nombre_archivo(potencia)

# -------------------------
# CREAR NOMBRE PDF
# -------------------------

partes = [f"ET CL-{codigo}"]

if nombre and nombre != "-":
    partes.append(nombre)

if potencia and potencia != "-":
    partes.append(potencia)

nombre_pdf = " ".join(partes) + ".pdf"

# -------------------------
# RUTAS
# -------------------------

pptx_path = os.path.abspath(
    "salidas/ficha_final.pptx"
)

output_dir = os.path.abspath(
    "salidas"
)

libreoffice_path = (
    "/Applications/LibreOffice.app/Contents/MacOS/soffice"
)

# -------------------------
# VALIDAR
# -------------------------

if not os.path.exists(pptx_path):

    print("No existe ficha_final.pptx")
    exit()

# -------------------------
# EXPORTAR PDF
# -------------------------

print("Exportando PDF...")

subprocess.run([
    libreoffice_path,
    "--headless",
    "--convert-to",
    "pdf",
    "--outdir",
    output_dir,
    pptx_path
], check=True)

# -------------------------
# RENOMBRAR PDF
# -------------------------

pdf_original = os.path.join(
    output_dir,
    "ficha_final.pdf"
)

pdf_final = os.path.join(
    output_dir,
    nombre_pdf
)

if os.path.exists(pdf_final):
    os.remove(pdf_final)

os.rename(
    pdf_original,
    pdf_final
)

# -------------------------
# BORRAR PPTX
# -------------------------

os.remove(pptx_path)

# -------------------------
# INYECTAR METADATOS INVISIBLES
# -------------------------

try:
    import fitz
    doc = fitz.open(pdf_final)
    meta = doc.metadata
    meta["subject"] = json.dumps(datos, ensure_ascii=False)
    doc.set_metadata(meta)
    doc.saveIncr()
    doc.close()
    print("Metadatos inyectados correctamente.")
except Exception as e:
    print(f"Advertencia: No se pudieron inyectar metadatos ({e})")

# -------------------------
# FINAL
# -------------------------

print("PDF generado correctamente:")
print(nombre_pdf)