from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import subprocess
import os
import json
import shutil
import platform
from typing import Optional

app = FastAPI(title="COM.LED Fichas Técnicas API", version="1.0")

# Permitir CORS para desarrollo local (React en puerto 5173 o similar)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorios del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDFS_DIR = os.path.join(BASE_DIR, "pdfs")
ENTRADAS_DIR = os.path.join(BASE_DIR, "entradas")
IMAGENES_DIR = os.path.join(BASE_DIR, "imagenes")
SALIDAS_DIR = os.path.join(BASE_DIR, "salidas")

# Asegurar que existan directorios básicos
os.makedirs(PDFS_DIR, exist_ok=True)
os.makedirs(ENTRADAS_DIR, exist_ok=True)
os.makedirs(IMAGENES_DIR, exist_ok=True)
os.makedirs(os.path.join(IMAGENES_DIR, "manual"), exist_ok=True)
os.makedirs(SALIDAS_DIR, exist_ok=True)

# Servir estáticos (imágenes y archivos PDF de salida)
app.mount("/api/imagenes", StaticFiles(directory=IMAGENES_DIR), name="imagenes")
app.mount("/api/salidas", StaticFiles(directory=SALIDAS_DIR), name="salidas")


@app.get("/api/ping")
def ping():
    return {"status": "ok", "message": "Servidor COM.LED activo"}


def parse_existing_pdf(pdf_path: str):
    import fitz
    from PIL import Image
    
    # 1. Leer Metadatos
    doc_temp = fitz.open(pdf_path)
    meta_pdf = doc_temp.metadata
    doc_temp.close()
    
    metadata_json = meta_pdf.get("subject", "")
    has_metadata = False
    if metadata_json and metadata_json.startswith("{"):
        try:
            # Validar JSON
            json.loads(metadata_json)
            datos_path = os.path.join(ENTRADAS_DIR, "datos.json")
            with open(datos_path, "w", encoding="utf-8") as f:
                f.write(metadata_json)
            has_metadata = True
            print("Metadatos cargados con éxito del PDF.")
        except Exception as ex:
            print("Error parsing metadata JSON:", ex)
            pass
            
    if not has_metadata:
        print("No hay metadatos incrustados. Usando IA...")
        subprocess.run(["python3", "backend/extraer_datos.py"], check=True)
        
    # 2. Extraer imágenes embebidas
    doc = fitz.open(pdf_path)
    imagenes = []
    temp_folder = os.path.join(IMAGENES_DIR, "temp")
    os.makedirs(temp_folder, exist_ok=True)
    
    # Limpiar temp
    for filename in os.listdir(temp_folder):
        fp = os.path.join(temp_folder, filename)
        if os.path.isfile(fp):
            os.remove(fp)
            
    try:
        for i, img in enumerate(doc.get_page_images(0)):
            try:
                xref = img[0]
                smask = img[1]
                
                pix = fitz.Pixmap(doc, xref)
                if smask > 0:
                    mask = fitz.Pixmap(doc, smask)
                    pix_with_alpha = fitz.Pixmap(pix, mask)
                    pix = pix_with_alpha
                
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                    
                ruta_temp = os.path.join(temp_folder, f"c_{i}.png")
                pix.save(ruta_temp)
                pix = None
                
                im = Image.open(ruta_temp)
                area = im.width * im.height
                
                if 10000 < area < 3000000:
                    es_dibujo = False
                    if im.mode in ('RGBA', 'LA'):
                        alpha = im.split()[-1]
                        transparentes = sum(1 for p in alpha.getdata() if p < 25)
                        if (transparentes / area) > 0.60:
                            es_dibujo = True
                    else:
                        gris = im.convert("L")
                        hist = gris.histogram()
                        blancos = sum(hist[225:256])
                        if (blancos / area) > 0.80:
                            es_dibujo = True

                    imagenes.append({"ruta": ruta_temp, "area": area, "es_dibujo": es_dibujo})
            except Exception as e:
                pass
                
        # Separar candidatas
        productos = [img for img in imagenes if not img["es_dibujo"]]
        dibujos = [img for img in imagenes if img["es_dibujo"]]
        
        productos = sorted(productos, key=lambda x: x["area"], reverse=True)
        dibujos = sorted(dibujos, key=lambda x: x["area"], reverse=True)
        
        producto_copiado = False
        dimensiones_copiado = False
        
        if productos:
            shutil.copy(productos[0]["ruta"], os.path.join(IMAGENES_DIR, "producto.png"))
            shutil.copy(productos[0]["ruta"], os.path.join(IMAGENES_DIR, "producto_final.png"))
            producto_copiado = True
        if dibujos:
            shutil.copy(dibujos[0]["ruta"], os.path.join(IMAGENES_DIR, "dimensiones.png"))
            dimensiones_copiado = True
        elif len(productos) > 1:
            shutil.copy(productos[1]["ruta"], os.path.join(IMAGENES_DIR, "dimensiones.png"))
            dimensiones_copiado = True
            
        # Generar estado.json para reflejar el estado
        estado = {
            "producto_ok": producto_copiado,
            "dimensiones_ok": dimensiones_copiado
        }
        estado_path = os.path.join(ENTRADAS_DIR, "estado.json")
        with open(estado_path, "w") as f:
            json.dump(estado, f, indent=2)
            
    except Exception as e:
        print("Error al extraer imágenes del PDF viejo:", e)
    finally:
        doc.close()


