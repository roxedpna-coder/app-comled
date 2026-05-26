/**
 * COM.LED Datasheet Engine
 * Frontend Application Controller
 */

const API_BASE = window.location.origin + "/api";

// ==========================================
// 1. CONTROL DE ESTADO GLOBAL (AppState)
// ==========================================
const AppState = {
    mode: "proveedor", // "proveedor" | "estandar" | "modificar"
    file: null,
    data: {},
    status: {
        producto_ok: false,
        dimensiones_ok: false,
        producto_url: "",
        dimensiones_url: ""
    },
    isProcessing: false
};

// Mapeo de Nombres de Sección con IDs de elementos HTML
const SECTIONS = {
    upload: "uploadSection",
    progress: "progressSection",
    validation: "validationSection",
    success: "successSection"
};

// ==========================================
// 2. SISTEMA DE TOASTS / NOTIFICACIONES
// ==========================================
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl border text-sm font-semibold shadow-lg transform translate-y-2 opacity-0 transition-all duration-300 max-w-sm`;
    
    let bg, border, text, icon;
    if (type === "success") {
        bg = "bg-emerald-500/10";
        border = "border-emerald-500/20";
        text = "text-emerald-700 dark:text-emerald-400";
        icon = "fa-solid fa-circle-check";
    } else if (type === "error") {
        bg = "bg-rose-500/10";
        border = "border-rose-500/20";
        text = "text-rose-700 dark:text-rose-400";
        icon = "fa-solid fa-triangle-exclamation";
    } else {
        bg = "bg-brand-500/10";
        border = "border-brand-500/20";
        text = "text-brand-700 dark:text-brand-400";
        icon = "fa-solid fa-circle-info";
    }

    toast.className += ` ${bg} ${border} ${text}`;
    toast.innerHTML = `<i class="${icon} text-base shrink-0"></i> <span>${message}</span>`;

    container.appendChild(toast);

    // Animación de entrada
    setTimeout(() => {
        toast.classList.remove("translate-y-2", "opacity-0");
    }, 10);

    // Auto-destrucción
    setTimeout(() => {
        toast.classList.add("translate-y-2", "opacity-0");
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}

// ==========================================
// 3. ENRUTADOR INTERNO / GESTIÓN DE VISTAS
// ==========================================
function navigateToSection(sectionName) {
    Object.keys(SECTIONS).forEach(key => {
        const el = document.getElementById(SECTIONS[key]);
        if (!el) return;
        if (key === sectionName) {
            el.classList.remove("hidden");
            el.style.opacity = "0";
            setTimeout(() => {
                el.style.opacity = "1";
            }, 50);
        } else {
            el.classList.add("hidden");
        }
    });
}

// Cambiar el Modo de Operación
function setMode(mode) {
    AppState.mode = mode;
    AppState.file = null;
    
    // Reiniciar inputs de subida
    const fileInput = document.getElementById("fileInput");
    if (fileInput) fileInput.value = "";
    
    const nombreInput = document.getElementById("nombreInput");
    if (nombreInput) nombreInput.value = "";
    
    const codigoInput = document.getElementById("codigoInput");
    if (codigoInput) codigoInput.value = "";
    
    const instalacionInput = document.getElementById("instalacionInput");
    if (instalacionInput) instalacionInput.value = "";

    const fileNameDisplay = document.getElementById("fileNameDisplay");
    if (fileNameDisplay) fileNameDisplay.innerText = "Arrastra y suelta tu archivo aquí";
    
    const dropzone = document.getElementById("dropzone");
    if (dropzone) {
        dropzone.className = "border-2 border-dashed border-slate-300 dark:border-slate-800 hover:border-brand-500 dark:hover:border-brand-500 rounded-2xl p-12 flex flex-col items-center justify-center gap-4 cursor-pointer transition-all bg-slate-100/10 dark:bg-slate-900/5 group relative overflow-hidden";
    }

    // Actualizar Clases de Pestañas
    const tabs = {
        proveedor: document.getElementById("tabProveedor"),
        estandar: document.getElementById("tabEstandar"),
        modificar: document.getElementById("tabModificar")
    };

    Object.keys(tabs).forEach(key => {
        const btn = tabs[key];
        if (!btn) return;
        if (key === mode) {
            btn.className = "flex-1 py-3 text-xs md:text-sm font-bold rounded-xl transition-all bg-white dark:bg-slate-800 shadow-sm text-brand-600 dark:text-brand-400";
        } else {
            btn.className = "flex-1 py-3 text-xs md:text-sm font-bold rounded-xl transition-all text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200";
        }
    });

    // Actualizar Textos e Inputs Opcionales
    const uploadTitle = document.getElementById("uploadTitle");
    const uploadSubtitle = document.getElementById("uploadSubtitle");
    const paramsGrid = document.querySelector("#uploadSection .grid");

    if (mode === "proveedor") {
        if (uploadTitle) uploadTitle.innerText = "Crear Ficha Técnica desde Proveedor";
        if (uploadSubtitle) uploadSubtitle.innerText = "Sube un catálogo PDF o una captura de pantalla del producto y extrae la información técnica de forma local.";
        if (paramsGrid) paramsGrid.classList.remove("hidden");
    } else if (mode === "estandar") {
        if (uploadTitle) uploadTitle.innerText = "Crear Ficha Técnica Estándar COM.LED";
        if (uploadSubtitle) uploadSubtitle.innerText = "Sube el PDF original del producto para extraer datos e imágenes y compilar una ficha técnica oficial.";
        if (paramsGrid) paramsGrid.classList.remove("hidden");
    } else if (mode === "modificar") {
        if (uploadTitle) uploadTitle.innerText = "Modificar Ficha COM.LED Existente";
        if (uploadSubtitle) uploadSubtitle.innerText = "Sube un PDF de ficha COM.LED generado anteriormente para recuperar sus datos e imágenes y modificarlos directamente.";
        if (paramsGrid) paramsGrid.classList.add("hidden"); // Se ocultan parámetros manuales en este modo
    }

    navigateToSection("upload");
}

// ==========================================
// 4. CONTROL DEL TEMA (CLARO / OSCURO)
// ==========================================
function initTheme() {
    const htmlEl = document.documentElement;
    const themeToggle = document.getElementById("themeToggle");
    if (!themeToggle) return;

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
        updateBrandingLogo();
    });
}

// Gestión del Logo de COM.LED
let logoMode = null; // 'theme-aware' | 'single'
function updateBrandingLogo() {
    const htmlEl = document.documentElement;
    const customLogoEl = document.getElementById("customBrandingLogo");
    const defaultBrandingEl = document.getElementById("defaultBranding");
    if (!customLogoEl || !defaultBrandingEl) return;

    if (logoMode === "theme-aware") {
        const isDark = htmlEl.classList.contains("dark");
        customLogoEl.src = isDark ? "logo-dark.png" : "logo-light.png";
    } else if (logoMode === "single") {
        customLogoEl.src = "logo.png";
    }
}

function showCustomLogo() {
    const customLogoEl = document.getElementById("customBrandingLogo");
    const defaultBrandingEl = document.getElementById("defaultBranding");
    if (customLogoEl && defaultBrandingEl) {
        defaultBrandingEl.classList.add("hidden");
        customLogoEl.classList.remove("hidden");
        updateBrandingLogo();
    }
}

function checkCustomLogos() {
    const testLogoDark = new Image();
    testLogoDark.src = "logo-dark.png";
    testLogoDark.onload = function() {
        logoMode = "theme-aware";
        showCustomLogo();
    };
    testLogoDark.onerror = function() {
        const testLogoLight = new Image();
        testLogoLight.src = "logo-light.png";
        testLogoLight.onload = function() {
            logoMode = "theme-aware";
            showCustomLogo();
        };
        testLogoLight.onerror = function() {
            const testLogoSingle = new Image();
            testLogoSingle.src = "logo.png";
            testLogoSingle.onload = function() {
                logoMode = "single";
                showCustomLogo();
            };
        };
    };
}

// ==========================================
// 5. DETECCIÓN AUTOMÁTICA DESDE NOMBRE
// ==========================================
function parseInfoFromFilename(filename) {
    const nameWithoutExt = filename.replace(/\.[^/.]+$/, "");
    let code = "";
    const codeMatch = nameWithoutExt.match(/CL\s*[-–]?\s*(\d+)/i) || nameWithoutExt.match(/\b(\d{5,6})\b/);
    if (codeMatch) {
        code = codeMatch[1];
    }
    
    let name = "";
    const parts = nameWithoutExt.split(/[-–]/);
    if (parts.length >= 3) {
        const middlePart = parts[1].trim();
        if (code && middlePart.includes(code)) {
            name = middlePart.replace(code, "").trim();
        } else {
            name = middlePart;
        }
    } else if (parts.length === 2) {
        const left = parts[0].trim();
        const right = parts[1].trim();
        if (code && right.includes(code)) {
            name = right.replace(code, "").trim();
        } else if (code && left.includes(code)) {
            name = left.replace(code, "").trim();
        } else {
            name = right;
        }
    } else {
        if (code) {
            name = nameWithoutExt.replace(code, "").replace(/CL/i, "").replace(/ET/i, "").replace(/[-–]/g, "").trim();
        }
    }
    
    if (name) {
        name = name.replace(/\b\d+W\b/i, "")
                   .replace(/CL/i, "")
                   .replace(/ET/i, "")
                   .replace(/[-–]/g, "")
                   .replace(/\s+/g, " ")
                   .trim();
    }
    
    return { name, code };
}

// ==========================================
// 6. GESTIÓN DE DROPZONE Y ARCHIVO
// ==========================================
function initFileUploader() {
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");
    const fileNameDisplay = document.getElementById("fileNameDisplay");
    if (!dropzone || !fileInput) return;

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
            selectFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            selectFile(fileInput.files[0]);
        }
    });
}

function selectFile(file) {
    AppState.file = file;
    const fileNameDisplay = document.getElementById("fileNameDisplay");
    const dropzone = document.getElementById("dropzone");
    if (fileNameDisplay) {
        fileNameDisplay.innerHTML = `<span class="text-brand-600 dark:text-brand-400 font-bold">${file.name}</span>`;
    }
    if (dropzone) {
        dropzone.classList.add("border-brand-500/50", "bg-brand-500/5");
    }

    // Auto-rellenar nombre/código
    const detected = parseInfoFromFilename(file.name);
    const nombreInput = document.getElementById("nombreInput");
    const codigoInput = document.getElementById("codigoInput");
    
    if (nombreInput) nombreInput.value = detected.name || "";
    if (codigoInput) codigoInput.value = detected.code || "";
}

// ==========================================
// 7. STEPPER Y PROGRESO DE PIPELINE
// ==========================================
function getStepperElements() {
    return {
        progressText: document.getElementById("currentStepName"),
        progressPercent: document.getElementById("progressPercent"),
        progressBar: document.getElementById("progressBar"),
        steps: {
            1: document.getElementById("step1"),
            2: document.getElementById("step2"),
            3: document.getElementById("step3")
        }
    };
}

function updateProgressUI(percent, statusText) {
    const el = getStepperElements();
    if (el.progressBar) el.progressBar.style.width = `${percent}%`;
    if (el.progressPercent) el.progressPercent.innerText = `${percent}%`;
    if (el.progressText) el.progressText.innerText = statusText;
}

function resetStepper() {
    const el = getStepperElements();
    Object.keys(el.steps).forEach(stepNum => {
        const stepEl = el.steps[stepNum];
        if (!stepEl) return;
        stepEl.className = "step-item flex items-start gap-4 text-slate-400 transition-all";
        const icon = stepEl.querySelector(".step-icon");
        if (icon) {
            icon.className = "step-icon w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-850 border border-slate-300/40 dark:border-slate-800 flex items-center justify-center text-xs font-bold shrink-0";
            icon.innerHTML = stepNum;
        }
    });
}

function setStepActive(stepNum) {
    const el = getStepperElements();
    const stepEl = el.steps[stepNum];
    if (!stepEl) return;
    stepEl.className = "step-item flex items-start gap-4 text-brand-600 dark:text-brand-400 transition-all";
    const icon = stepEl.querySelector(".step-icon");
    if (icon) {
        icon.className = "step-icon w-6 h-6 rounded-full bg-brand-500/10 border border-brand-500 flex items-center justify-center text-xs font-bold shrink-0 pulse-active";
        icon.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i>';
    }
}

function setStepDone(stepNum) {
    const el = getStepperElements();
    const stepEl = el.steps[stepNum];
    if (!stepEl) return;
    stepEl.className = "step-item flex items-start gap-4 text-emerald-600 dark:text-emerald-400 transition-all";
    const icon = stepEl.querySelector(".step-icon");
    if (icon) {
        icon.className = "step-icon w-6 h-6 rounded-full bg-emerald-500/10 border border-emerald-500 flex items-center justify-center text-xs font-bold shrink-0";
        icon.innerHTML = '<i class="fa-solid fa-check"></i>';
    }
}

// Lanzar extracción de archivo
async function startExtraction() {
    if (!AppState.file) {
        showToast("Por favor, selecciona un archivo primero", "error");
        return;
    }

    const nombre = document.getElementById("nombreInput")?.value || "";
    const codigo = document.getElementById("codigoInput")?.value || "";
    const instalacion = document.getElementById("instalacionInput")?.value || "";

    const formData = new FormData();
    formData.append("file", AppState.file);
    if (nombre) formData.append("nombre_comled", nombre);
    if (codigo) formData.append("codigo_comled", codigo);
    if (instalacion) formData.append("instalacion_manual", instalacion);

    const btnExtract = document.getElementById("btnExtract");

    try {
        if (btnExtract) {
            btnExtract.disabled = true;
            btnExtract.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Subiendo archivo...';
        }

        // 1. Subir archivo
        const uploadRes = await fetch(`${API_BASE}/upload`, {
            method: "POST",
            body: formData
        });

        if (!uploadRes.ok) {
            throw new Error("No se pudo subir el archivo correctamente al servidor.");
        }

        // Configurar los títulos del stepper según el modo actual
        const elStepper = getStepperElements();
        const step1Text = elStepper.steps[1]?.querySelector("div:last-child");
        const step2Text = elStepper.steps[2]?.querySelector("div:last-child");
        const step3Text = elStepper.steps[3]?.querySelector("div:last-child");

        if (AppState.mode === "proveedor") {
            if (step1Text) step1Text.innerText = "Extrayendo datos técnicos con OpenAI Vision...";
            if (step2Text) step2Text.innerText = "Buscando imágenes de la luminaria y cotas...";
            if (step3Text) step3Text.innerText = "Validando integridad y calidad de la extracción...";
        } else if (AppState.mode === "estandar") {
            if (step1Text) step1Text.innerText = "Leyendo documento del catálogo original...";
            if (step2Text) step2Text.innerText = "Buscando imágenes del producto incrustadas...";
            if (step3Text) step3Text.innerText = "Extrayendo datos de luminaria mediante IA...";
        } else {
            if (step1Text) step1Text.innerText = "Leyendo metadatos de ficha COM.LED anterior...";
            if (step2Text) step2Text.innerText = "Recuperando imágenes adjuntas del PDF...";
            if (step3Text) step3Text.innerText = "Inicializando variables para la modificación...";
        }

        // 2. Entrar en la pantalla de Stepper
        navigateToSection("progress");
        updateProgressUI(10, "Iniciando análisis del archivo...");
        resetStepper();
        setStepActive(1);

        // Progreso simulado para mayor suavidad
        let progressVal = 10;
        const progressInterval = setInterval(() => {
            if (progressVal < 90) {
                progressVal += Math.floor(Math.random() * 4) + 2;
                if (progressVal > 90) progressVal = 90;
                
                if (progressVal > 35 && progressVal <= 68) {
                    setStepDone(1);
                    setStepActive(2);
                    updateProgressUI(progressVal, "Detectando y aislando planos e imágenes...");
                } else if (progressVal > 68) {
                    setStepDone(2);
                    setStepActive(3);
                    updateProgressUI(progressVal, "Validando coherencia técnica de datos...");
                } else {
                    updateProgressUI(progressVal, "Leyendo textos de la ficha y mapeando campos...");
                }
            }
        }, 500);

        // 3. Petición API para ejecutar el script de extracción
        const extractRes = await fetch(`${API_BASE}/extract?mode=${AppState.mode}`, {
            method: "POST"
        });

        clearInterval(progressInterval);

        if (!extractRes.ok) {
            const errData = await extractRes.json();
            throw new Error(errData.detail || "Error en el motor de extracción técnica.");
        }

        const data = await extractRes.json();
        AppState.data = data.datos;
        AppState.status = data.estado;

        setStepDone(1);
        setStepDone(2);
        setStepDone(3);
        updateProgressUI(100, "Extracción de datos completada.");

        // Redirigir al formulario de validación
        setTimeout(() => {
            renderValidationPanel();
            navigateToSection("validation");
            if (btnExtract) {
                btnExtract.disabled = false;
                btnExtract.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Iniciar Extracción Inteligente';
            }
        }, 700);

    } catch (e) {
        showToast(e.message, "error");
        navigateToSection("upload");
        if (btnExtract) {
            btnExtract.disabled = false;
            btnExtract.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Iniciar Extracción Inteligente';
        }
    }
}

// ==========================================
// 8. PANEL DE EDICIÓN Y GESTOR DE IMÁGENES
// ==========================================
const FIELD_GROUPS = {
    identificacion: {
        title: "Identificación del Producto",
        fields: {
            nombre_producto: "Nombre Comercial",
            codigo_comled: "Código COM.LED",
            instalacion: "Instalación"
        }
    },
    electrico: {
        title: "Parámetros Eléctricos",
        fields: {
            potencia: "Potencia (W)",
            tension_entrada: "Voltaje Entrada",
            clase_aislamiento: "Clase Aislamiento"
        }
    },
    luminico: {
        title: "Parámetros Lumínicos",
        fields: {
            flujo_luminoso: "Flujo (Lm)",
            eficacia_luminosa: "Eficacia (Lm/W)",
            cct: "Temp. Color (CCT)",
            cri: "IRC (CRI)",
            ugr: "Deslumbramiento (UGR)"
        }
    },
    opticas: {
        title: "Ópticas y Construcción",
        fields: {
            apertura_haz: "Ángulo Óptica",
            aperturas_disponibles: "Ópticas Opcionales",
            colores_disponibles: "Colores/Acabados",
            material_carcasa: "Material Cuerpo"
        }
    },
    proteccion: {
        title: "Protección Física",
        fields: {
            ip: "Grado Estanqueidad (IP)",
            ik: "Resistencia Impacto (IK)"
        }
    }
};

function renderValidationPanel() {
    const dataFormContainer = document.getElementById("dataFormContainer");
    if (!dataFormContainer) return;

    dataFormContainer.innerHTML = "";

    // Agrupar los inputs lógicamente para un diseño premium
    Object.keys(FIELD_GROUPS).forEach(groupId => {
        const group = FIELD_GROUPS[groupId];
        
        // Crear un divisor / contenedor de grupo
        const groupHeader = document.createElement("div");
        groupHeader.className = "col-span-1 md:col-span-2 border-t border-slate-200/40 dark:border-slate-800/40 pt-4 mt-2 first:border-0 first:pt-0 first:mt-0";
        groupHeader.innerHTML = `<h4 class="text-xs font-bold text-slate-405 dark:text-slate-400 uppercase tracking-widest">${group.title}</h4>`;
        dataFormContainer.appendChild(groupHeader);

        // Inyectar inputs del grupo
        Object.keys(group.fields).forEach(key => {
            const label = group.fields[key];
            const value = AppState.data[key] || "";
            const wrapper = document.createElement("div");
            wrapper.className = "space-y-1.5";
            wrapper.innerHTML = `
                <label class="text-[11px] font-bold text-slate-450 dark:text-slate-500 uppercase tracking-wider block">${label}</label>
                <input type="text" data-key="${key}" value="${value}" class="tech-field-input w-full bg-slate-150/40 dark:bg-slate-900/40 border border-slate-250/30 dark:border-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all font-medium">
            `;
            dataFormContainer.appendChild(wrapper);
        });
    });

    // Añadir listener reactivo para no perder las modificaciones del usuario
    document.querySelectorAll(".tech-field-input").forEach(input => {
        input.addEventListener("input", (e) => {
            const key = e.target.getAttribute("data-key");
            AppState.data[key] = e.target.value;
        });
    });

    updateImagesPreviews();
    initCalculadora();
}

// ==========================================
// 8. CALCULADORA REGLA DE 3 (LÚMENES / W / LM/W)
// ==========================================

/**
 * Extrae solo el valor numérico de un string como "20W", "2000 lm", "100 lm/W", ">90", etc.
 * @param {string} str
 * @returns {number|null}
 */
function parseNumericValue(str) {
    if (!str && str !== 0) return null;
    const s = String(str).replace(",", ".");
    const match = s.match(/[\d.]+/);
    if (!match) return null;
    const n = parseFloat(match[0]);
    return isNaN(n) ? null : n;
}

/**
 * Formatea un número para los campos del formulario manteniendo el estilo original.
 * Si el string original tenía unidades ("W", "lm", "lm/W"), las conserva.
 */
function formatWithUnit(numericValue, originalStr) {
    const num = Math.round(numericValue * 100) / 100; // 2 decimales máx
    const s = String(originalStr || "");
    // Detectar unidad en el string original
    if (/lm\/W/i.test(s)) return `${num} lm/W`;
    if (/lm/i.test(s))    return `${num} lm`;
    if (/W/i.test(s))     return `${num}W`;
    return String(num);
}

/**
 * Inicializa la calculadora: rellena los inputs con los valores actuales
 * y vincula el botón "Aplicar Cálculo".
 */
function initCalculadora() {
    // Rellenar inputs con valores actuales de AppState
    const inputW  = document.getElementById("calcPotencia");
    const inputLm = document.getElementById("calcFlujo");
    const inputEf = document.getElementById("calcEficacia");

    if (inputW)  inputW.value  = parseNumericValue(AppState.data.potencia)       ?? "";
    if (inputLm) inputLm.value = parseNumericValue(AppState.data.flujo_luminoso) ?? "";
    if (inputEf) inputEf.value = parseNumericValue(AppState.data.eficacia_luminosa) ?? "";

    // Limpiar resultado anterior
    const resDiv  = document.getElementById("calcResultado");
    const resSpan = document.getElementById("calcResultadoTexto");
    if (resDiv)  resDiv.classList.add("hidden");
    if (resSpan) resSpan.textContent = "";

    // Bind del botón
    const btn = document.getElementById("btnAplicarCalculo");
    if (btn) {
        // Clonar para eliminar listeners anteriores
        const nuevoBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(nuevoBtn, btn);
        nuevoBtn.addEventListener("click", applyRegla3);
    }
}

/**
 * Lee los tres inputs, detecta cuál calcular y aplica la fórmula:
 *   lm = W × lm/W
 *   W  = lm / lm/W
 *   lm/W = lm / W
 * Actualiza AppState.data y re-renderiza el formulario.
 */
function applyRegla3() {
    const inputW  = document.getElementById("calcPotencia");
    const inputLm = document.getElementById("calcFlujo");
    const inputEf = document.getElementById("calcEficacia");
    const resDiv  = document.getElementById("calcResultado");
    const resSpan = document.getElementById("calcResultadoTexto");

    if (!inputW || !inputLm || !inputEf) return;

    const W   = inputW.value  !== "" ? parseFloat(inputW.value)  : null;
    const lm  = inputLm.value !== "" ? parseFloat(inputLm.value) : null;
    const ef  = inputEf.value !== "" ? parseFloat(inputEf.value) : null;

    const target = document.querySelector('input[name="calcTarget"]:checked')?.value || "flujo";

    let nuevoW = W, nuevoLm = lm, nuevoEf = ef;
    let resultMsg = "";

    if (target === "flujo") {
        if (W === null || ef === null) {
            showToast("Para calcular el Flujo, introduce Potencia (W) y Eficacia (lm/W).", "error");
            return;
        }
        nuevoLm = W * ef;
        resultMsg = `Flujo calculado: ${nuevoLm} lm`;
    } else if (target === "eficacia") {
        if (W === null || lm === null) {
            showToast("Para calcular la Eficacia, introduce Potencia (W) y Flujo (lm).", "error");
            return;
        }
        if (W === 0) { showToast("La potencia no puede ser 0.", "error"); return; }
        nuevoEf = lm / W;
        nuevoEf = Math.round(nuevoEf * 100) / 100;
        resultMsg = `Eficacia calculada: ${nuevoEf} lm/W`;
    } else if (target === "potencia") {
        if (lm === null || ef === null) {
            showToast("Para calcular la Potencia, introduce Flujo (lm) y Eficacia (lm/W).", "error");
            return;
        }
        if (ef === 0) { showToast("La eficacia no puede ser 0.", "error"); return; }
        nuevoW = lm / ef;
        nuevoW = Math.round(nuevoW * 100) / 100;
        resultMsg = `Potencia calculada: ${nuevoW} W`;
    }

    // Actualizar AppState.data preservando el formato/unidad original
    AppState.data.potencia          = formatWithUnit(nuevoW,  AppState.data.potencia);
    AppState.data.potencia_resumido = formatWithUnit(nuevoW,  AppState.data.potencia_resumido || AppState.data.potencia);
    AppState.data.flujo_luminoso    = formatWithUnit(nuevoLm, AppState.data.flujo_luminoso);
    AppState.data.flujo_resumido    = formatWithUnit(nuevoLm, AppState.data.flujo_resumido || AppState.data.flujo_luminoso);
    AppState.data.eficacia_luminosa = formatWithUnit(nuevoEf, AppState.data.eficacia_luminosa);
    AppState.data.eficacia_resumido = formatWithUnit(nuevoEf, AppState.data.eficacia_resumido || AppState.data.eficacia_luminosa);

    // Re-renderizar el formulario para que los inputs reflejen los nuevos valores
    renderValidationPanel();

    // Mostrar resultado
    showToast(`✅ ${resultMsg}`, "success");
    if (resDiv && resSpan) {
        resSpan.textContent = resultMsg;
        resDiv.classList.remove("hidden");
        setTimeout(() => resDiv.classList.add("hidden"), 5000);
    }
}

function updateImagesPreviews() {
    const cacheBuster = Date.now();

    // ── Foto del Producto ──
    const imgProduct  = document.getElementById("imgProductoPreview");
    const badgeProduct = document.getElementById("badgeProducto");
    const placeholderProduct = document.getElementById("placeholderProducto");
    const wrapProduct = document.getElementById("previewProductoWrap");

    if (imgProduct && badgeProduct) {
        if (AppState.status.producto_ok && AppState.status.producto_url) {
            const url = AppState.status.producto_url.startsWith("http")
                ? AppState.status.producto_url
                : `${window.location.origin}${AppState.status.producto_url}`;
            imgProduct.src = `${url}?t=${cacheBuster}`;
            imgProduct.classList.remove("hidden");
            if (placeholderProduct) placeholderProduct.classList.add("hidden");
            if (wrapProduct) {
                wrapProduct.classList.remove("border-dashed","border-slate-200","dark:border-slate-700");
                wrapProduct.classList.add("border-solid","border-emerald-400/50");
            }
            badgeProduct.className = "flex items-center gap-1.5 text-xs font-bold px-2.5 py-0.5 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/15";
            badgeProduct.innerHTML = '<i class="fa-solid fa-circle-check"></i> Lista';
        } else {
            imgProduct.classList.add("hidden");
            imgProduct.removeAttribute("src");
            if (placeholderProduct) placeholderProduct.classList.remove("hidden");
            if (wrapProduct) {
                wrapProduct.classList.remove("border-solid","border-emerald-400/50");
                wrapProduct.classList.add("border-dashed","border-slate-200","dark:border-slate-700");
            }
            badgeProduct.className = "flex items-center gap-1.5 text-xs font-bold px-2.5 py-0.5 rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/15";
            badgeProduct.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Vacía';
        }
    }

    // ── Plano de Dimensiones ──
    const imgDims  = document.getElementById("imgDimensionesPreview");
    const badgeDims = document.getElementById("badgeDimensiones");
    const placeholderDims = document.getElementById("placeholderDimensiones");
    const wrapDims = document.getElementById("previewDimensionesWrap");

    if (imgDims && badgeDims) {
        if (AppState.status.dimensiones_ok && AppState.status.dimensiones_url) {
            const url = AppState.status.dimensiones_url.startsWith("http")
                ? AppState.status.dimensiones_url
                : `${window.location.origin}${AppState.status.dimensiones_url}`;
            imgDims.src = `${url}?t=${cacheBuster}`;
            imgDims.classList.remove("hidden");
            if (placeholderDims) placeholderDims.classList.add("hidden");
            if (wrapDims) {
                wrapDims.classList.remove("border-dashed","border-slate-200","dark:border-slate-700");
                wrapDims.classList.add("border-solid","border-emerald-400/50");
            }
            badgeDims.className = "flex items-center gap-1.5 text-xs font-bold px-2.5 py-0.5 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/15";
            badgeDims.innerHTML = '<i class="fa-solid fa-circle-check"></i> Lista';
        } else {
            imgDims.classList.add("hidden");
            imgDims.removeAttribute("src");
            if (placeholderDims) placeholderDims.classList.remove("hidden");
            if (wrapDims) {
                wrapDims.classList.remove("border-solid","border-emerald-400/50");
                wrapDims.classList.add("border-dashed","border-slate-200","dark:border-slate-700");
            }
            badgeDims.className = "flex items-center gap-1.5 text-xs font-bold px-2.5 py-0.5 rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/15";
            badgeDims.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Vacía';
        }
    }

    // Mostrar banner de aviso si falta alguna imagen
    const missingAlert = document.getElementById("missingImagesAlert");
    const missingText  = document.getElementById("missingImagesText");
    if (missingAlert && missingText) {
        if (!AppState.status.producto_ok || !AppState.status.dimensiones_ok) {
            missingAlert.classList.remove("hidden");
            let msg = "No se ha detectado automáticamente la ";
            if (!AppState.status.producto_ok && !AppState.status.dimensiones_ok) {
                msg += "foto de la luminaria ni el plano de dimensiones. Súbelos manualmente.";
            } else if (!AppState.status.producto_ok) {
                msg += "foto de la luminaria. Súbela manualmente.";
            } else {
                msg += "cota de dimensiones. Súbela manualmente.";
            }
            missingText.innerText = msg;
        } else {
            missingAlert.classList.add("hidden");
        }
    }
}

// Handler para drag & drop en las zonas de imagen
function handleImageDrop(event, type) {
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
        const file = files[0];
        if (!file.type.startsWith("image/")) {
            showToast("Solo se aceptan imágenes (PNG, JPG, WEBP)", "error");
            return;
        }
        uploadManualImage(type, file);
    }
}

// Subir imágenes manualmente
async function uploadManualImage(type, file) {
    const badgeId = type === "producto" ? "badgeProducto" : "badgeDimensiones";
    const badge = document.getElementById(badgeId);
    if (badge) {
        badge.className = "flex items-center gap-1.5 text-xs font-bold px-2.5 py-0.5 rounded-lg bg-brand-500/10 text-brand-650 dark:text-brand-400 border border-brand-500/15";
        badge.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Cargando...';
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch(`${API_BASE}/upload-manual-image?type=${type}`, {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            throw new Error("Fallo al guardar la imagen de reemplazo.");
        }

        const data = await res.json();
        if (data.estado) {
            AppState.status = data.estado;
        } else {
            AppState.status[`${type}_ok`] = true;
        }

        showToast(`Imagen de ${type} reemplazada correctamente`, "success");
        updateImagesPreviews();

    } catch (e) {
        showToast(e.message, "error");
        updateImagesPreviews();
    }
}

function initManualImageUploaders() {
    const fileProductUpload = document.getElementById("fileProductUpload");
    const fileDimensionsUpload = document.getElementById("fileDimensionsUpload");

    if (fileProductUpload) {
        fileProductUpload.addEventListener("change", () => {
            if (fileProductUpload.files.length > 0) {
                uploadManualImage("producto", fileProductUpload.files[0]);
            }
        });
    }

    if (fileDimensionsUpload) {
        fileDimensionsUpload.addEventListener("change", () => {
            if (fileDimensionsUpload.files.length > 0) {
                uploadManualImage("dimensiones", fileDimensionsUpload.files[0]);
            }
        });
    }
}

// ==========================================
// 9. COMPILACIÓN DE PPTX & EXPORTACIÓN A PDF
// ==========================================
async function compileTechnicalDatasheet() {
    const btnCompile = document.getElementById("btnCompile");

    try {
        if (btnCompile) {
            btnCompile.disabled = true;
            btnCompile.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Guardando datos...';
        }

        // 1. Guardar cambios en el backend antes de compilar
        const saveRes = await fetch(`${API_BASE}/datos`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(AppState.data)
        });

        if (!saveRes.ok) {
            throw new Error("No se pudieron almacenar las modificaciones técnicas.");
        }

        // 2. Mostrar Stepper de generación
        navigateToSection("progress");
        updateProgressUI(5, "Compilando PowerPoint...");
        resetStepper();

        const elStepper = getStepperElements();
        const step1Text = elStepper.steps[1]?.querySelector("div:last-child");
        const step2Text = elStepper.steps[2]?.querySelector("div:last-child");
        const step3Text = elStepper.steps[3]?.querySelector("div:last-child");

        if (AppState.mode === "modificar") {
            if (step1Text) step1Text.innerText = "Ajustando curvas fotométricas...";
            if (step2Text) step2Text.innerText = "Compilando plantilla PowerPoint con nuevos valores...";
            if (step3Text) step3Text.innerText = "Generando PDF modificado definitivo...";
        } else {
            if (step1Text) step1Text.innerText = "Limpiando fondo del producto y escalando resolución...";
            if (step2Text) step2Text.innerText = "Procesando curvas fotométricas del producto...";
            if (step3Text) step3Text.innerText = "Renderizando PowerPoint y convirtiendo a PDF...";
        }

        setStepActive(1);
        updateProgressUI(15, "Mejorando imágenes y quitando fondos...");

        let progressVal = 15;
        const progressInterval = setInterval(() => {
            if (progressVal < 95) {
                progressVal += Math.floor(Math.random() * 3) + 1;
                if (progressVal > 95) progressVal = 95;
                
                if (progressVal > 35 && progressVal <= 70) {
                    setStepDone(1);
                    setStepActive(2);
                    updateProgressUI(progressVal, "Dibujando gráficos de curvas polares...");
                } else if (progressVal > 70) {
                    setStepDone(2);
                    setStepActive(3);
                    updateProgressUI(progressVal, "Inyectando variables de tabla en PPTX...");
                } else {
                    updateProgressUI(progressVal, "Aplicando recorte y corrección cromática...");
                }
            }
        }, 800);

        // 3. Ejecutar llamada al pipeline de generación del backend
        const compileRes = await fetch(`${API_BASE}/generate?mode=${AppState.mode}`, {
            method: "POST"
        });

        clearInterval(progressInterval);

        if (!compileRes.ok) {
            const errData = await compileRes.json();
            throw new Error(errData.detail || "Fallo en los scripts de generación local.");
        }

        const buildData = await compileRes.json();

        setStepDone(1);
        setStepDone(2);
        setStepDone(3);
        updateProgressUI(100, "Compilación exitosa.");

        // Redirigir a sección de éxito
        setTimeout(() => {
            navigateToSection("success");
            
            const btnDownloadPdf = document.getElementById("btnDownloadPdf");
            if (btnDownloadPdf && buildData.pdf_url) {
                btnDownloadPdf.href = window.location.origin + buildData.pdf_url;
            }

            if (btnCompile) {
                btnCompile.disabled = false;
                btnCompile.innerHTML = '<i class="fa-solid fa-file-pdf"></i> Generar Ficha Técnica';
            }
        }, 700);

    } catch (e) {
        showToast(e.message, "error");
        navigateToSection("validation");
        if (btnCompile) {
            btnCompile.disabled = false;
            btnCompile.innerHTML = '<i class="fa-solid fa-file-pdf"></i> Generar Ficha Técnica';
        }
    }
}

// Abrir la carpeta de salidas nativamente
async function openOutputsFolder() {
    try {
        const res = await fetch(`${API_BASE}/open-folder`, { method: "POST" });
        if (!res.ok) throw new Error("No se pudo abrir la carpeta del sistema.");
        showToast("Carpeta de salidas abierta en el ordenador", "success");
    } catch (e) {
        showToast(e.message, "error");
    }
}

function initActionButtons() {
    const btnCompile = document.getElementById("btnCompile");
    if (btnCompile) {
        btnCompile.addEventListener("click", compileTechnicalDatasheet);
    }

    const btnOpenFolder = document.getElementById("btnOpenFolder");
    if (btnOpenFolder) {
        btnOpenFolder.addEventListener("click", openOutputsFolder);
    }

    const btnBackToUpload = document.getElementById("btnBackToUpload");
    if (btnBackToUpload) {
        btnBackToUpload.addEventListener("click", () => {
            navigateToSection("upload");
        });
    }

    const btnRestart = document.getElementById("btnRestart");
    if (btnRestart) {
        btnRestart.addEventListener("click", () => {
            setMode(AppState.mode);
        });
    }

    // Volver a editar desde la pantalla de éxito (sin resetear sesión)
    const btnBackToEdit = document.getElementById("btnBackToEdit");
    if (btnBackToEdit) {
        btnBackToEdit.addEventListener("click", () => {
            navigateToSection("validation");
        });
    }
}

// ==========================================
// 10. INICIALIZACIÓN GLOBAL DE LA APLICACIÓN
// ==========================================
function initApp() {
    initTheme();
    checkCustomLogos();
    initFileUploader();
    initManualImageUploaders();
    initActionButtons();

    // Listeners para pestañas superiores
    const tabs = {
        proveedor: document.getElementById("tabProveedor"),
        estandar: document.getElementById("tabEstandar"),
        modificar: document.getElementById("tabModificar")
    };

    Object.keys(tabs).forEach(key => {
        const btn = tabs[key];
        if (btn) {
            btn.addEventListener("click", () => setMode(key));
        }
    });

    // Listener para botón de Extracción
    const btnExtract = document.getElementById("btnExtract");
    if (btnExtract) {
        btnExtract.addEventListener("click", startExtraction);
    }

    // Configurar modo inicial por defecto
    setMode("proveedor");
}

// Iniciar aplicación al cargar el DOM
document.addEventListener("DOMContentLoaded", initApp);
