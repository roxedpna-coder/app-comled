import json
import os
import subprocess
import shutil
import glob

print("=======================================")
print("🔧 INICIANDO: EDITOR DE FICHAS COM.LED")
print("=======================================\n")

# 1. Cargar PDF
print("Arrastra aquí el archivo PDF de la ficha COM.LED que deseas modificar.")
print("(O pulsa Enter si quieres editar la ÚLTIMA ficha generada que ya está en memoria)")
ruta_pdf = input("Ruta del PDF: ").strip().replace("'", "").replace('"', "")

if ruta_pdf:
    if not os.path.exists(ruta_pdf):
        print("❌ ERROR: No se encontró el archivo en la ruta especificada.")
        exit()
    
    nombre_archivo = os.path.basename(ruta_pdf)
    destino_pdf = os.path.join("pdfs", nombre_archivo)
    shutil.copy(ruta_pdf, destino_pdf)
    os.utime(destino_pdf, None)
    
    print("\n1/3 Leyendo PDF para extraer datos técnicos...")
    import fitz
    doc_temp = fitz.open(destino_pdf)
    meta_pdf = doc_temp.metadata
    doc_temp.close()
    
    metadata_json = meta_pdf.get("subject", "")
    if metadata_json and metadata_json.startswith("{"):
        print("✅ Metadatos exactos detectados en el PDF. Cargando configuración original sin usar IA...")
        with open("entradas/datos.json", "w", encoding="utf-8") as f:
            f.write(metadata_json)
    else:
        print("⚠️ No hay metadatos incrustados (PDF muy antiguo). Usando IA para leer textos...")
        subprocess.run(["python3", "backend/extraer_datos.py"], check=True)
    
    print("2/3 Recuperando imágenes incrustadas del PDF viejo...")
    import fitz
    from PIL import Image
    
    doc = fitz.open(destino_pdf)
    imagenes = []
    temp_folder = "imagenes/temp"
    os.makedirs(temp_folder, exist_ok=True)
    
    try:
        for i, img in enumerate(doc.get_page_images(0)):
            try:
                xref = img[0]
                smask = img[1]
                
                pix = fitz.Pixmap(doc, xref)
                # Si tiene máscara de transparencia (smask) la aplicamos
                if smask > 0:
                    mask = fitz.Pixmap(doc, smask)
                    pix_with_alpha = fitz.Pixmap(pix, mask)
                    pix = pix_with_alpha
                
                # Convertir CMYK a RGB si es necesario
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                    
                ruta_temp = f"{temp_folder}/c_{i}.png"
                pix.save(ruta_temp)
                pix = None
                
                im = Image.open(ruta_temp)
                area = im.width * im.height
                
                if 10000 < area < 3000000:
                    # Calcular qué porcentaje de la imagen es "vacío" (transparente o blanco puro)
                    es_dibujo = False
                    if im.mode in ('RGBA', 'LA'):
                        alpha = im.split()[-1]
                        # Pixeles transparentes (alpha < 25)
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
        
        if productos:
            shutil.copy(productos[0]["ruta"], "imagenes/producto.png")
            shutil.copy(productos[0]["ruta"], "imagenes/producto_final.png")
        if dibujos:
            shutil.copy(dibujos[0]["ruta"], "imagenes/dimensiones.png")
        elif len(productos) > 1:
            # Si no encontró dibujos, usa la segunda más grande como fallback
            shutil.copy(productos[1]["ruta"], "imagenes/dimensiones.png")
    except Exception as e:
        print("Nota: No se pudieron extraer las imágenes automáticamente.")
    finally:
        doc.close()
    
    print("3/3 Archivo parseado. Listo para modificar.\n")


datos_path = "entradas/datos.json"

if not os.path.exists(datos_path):
    print("❌ ERROR: No hay datos cargados.")
    exit()

with open(datos_path, "r", encoding="utf-8") as f:
    datos = json.load(f)

