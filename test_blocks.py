import fitz
doc = fitz.open("pdfs/TUB 4.pdf")
keywords_dim = ["DIMENSIONES", "DIMENSIONS", "SIZE", "MEDIDAS", "DRAWING", "UNIT: MM", "DIMENSION", "INSTALLATION"]
for num_pagina, pagina_doc in enumerate(doc):
    for bloque in pagina_doc.get_text("blocks"):
        x0, y0, x1, y1, texto, *_ = bloque
        texto_mayus = texto.upper()
        if any(kw in texto_mayus for kw in keywords_dim):
            print(f"Página {num_pagina}: Encontrado '{texto.strip()}' en x0={x0:.1f}, y0={y0:.1f}")
