// Configuración de API URL
const API_BASE = "http://127.0.0.1:8000/api";

// Variables de Estado
let selectedFile = null;
let extractedData = {};
let extractionStatus = {};
let currentMode = "proveedor"; // "proveedor", "estandar" o "modificar"

// Elementos de los Tabs de Modo
const tabs = {
    proveedor: document.getElementById("tabProveedor"),
    estandar: document.getElementById("tabEstandar"),
    modificar: document.getElementById("tabModificar")
};

const uploadTitle = document.getElementById("uploadTitle");
const uploadSubtitle = document.getElementById("uploadSubtitle");
const paramsContainer = document.querySelector("#uploadSection .grid");

function setMode(mode) {
    currentMode = mode;
    
    // Cambiar clases de los botones de pestaña
    Object.keys(tabs).forEach(key => {
        const btn = tabs[key];
        if (key === mode) {
            btn.className = "flex-1 py-2.5 text-xs md:text-sm font-semibold rounded-lg transition-all bg-white dark:bg-slate-800 shadow-md text-brand-600 dark:text-brand-400";
        } else {
            btn.className = "flex-1 py-2.5 text-xs md:text-sm font-semibold rounded-lg transition-all text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100";
        }
    });

    // Cambiar textos explicativos
    if (mode === "proveedor") {
        uploadTitle.innerText = "Crear Ficha Técnica desde Proveedor";
        uploadSubtitle.innerText = "Sube un catálogo PDF o una captura de pantalla del producto y extrae la información técnica de forma local.";
        paramsContainer.classList.remove("hidden");
    } else if (mode === "estandar") {
        uploadTitle.innerText = "Crear Ficha Técnica Estándar COM.LED";
        uploadSubtitle.innerText = "Sube el PDF original del producto para extraer datos e imágenes y compilar una ficha técnica oficial.";
        paramsContainer.classList.remove("hidden");
    } else if (mode === "modificar") {
        uploadTitle.innerText = "Modificar Ficha COM.LED Existente";
        uploadSubtitle.innerText = "Sube un PDF de ficha COM.LED generado anteriormente para recuperar sus datos e imágenes y modificarlos directamente.";
        paramsContainer.classList.add("hidden"); // Ocultar parámetros extra para modificar ya que vienen del PDF
    }
}

tabs.proveedor.addEventListener("click", () => setMode("proveedor"));
tabs.estandar.addEventListener("click", () => setMode("estandar"));
tabs.modificar.addEventListener("click", () => setMode("modificar"));

// Inicialización del Tema (Claro/Oscuro)
const htmlEl = document.documentElement;
const themeToggle = document.getElementById("themeToggle");

const savedTheme = localStorage.getItem("theme") || "dark";
if (savedTheme === "dark") {
    htmlEl.classList.add("dark");
} else {
    htmlEl.classList.remove("dark");
}

themeToggle.addEventListener("click", () => {
    if (htmlEl.classList.contains("dark")) {
        htmlEl.classList.remove("dark");
        localStorage.setItem("theme", "light");
    } else {
        htmlEl.classList.add("dark");
        localStorage.setItem("theme", "dark");
    }
});

// Elementos de Navegación de Secciones
const sections = {
    upload: document.getElementById("uploadSection"),
    progress: document.getElementById("progressSection"),
    validation: document.getElementById("validationSection"),
    success: document.getElementById("successSection")
};

function showSection(name) {
    Object.keys(sections).forEach(key => {
        if (key === name) {
            sections[key].classList.remove("hidden");
        } else {
            sections[key].classList.add("hidden");
        }
    });
}

// ==========================================
// 1. CARGA DE ARCHIVOS Y DROPZONE
// ==========================================
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const fileNameDisplay = document.getElementById("fileNameDisplay");
const btnExtract = document.getElementById("btnExtract");

dropzone.addEventListener("click", () => fileInput.click());

dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("border-brand-500", "bg-brand-500/5");
});

dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("border-brand-500", "bg-brand-500/5");
});

dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("border-brand-500", "bg-brand-500/5");
    if (e.dataTransfer.files.length > 0) {
        handleFileSelection(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
        handleFileSelection(fileInput.files[0]);
    }
});

function handleFileSelection(file) {
    selectedFile = file;
    fileNameDisplay.innerHTML = `<span class="text-brand-600 dark:text-brand-400 font-bold">${file.name}</span>`;
    dropzone.classList.add("border-brand-500/50", "bg-brand-500/5");
}