while True:
    print("\n¿Qué deseas modificar de la ficha?")
    print("1. Un dato de texto (Potencia, Flujo, IP, Nombre, etc.)")
    print("2. La imagen del Producto")
    print("3. La imagen de Dimensiones")
    print("4. Nada, ir directamente a regenerar PDF")
    print("5. Cancelar y salir")

    opcion = input("\nElige una opción (1-5): ")

    if opcion == "1":
        print("\n--- DATOS ACTUALES ---")
        claves_texto = [k for k in datos.keys() if not k.startswith("img_")]
        
        for i, clave in enumerate(claves_texto):
            print(f"{i + 1}. {clave}: {datos[clave]}")
            
        seleccion = input(f"\nIngresa el número del dato que quieres modificar (1-{len(claves_texto)}): ")
        
        try:
            idx = int(seleccion) - 1
            if 0 <= idx < len(claves_texto):
                clave_elegida = claves_texto[idx]
                nuevo_valor = input(f"\nIntroduce el nuevo valor para '{clave_elegida}': ")
                
                datos[clave_elegida] = nuevo_valor
                
                # --- LÓGICA DE RECALCULO AUTOMÁTICO ---
                import re
                def extract_number(text):
                    matches = re.findall(r"[\d\.]+", str(text).replace(',', '.'))
                    return float(matches[0]) if matches else None

                if clave_elegida in ["potencia", "eficacia_luminosa", "flujo_luminoso"]:
                    pot = extract_number(datos.get("potencia", ""))
                    efi = extract_number(datos.get("eficacia_luminosa", ""))
                    flu = extract_number(datos.get("flujo_luminoso", ""))
                    
                    if clave_elegida == "potencia" and pot and efi:
                        nuevo_flu = int(pot * efi)
                        datos["flujo_luminoso"] = f"{nuevo_flu} lm"
                        datos["flujo_resumido"] = f"{nuevo_flu} lm"
                        print(f"🔄 Recalculado: Flujo Luminoso -> {nuevo_flu} lm")
                    elif clave_elegida == "eficacia_luminosa" and pot and efi:
                        nuevo_flu = int(pot * efi)
                        datos["flujo_luminoso"] = f"{nuevo_flu} lm"
                        datos["flujo_resumido"] = f"{nuevo_flu} lm"
                        print(f"🔄 Recalculado: Flujo Luminoso -> {nuevo_flu} lm")
                    elif clave_elegida == "flujo_luminoso" and flu and pot and pot > 0:
                        nuevo_efi = int(flu / pot)
                        datos["eficacia_luminosa"] = f"{nuevo_efi} lm/W"
                        datos["eficacia_resumido"] = f"{nuevo_efi} lm/W"
                        print(f"🔄 Recalculado: Eficacia Luminosa -> {nuevo_efi} lm/W")
                # --------------------------------------
                
                with open(datos_path, "w", encoding="utf-8") as f:
                    json.dump(datos, f, indent=2, ensure_ascii=False)
                    
                print(f"✅ Dato guardado correctamente.")
            else:
                print("❌ Número fuera de rango.")
                continue
        except ValueError:
            print("❌ Selección inválida.")
            continue

    elif opcion == "2":
        print("\n--- MODIFICAR IMAGEN DEL PRODUCTO ---")
        print("1. Borra cualquier imagen antigua en 'imagenes/manual/'.")
        print("2. Coloca tu nueva imagen dentro de 'imagenes/manual/' (asegúrate de que el nombre del archivo contenga la palabra 'producto').")
        
        confirmacion = input("\n¿Has colocado ya la imagen? (s/n): ").lower()
        if confirmacion == 's':
            print("\nProcesando nueva imagen del producto...")
            subprocess.run(["python3", "backend/preparar_producto.py"], check=True)
            print("✅ Imagen de producto actualizada.")
        else:
            print("Operación cancelada.")
            continue

    elif opcion == "3":
        print("\n--- MODIFICAR IMAGEN DE DIMENSIONES ---")
        print("1. Borra cualquier imagen antigua en 'imagenes/manual/'.")
        print("2. Coloca tu nueva imagen de esquema dentro de 'imagenes/manual/' (asegúrate de que el nombre del archivo contenga la palabra 'dimensiones').")
        
        confirmacion = input("\n¿Has colocado ya la imagen? (s/n): ").lower()
        if confirmacion == 's':
            manuales = glob.glob("imagenes/manual/dimensiones.*") + glob.glob("imagenes/manual/*dimensiones*.*")
            if manuales:
                shutil.copy(manuales[0], "imagenes/dimensiones.png")
                print(f"✅ Nueva imagen de dimensiones copiada: {manuales[0]}")
            else:
                print("❌ No se encontró la imagen en la carpeta manual.")
                continue
        else:
            print("Operación cancelada.")
            continue

    elif opcion == "4":
        break

    elif opcion == "5":
        print("Operación cancelada. Saliendo sin regenerar el PDF.")
        exit()

    else:
        print("❌ Opción no válida.")
        continue
        
    otra = input("\n¿Deseas realizar OTRA modificación a esta misma ficha antes de terminar? (s/n): ").lower()
    if otra != 's':
        break

print("\n--- REGENERANDO PDF ---")

print("1/3 Generando curva fotométrica y ópticas...")
subprocess.run(["python3", "backend/generar_fotometria.py"], check=True)

print("2/3 Actualizando plantilla PowerPoint...")
subprocess.run(["python3", "backend/main.py"], check=True)

print("3/3 Exportando a PDF final...")
subprocess.run(["python3", "backend/exportar_pdf.py"], check=True)

print("\n=======================================")
print("✅ FICHA MODIFICADA EXITOSAMENTE")
print("=======================================")