@app.post("/api/upload")
async def upload_catalog(
    file: UploadFile = File(...),
    nombre_comled: Optional[str] = Form(None),
    codigo_comled: Optional[str] = Form(None),
    instalacion_manual: Optional[str] = Form(None)
):
    try:
        # 1. Limpiar PDFs anteriores para evitar interferencia
        for filename in os.listdir(PDFS_DIR):
            file_path = os.path.join(PDFS_DIR, filename)
            if os.path.isfile(file_path) and not filename.startswith("."):
                try:
                    os.remove(file_path)
                except Exception as de:
                    print(f"No se pudo eliminar PDF antiguo {filename}: {de}")

        # 2. Guardar el archivo subido
        file_ext = os.path.splitext(file.filename)[1]
        save_path = os.path.join(PDFS_DIR, f"catalogo_proveedor{file_ext}")
        
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Guardar la configuración manual
        config = {}
        if nombre_comled and nombre_comled.strip():
            config["nombre_comled"] = nombre_comled.strip()
        if codigo_comled and codigo_comled.strip():
            config["codigo_comled"] = codigo_comled.strip()
        if instalacion_manual and instalacion_manual.strip():
            config["instalacion_manual"] = instalacion_manual.strip()

        config_path = os.path.join(ENTRADAS_DIR, "config_proveedor.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as ce:
            print(f"No se pudo escribir config_proveedor.json: {ce}")

        # 4. Limpiar cualquier imagen manual antigua para una nueva luminaria
        manual_dir = os.path.join(IMAGENES_DIR, "manual")
        for f in os.listdir(manual_dir):
            fp = os.path.join(manual_dir, f)
            if os.path.isfile(fp) and not f.startswith("."):
                try:
                    os.remove(fp)
                except Exception as de:
                    print(f"No se pudo eliminar imagen manual antigua {f}: {de}")

        # 5. Limpiar imágenes de producto, cota y fotometría antiguas de la carpeta raíz
        imagenes_a_limpiar = [
            "producto.png", "producto_final.png", "producto_final_test.png",
            "dimensiones.png", "fotometria_generada.png", "curva_polar.png"
        ]
        for img_name in imagenes_a_limpiar:
            fp = os.path.join(IMAGENES_DIR, img_name)
            if os.path.exists(fp):
                try:
                    os.remove(fp)
                except Exception as de:
                    print(f"No se pudo eliminar {img_name}: {de}")
                    
        temp_dir = os.path.join(IMAGENES_DIR, "temp")
        if os.path.exists(temp_dir):
            for f in os.listdir(temp_dir):
                fp = os.path.join(temp_dir, f)
                if os.path.isfile(fp) and not f.startswith("."):
                    try:
                        os.remove(fp)
                    except Exception as de:
                        print(f"No se pudo eliminar archivo temp antiguo {f}: {de}")

        # También limpiar estado_img.json viejo y estado.json viejo
        estado_img_path = os.path.join(ENTRADAS_DIR, "estado_img.json")
        if os.path.exists(estado_img_path):
            try:
                os.remove(estado_img_path)
            except Exception as de:
                print(f"No se pudo eliminar estado_img.json: {de}")
            
        estado_path = os.path.join(ENTRADAS_DIR, "estado.json")
        if os.path.exists(estado_path):
            try:
                os.remove(estado_path)
            except Exception as de:
                print(f"No se pudo eliminar estado.json: {de}")

        return {
            "status": "success",
            "file": file.filename,
            "config": config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir catálogo: {str(e)}")


@app.post("/api/extract")
def run_extraction_pipeline(mode: str = "proveedor"):
    """
    Ejecuta el bloque de extracción para el modo seleccionado:
    - proveedor: extraer_datos_proveedor.py + extraer_imagenes_proveedor.py
    - estandar: extraer_datos.py + extraer_imagenes_pdf.py
    - modificar: parse_existing_pdf()
    """
    try:
        if mode == "proveedor":
            print("Modo Proveedor: Ejecutando extraer_datos_proveedor.py")
            subprocess.run(["python3", "backend/extraer_datos_proveedor.py"], check=True)
            print("Modo Proveedor: Ejecutando extraer_imagenes_proveedor.py")
            subprocess.run(["python3", "backend/extraer_imagenes_proveedor.py"], check=True)
            print("Modo Proveedor: Ejecutando validar_extraccion_proveedor.py")
            subprocess.run(["python3", "backend/validar_extraccion_proveedor.py"], check=True)
            
        elif mode == "estandar":
            print("Modo Estándar: Ejecutando extraer_datos.py")
            subprocess.run(["python3", "backend/extraer_datos.py"], check=True)
            print("Modo Estándar: Ejecutando extraer_imagenes_pdf.py")
            subprocess.run(["python3", "backend/extraer_imagenes_pdf.py"], check=True)
            
            # Generar estado.json para modo estándar
            estado = {
                "producto_ok": os.path.exists("imagenes/producto.png") or os.path.exists("imagenes/producto_final.png"),
                "dimensiones_ok": os.path.exists("imagenes/dimensiones.png")
            }
            estado_path = os.path.join(ENTRADAS_DIR, "estado.json")
            with open(estado_path, "w") as f:
                json.dump(estado, f, indent=2)
                
        elif mode == "modificar":
            # Buscar el archivo PDF subido
            uploaded_pdf = None
            for f in os.listdir(PDFS_DIR):
                if f.endswith(".pdf") and not f.startswith("."):
                    uploaded_pdf = os.path.join(PDFS_DIR, f)
                    break
            if not uploaded_pdf:
                raise HTTPException(status_code=400, detail="No se encontró ningún PDF para modificar.")
            
            print(f"Modo Modificar: Procesando PDF {uploaded_pdf}")
            parse_existing_pdf(uploaded_pdf)
            
        else:
            raise HTTPException(status_code=400, detail=f"Modo inválido: {mode}")

        # Leer resultados
        datos = {}
        estado = {}
        
        datos_path = os.path.join(ENTRADAS_DIR, "datos.json")
        if os.path.exists(datos_path):
            with open(datos_path, "r", encoding="utf-8") as f:
                datos = json.load(f)

        estado_path = os.path.join(ENTRADAS_DIR, "estado.json")
        if os.path.exists(estado_path):
            with open(estado_path, "r", encoding="utf-8") as f:
                estado = json.load(f)

        return {
            "status": "success",
            "datos": datos,
            "estado": estado
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error en script de extracción: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@app.get("/api/datos")
def get_extracted_data():
    """Obtiene los datos técnicos actuales (JSON)."""
    datos_path = os.path.join(ENTRADAS_DIR, "datos.json")
    if not os.path.exists(datos_path):
        return {}
    with open(datos_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/datos")
def update_extracted_data(datos: dict):
    """Guarda modificaciones manuales del usuario sobre los datos técnicos."""
    try:
        datos_path = os.path.join(ENTRADAS_DIR, "datos.json")
        with open(datos_path, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        return {"status": "success", "message": "Datos técnicos guardados correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar datos: {str(e)}")


@app.post("/api/upload-manual-image")
async def upload_manual_image(
    type: str,  # 'producto' o 'dimensiones'
    file: UploadFile = File(...)
):
    """
    Permite al usuario subir de forma manual una imagen de contingencia
    si el backend automático no detectó la luminaria o el plano de cotas.
    """
    if type not in ["producto", "dimensiones"]:
        raise HTTPException(status_code=400, detail="El tipo debe ser 'producto' o 'dimensiones'")

    try:
        manual_dir = os.path.join(IMAGENES_DIR, "manual")
        # Eliminar archivos viejos del mismo tipo
        for f in os.listdir(manual_dir):
            if f.startswith(type):
                try:
                    os.remove(os.path.join(manual_dir, f))
                except Exception as de:
                    print(f"No se pudo eliminar imagen manual antigua {f}: {de}")

        file_ext = os.path.splitext(file.filename)[1]
        import time
        timestamp = int(time.time())
        save_path = os.path.join(manual_dir, f"{type}_{timestamp}{file_ext}")
        
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Actualizar estado_img.json
        estado_img_path = os.path.join(ENTRADAS_DIR, "estado_img.json")
        estado_img = {}
        if os.path.exists(estado_img_path):
            try:
                with open(estado_img_path, "r") as f:
                    estado_img = json.load(f)
            except:
                pass
        
        estado_img[f"{type}_ok"] = True
        
        with open(estado_img_path, "w") as f:
            json.dump(estado_img, f, indent=2)

        # Ejecutar re-validación
        subprocess.run(["python3", "backend/validar_extraccion_proveedor.py"], check=True)

        return {"status": "success", "message": f"Imagen de {type} subida e integrada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir imagen manual: {str(e)}")


@app.post("/api/generate")
def run_generation_pipeline(mode: str = "proveedor"):
    """
    Ejecuta el bloque de generación final (Pasos 4 a 10) según el modo.
    Crea el PowerPoint y exporta a PDF.
    """
    try:
        if mode == "modificar":
            scripts = [
                "backend/generar_fotometria.py",
                "backend/main.py",
                "backend/exportar_pdf.py"
            ]
        else:
            scripts = [
                "backend/preparar_producto.py",
                "backend/mejorar_producto_ia.py",
                "backend/generar_fotometria.py",
                "backend/validar_imagenes.py",
                "backend/reporte_prueba.py",
                "backend/main.py",
                "backend/exportar_pdf.py"
            ]

        for script in scripts:
            print(f"Ejecutando: {script}")
            subprocess.run(["python3", script], check=True)

        # Buscar nombre del archivo PDF generado
        pdf_generado = ""
        for f in os.listdir(SALIDAS_DIR):
            if f.endswith(".pdf") and f.startswith("ET CL-"):
                pdf_generado = f
                break

        return {
            "status": "success",
            "message": "Ficha generada exitosamente",
            "pdf_name": pdf_generado,
            "pdf_url": f"/api/salidas/{pdf_generado}" if pdf_generado else None
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error en script de generación: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado al generar: {str(e)}")


@app.post("/api/open-folder")
def open_output_folder():
    """Abre la carpeta de salidas en el explorador de archivos nativo."""
    try:
        sistema = platform.system()
        if sistema == "Windows":
            os.startfile(SALIDAS_DIR)
        elif sistema == "Darwin":  # macOS
            subprocess.run(["open", SALIDAS_DIR])
        else:  # Linux
            subprocess.run(["xdg-open", SALIDAS_DIR])
        return {"status": "success", "message": "Carpeta de salidas abierta"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo abrir la carpeta: {str(e)}")


app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "frontend"), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