// Iniciar Extracción
btnExtract.addEventListener("click", async () => {
    if (!selectedFile) {
        alert("Por favor, selecciona o arrastra un archivo primero.");
        return;
    }

    const nombre = document.getElementById("nombreInput").value;
    const codigo = document.getElementById("codigoInput").value;
    const instalacion = document.getElementById("instalacionInput").value;

    const formData = new FormData();
    formData.append("file", selectedFile);
    if (nombre) formData.append("nombre_comled", nombre);
    if (codigo) formData.append("codigo_comled", codigo);
    if (instalacion) formData.append("instalacion_manual", instalacion);

    try {
        btnExtract.disabled = true;
        btnExtract.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Subiendo archivo...';

        // 1. Subir archivo a la API
        const uploadRes = await fetch(`${API_BASE}/upload`, {
            method: "POST",
            body: formData
        });

        if (!uploadRes.ok) {
            throw new Error("Fallo al subir el archivo.");
        }

        // Configurar los pasos del stepper según el modo
        const step1Text = document.getElementById("step1").querySelector("div:last-child");
        const step2Text = document.getElementById("step2").querySelector("div:last-child");
        const step3Text = document.getElementById("step3").querySelector("div:last-child");

        if (currentMode === "proveedor") {
            step1Text.innerText = "Extrayendo datos técnicos con OpenAI Vision...";
            step2Text.innerText = "Buscando imágenes de la luminaria y cotas...";
            step3Text.innerText = "Validando integridad y calidad de la extracción...";
        } else if (currentMode === "estandar") {
            step1Text.innerText = "Leyendo PDF del catálogo original...";
            step2Text.innerText = "Extrayendo imágenes embebidas automáticamente...";
            step3Text.innerText = "Extrayendo y mapeando datos técnicos con IA...";
        } else if (currentMode === "modificar") {
            step1Text.innerText = "Cargando metadatos estructurados del PDF...";
            step2Text.innerText = "Recuperando imágenes incrustadas antiguas...";
            step3Text.innerText = "Inicializando tabla para modificaciones...";
        }

        // 2. Cambiar a pantalla de progreso
        showSection("progress");
        updateProgress(10, "Ejecutando extracción técnica...");
        resetSteps();

        // Paso 1 visual activo
        setStepActive("step1");

        // 3. Lanzar pipeline de extracción en el backend
        updateProgress(35, "Extrayendo datos técnicos...");
        setStepDone("step1");
        setStepActive("step2");

        const extractRes = await fetch(`${API_BASE}/extract?mode=${currentMode}`, {
            method: "POST"
        });

        if (!extractRes.ok) {
            const errData = await extractRes.json();
            throw new Error(errData.detail || "Error durante la extracción de datos.");
        }

        const data = await extractRes.json();
        extractedData = data.datos;
        extractionStatus = data.estado;

        setStepDone("step2");
        setStepActive("step3");
        updateProgress(80, "Validando datos e imágenes...");

        // Finalizar barra de carga
        updateProgress(100, "Completado");
        setStepDone("step3");

        // Esperar un breve instante para mostrar finalización
        setTimeout(() => {
            loadValidationPanel();
            showSection("validation");
            // Reactivar botón de carga por si vuelve
            btnExtract.disabled = false;
            btnExtract.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Iniciar Extracción Inteligente';
        }, 800);

    } catch (error) {
        alert(`Error: ${error.message}`);
        showSection("upload");
        btnExtract.disabled = false;
        btnExtract.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Iniciar Extracción Inteligente';
    }
});

// ==========================================
// CONTROL DEL STEPPER DE PROGRESO
// ==========================================
const currentStepName = document.getElementById("currentStepName");
const progressPercent = document.getElementById("progressPercent");
const progressBar = document.getElementById("progressBar");

function updateProgress(percent, statusText) {
    progressBar.style.width = `${percent}%`;
    progressPercent.innerText = `${percent}%`;
    currentStepName.innerText = statusText;
}

function resetSteps() {
    document.querySelectorAll(".step-item").forEach(el => {
        el.className = "step-item flex items-start gap-4 text-slate-400";
        el.querySelector(".step-icon").className = "step-icon w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 flex items-center justify-center text-xs font-bold shrink-0";
        el.querySelector(".step-icon").innerHTML = el.id.replace("step", "");
    });
}

function setStepActive(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = "step-item flex items-start gap-4 text-brand-600 dark:text-brand-400";
    el.querySelector(".step-icon").className = "step-icon w-6 h-6 rounded-full bg-brand-500/10 border border-brand-500 flex items-center justify-center text-xs font-bold shrink-0 glow-effect";
    el.querySelector(".step-icon").innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i>';
}

function setStepDone(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = "step-item flex items-start gap-4 text-emerald-600 dark:text-emerald-400";
    el.querySelector(".step-icon").className = "step-icon w-6 h-6 rounded-full bg-emerald-500/10 border border-emerald-500 flex items-center justify-center text-xs font-bold shrink-0";
    el.querySelector(".step-icon").innerHTML = '<i class="fa-solid fa-check"></i>';
}

