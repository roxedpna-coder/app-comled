import json
import re
import numpy as np
import matplotlib.pyplot as plt

with open("entradas/datos.json", "r", encoding="utf-8") as archivo:
    datos = json.load(archivo)

aperturas_disponibles = str(
    datos.get("aperturas_disponibles", "-")
).strip()

apertura_haz = str(
    datos.get("apertura_haz", "-")
).strip()

# Si la IA puso "Si" por error, usamos apertura_haz
if aperturas_disponibles.lower() in ["si", "sí", "yes", "-", ""]:
    aperturas_texto = apertura_haz
else:
    aperturas_texto = aperturas_disponibles

if "difusa" in aperturas_texto.lower():
    apertura = 120
else:
    numeros = re.findall(r"\d+", aperturas_texto)
    apertura = float(numeros[0]) if numeros else 120

# Guardar óptica realmente representada

# -------------------------
# LIMPIAR ÓPTICAS DISPONIBLES
# -------------------------

aperturas_disponibles = str(
    datos.get("aperturas_disponibles", "-")
).strip()

if aperturas_disponibles.lower() in [
    "si",
    "sí",
    "yes",
    "-",
    ""
]:
    datos["aperturas_disponibles"] = f"{int(apertura)}°"

datos["optica_grafico"] = f"{int(apertura)}°"

with open("entradas/datos.json", "w", encoding="utf-8") as archivo:
    json.dump(datos, archivo, indent=2, ensure_ascii=False)

theta = np.linspace(-90, 90, 400)
sigma = apertura / 2.35
intensidad = np.exp(-(theta ** 2) / (2 * sigma ** 2))

fig = plt.figure(figsize=(8, 8))
ax = plt.subplot(111, polar=True)

# Curva hacia abajo
theta_rad = np.deg2rad(theta + 180)

ax.plot(theta_rad, intensidad, linewidth=4)
ax.fill(theta_rad, intensidad, alpha=0.25)

ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

ax.set_thetamin(90)
ax.set_thetamax(270)

ax.set_rticks([])
ax.set_xticks(np.deg2rad([90, 120, 150, 180, 210, 240, 270]))
ax.set_xticklabels(["-90°", "-60°", "-30°", "0°", "30°", "60°", "90°"])

ax.grid(True)
ax.set_position([0.02, 0.02, 0.96, 0.96])

output_path = "imagenes/fotometria_generada.png"

plt.savefig(
    output_path,
    dpi=300,
    transparent=True,
    pad_inches=0
)

plt.close()

print("Fotometría generada correctamente")
print("Óptica representada:", datos["optica_grafico"])
print(output_path)