import fitz
doc = fitz.open("pdfs/TUB 4.pdf")
for num_pagina, pagina in enumerate(doc):
    drawings = pagina.get_drawings()
    if drawings:
        rect = fitz.Rect()
        for d in drawings:
            rect |= d["rect"]
        print(f"Página {num_pagina}: Dibujos vectoriales encontrados. Bounding box total: {rect}")
        
        # Renderizar solo ese pedazo
        pix = pagina.get_pixmap(matrix=fitz.Matrix(4, 4), clip=rect)
        pix.save(f"imagenes/debug/drawings_p{num_pagina}.png")