// ==========================================
// 2. PANEL DE VALIDACIÓN Y EDICIÓN
// ==========================================
const dataFormContainer = document.getElementById("dataFormContainer");
const missingImagesAlert = document.getElementById("missingImagesAlert");
const missingImagesText = document.getElementById("missingImagesText");

// Nombres legibles en español de los campos técnicos
const fieldLabels = {
    nombre_luminaria: "Nombre de Luminaria",
    codigo_comled: "Código COM.LED",
    tipo_instalacion: "Tipo Instalación",
    potencia: "Potencia (W)",
    flujo_luminoso: "Flujo Luminoso (Lm)",
    temperatura_color: "Temp. Color (CCT)",
    indice_reproduccion_cromatica: "Índice IRC (CRI)",
    angulo_apertura: "Ángulo Óptica",
    estanqueidad_ip: "Protección (IP)",
    resistencia_ik: "Resistencia (IK)",
    driver: "Marca/Tipo Driver",
    eficiencia: "Eficiencia (Lm/W)",
    material: "Material Cuerpo",
    acabado: "Acabado/Color",
    garantia: "Garantía (Años)",
    regulacion: "Regulación (Dimmable)",
    diametro_corte: "Corte / Empotramiento"
};

function loadValidationPanel() {
    // 1. Limpiar contenedor
    dataFormContainer.innerHTML = "";

    // 2. Cargar campos editables
    Object.keys(fieldLabels).forEach(key => {
        const value = extractedData[key] || "";
        const div = document.createElement("div");
        div.className = "space-y-1";
        div.innerHTML = `
            <label class="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">${fieldLabels[key]}</label>
            <input type="text" data-key="${key}" value="${value}" class="tech-field-input w-full bg-slate-100/50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500 transition-colors">
        `;
        dataFormContainer.appendChild(div);
    });

    // 3. Escuchar cambios para actualizar los datos en memoria
    document.querySelectorAll(".tech-field-input").forEach(input => {
        input.addEventListener("input", (e) => {
            const key = e.target.getAttribute("data-key");
            extractedData[key] = e.target.value;
        });
    });

    // 4. Actualizar estado de imágenes
    updateImagesPanel();
}

function updateImagesPanel() {
    const cacheBuster = Date.now();
    
    // Imagen Producto
    const imgProductPreview = document.getElementById("imgProductoPreview");
    const badgeProducto = document.getElementById("badgeProducto");
    
    if (extractionStatus.producto_ok) {
        imgProductPreview.src = `${API_BASE}/imagenes/producto_final.png?t=${cacheBuster}`;
        badgeProducto.className = "flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20";
        badgeProducto.innerHTML = '<i class="fa-solid fa-circle-check"></i> Detectada';
    } else {
        imgProductPreview.src = ""; // Vacío
        badgeProducto.className = "flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20";
        badgeProducto.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> No Detectada';
    }

    // Imagen Dimensiones
    const imgDimensionesPreview = document.getElementById("imgDimensionesPreview");
    const badgeDimensiones = document.getElementById("badgeDimensiones");

    if (extractionStatus.dimensiones_ok) {
        imgDimensionesPreview.src = `${API_BASE}/imagenes/dimensiones.png?t=${cacheBuster}`;
        badgeDimensiones.className = "flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20";
        badgeDimensiones.innerHTML = '<i class="fa-solid fa-circle-check"></i> Detectada';
    } else {
        imgDimensionesPreview.src = "";
        badgeDimensiones.className = "flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20";
        badgeDimensiones.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> No Detectada';
    }

    // Alerta de Imágenes Faltantes
    if (!extractionStatus.producto_ok || !extractionStatus.dimensiones_ok) {
        missingImagesAlert.classList.remove("hidden");
        let txt = "No se ha podido detectar automáticamente la ";
        if (!extractionStatus.producto_ok && !extractionStatus.dimensiones_ok) {
            txt += "foto de la luminaria ni el plano de dimensiones. Por favor, cárgalos manualmente a la derecha.";
        } else if (!extractionStatus.producto_ok) {
            txt += "foto de la luminaria. Por favor, cárgala manualmente a la derecha.";
        } else {
            txt += "cota de dimensiones. Por favor, cárgala manualmente a la derecha.";
        }
        missingImagesText.innerText = txt;
    } else {
        missingImagesAlert.classList.add("hidden");
    }
}

// Manejar re-subida manual de imagen
const fileProductUpload = document.getElementById("fileProductUpload");
const fileDimensionsUpload = document.getElementById("fileDimensionsUpload");

fileProductUpload.addEventListener("change", () => {
    if (fileProductUpload.files.length > 0) {
        uploadManualImage("producto", fileProductUpload.files[0]);
    }
});

fileDimensionsUpload.addEventListener("change", () => {
    if (fileDimensionsUpload.files.length > 0) {
        uploadManualImage("dimensiones", fileDimensionsUpload.files[0]);
    }
});

async function uploadManualImage(type, file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch(`${API_BASE}/upload-manual-image?type=${type}`, {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            throw new Error("No se pudo cargar la imagen manual.");
        }

        const resData = await res.json();
        
        // Actualizar el estado de validación local
        extractionStatus[`${type}_ok`] = true;
        
        // Recargar el panel visualizador
        updateImagesPanel();
        
    } catch (e) {
        alert(`Error al subir imagen de contingencia: ${e.message}`);
    }
}

// Botón de Volver a Carga
document.getElementById("btnBackToUpload").addEventListener("click", () => {
    showSection("upload");
});

// ==========================================
// 3. GENERACIÓN FINAL DEL POWERPOINT
// ==========================================
const btnCompile = document.getElementById("btnCompile");

btnCompile.addEventListener("click", async () => {
    // 1. Guardar primero cualquier cambio en la tabla técnica del backend
    try {
        btnCompile.disabled = true;
        btnCompile.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Guardando datos...';

        const saveRes = await fetch(`${API_BASE}/datos`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(extractedData)
        });

        if (!saveRes.ok) throw new Error("No se pudieron guardar las modificaciones técnicas.");

        // 2. Cambiar a pantalla de carga (stepper de compilación)
        showSection("progress");
        updateProgress(5, "Compilando PowerPoint...");
        resetSteps();
        
        // Cambiar títulos de stepper para la fase de compilación
        const step1Text = document.getElementById("step1").querySelector("div:last-child");
        const step2Text = document.getElementById("step2").querySelector("div:last-child");
        const step3Text = document.getElementById("step3").querySelector("div:last-child");

        if (currentMode === "modificar") {
            step1Text.innerText = "Actualizando fotometría y ópticas...";
            step2Text.innerText = "Actualizando plantilla PowerPoint con nuevos valores...";
            step3Text.innerText = "Exportando PDF modificado final...";
        } else {
            step1Text.innerText = "Limpiando fondo del producto y mejorando resolución...";
            step2Text.innerText = "Generando gráficos de fotometría...";
            step3Text.innerText = "Compilando plantilla PowerPoint y exportando a PDF...";
        }

        // Ejecutar compilación
        setStepActive("step1");
        updateProgress(20, "Compilando ficha técnica...");
        
        // Llamar API de compilación (corre los pasos 4 a 10)
        const compileRes = await fetch(`${API_BASE}/generate?mode=${currentMode}`, {
            method: "POST"
        });

        if (!compileRes.ok) {
            const errData = await compileRes.json();
            throw new Error(errData.detail || "Error al compilar la ficha.");
        }

        const buildData = await compileRes.json();

        setStepDone("step1");
        setStepDone("step2");
        setStepDone("step3");
        updateProgress(100, "Ficha generada");

        // 3. Mostrar pantalla de éxito
        setTimeout(() => {
            showSection("success");
            
            // Configurar botones de descarga y apertura
            const btnDownloadPdf = document.getElementById("btnDownloadPdf");
            btnDownloadPdf.href = `http://127.0.0.1:8000${buildData.pdf_url}`;
            
            btnCompile.disabled = false;
            btnCompile.innerHTML = '<i class="fa-solid fa-file-powerpoint"></i> Generar Ficha Técnica';
        }, 800);

    } catch (e) {
        alert(`Error al compilar PowerPoint: ${e.message}`);
        showSection("validation");
        btnCompile.disabled = false;
        btnCompile.innerHTML = '<i class="fa-solid fa-file-powerpoint"></i> Generar Ficha Técnica';
    }
});

// ==========================================
// 4. ACCIONES FINALES Y APERTURA DE CARPETA
// ==========================================
const btnOpenFolder = document.getElementById("btnOpenFolder");
const btnRestart = document.getElementById("btnRestart");

btnOpenFolder.addEventListener("click", async () => {
    try {
        const res = await fetch(`${API_BASE}/open-folder`, { method: "POST" });
        if (!res.ok) throw new Error("No se pudo abrir la carpeta.");
    } catch (e) {
        alert(e.message);
    }
});

btnRestart.addEventListener("click", () => {
    // Reiniciar inputs y archivos
    selectedFile = null;
    fileInput.value = "";
    document.getElementById("nombreInput").value = "";
    document.getElementById("codigoInput").value = "";
    document.getElementById("instalacionInput").value = "";
    fileNameDisplay.innerHTML = "Arrastra y suelta tu archivo aquí";
    dropzone.className = "border-2 border-dashed border-slate-300 dark:border-slate-800 hover:border-brand-500 dark:hover:border-brand-500 rounded-xl p-10 flex flex-col items-center justify-center gap-4 cursor-pointer transition-all bg-slate-100/20 dark:bg-slate-900/10 group";

    showSection("upload");
});
