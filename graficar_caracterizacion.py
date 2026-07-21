"""
Graficado de caracterización de piezoeléctrico 
==============================================================
Lee el CSV generado por el barrido automático (frecuencia_kHz,
vpp_generador_V, vpp_medida_V, desfase_deg) y grafica en una sola
figura con doble eje Y:

    - Eje X: frecuencia (kHz)
    - Eje Y izquierdo: Vpp medido (V)
    - Eje Y derecho: desfase (grados)

Al final guarda la figura como PNG junto al CSV.
"""

import csv
import matplotlib.pyplot as plt
import os
import glob


def leer_csv(ruta_csv: str):
    frecuencias = []
    vpp_gen = []
    vpp_medida = []
    desfase = []
    impedancia = []
    
    with open(ruta_csv, "r", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        for fila in lector:
            frecuencias.append(float(fila["frecuencia_kHz"]))
            vpp_medida.append(float(fila["vpp_medida_V"]))
            vpp_gen.append(float(fila["vpp_generador_V"]))
            desfase.append(float(fila["desfase_deg"]))

    return frecuencias, vpp_gen, vpp_medida, desfase
    
def encontrar_picos(valores, frecuencias, cantidad=2, min_separacion_khz=10):
    
    candidatos = []
    for i in range(1, len(valores) - 1):
        if valores[i] > valores[i - 1] and valores[i] > valores[i + 1]:
            candidatos.append((frecuencias[i], valores[i]))

    # Ordenar de mayor a menor valor los picos encontrados
    candidatos.sort(key=lambda x: x[1], reverse=True)

    picos_seleccionados = []
    for freq, val in candidatos:
        if all(abs(freq - f_sel) >= min_separacion_khz for f_sel, _ in picos_seleccionados):
            picos_seleccionados.append((freq, val))
        if len(picos_seleccionados) == cantidad:
            break

    return picos_seleccionados

def calcular_impedancia(vpp_gen, vpp_med, resistencia):
    vpp_gen = float(vpp_gen) / (2 * (2 ** 0.5))  # Convertir de Vpp a Vrms
    vpp_med = float(vpp_med) / (2 * (2 ** 0.5))  # Convertir de Vpp a Vrms
    
    if vpp_med > 0:
        return resistencia * ((vpp_gen - vpp_med) / vpp_med) 
    else:
        return float("nan")

def graficar(frecuencias, vpp_medida, desfase, impedancia, ruta_csv: str):
    fig, ax_imp = plt.subplots(figsize=(10, 6))

    # --- IMPEDANCIA ---
    impedancias_kohm = [z / 1000 for z in impedancia]
    color_imp = "tab:blue"
    ax_imp.set_xlabel("Frecuencia (kHz)")
    ax_imp.set_ylabel("Impedancia (kΩ)", color=color_imp)
    linea_imp, = ax_imp.plot(frecuencias, impedancias_kohm, color=color_imp, label="Impedancia")
    ax_imp.tick_params(axis="y", labelcolor=color_imp)
    ax_imp.grid(True, which="major", linestyle="--", linewidth=0.5, alpha=0.4)

    # --- DESFASE  ---
    ax_desfase = ax_imp.twinx()
    color_desfase = "tab:red"
    ax_desfase.set_ylabel("Desfase (°)", color=color_desfase)
    linea_desfase, = ax_desfase.plot(frecuencias, desfase, color=color_desfase, label="Desfase")
    ax_desfase.tick_params(axis="y", labelcolor=color_desfase)

    ax_desfase.axhline(0, color="gray", linestyle="-", linewidth=0.8, zorder=1)

    # ---  VPP  ---
    ax_vpp = ax_imp.twinx()
    ax_vpp.yaxis.set_visible(False)
    for spine in ax_vpp.spines.values():
        spine.set_visible(False)
    color_vpp = "gray"
    linea_vpp, = ax_vpp.plot(frecuencias, vpp_medida, color=color_vpp,
                              linestyle="--", alpha=0.5, label="Vpp medido (referencia)")

    plt.title("Caracterización piezoeléctrico: Impedancia y desfase vs. Frecuencia")

    # --- Picos ---
    picos_imp = encontrar_picos(impedancias_kohm, frecuencias, cantidad=2)
    for freq_pico, val_pico in picos_imp:
        ax_imp.axvline(freq_pico, color=color_imp, linestyle=":", alpha=0.6)
        ax_imp.annotate(f"{freq_pico:.1f} kHz",
                         xy=(freq_pico, val_pico),
                         xytext=(5, 5), textcoords="offset points",
                         color=color_imp, fontsize=8)

    desfase_abs = [abs(d) for d in desfase]
    picos_desfase = encontrar_picos(desfase_abs, frecuencias, cantidad=2)
    for freq_pico, _ in picos_desfase:
        indice = frecuencias.index(freq_pico)
        valor_real = desfase[indice]
        ax_desfase.axvline(freq_pico, color=color_desfase, linestyle=":", alpha=0.6)
        ax_desfase.annotate(f"{freq_pico:.1f} kHz",
                             xy=(freq_pico, valor_real),
                             xytext=(5, -12), textcoords="offset points",
                             color=color_desfase, fontsize=8)

    lineas = [linea_imp, linea_desfase, linea_vpp]
    etiquetas = [l.get_label() for l in lineas]
    ax_imp.legend(lineas, etiquetas, loc="upper right")

    fig.tight_layout()

    carpeta_graficas = os.path.join(os.path.dirname(ruta_csv) or ".", "graficas")
    os.makedirs(carpeta_graficas, exist_ok=True)
    nombre_base = os.path.basename(ruta_csv).rsplit(".", 1)[0]
    ruta_png = os.path.join(carpeta_graficas, nombre_base + ".png")
    fig.savefig(ruta_png, dpi=150)
    print(f"💾 Gráfica guardada en: {ruta_png}")

    plt.show(block=False)
    plt.pause(0.5)

def elegir_csv() -> str:
    while True:
        archivos_csv = sorted(glob.glob("*.csv"))
        if not archivos_csv:
            print("❌ No se encontraron archivos CSV en el directorio actual.")
            ruta =input("escriba la ruta completa del csv >").strip()
            if os.path.isfile(ruta):
                return ruta
            print("❌ Archivo no encontrado: {ruta}")
            continue

        print("Archivos CSV disponibles:")
        for i, nombre in enumerate(archivos_csv, start=1):
            print(f"  {i}. {nombre}")
        
        entrada = input("Selecciona un archivo > ").strip()
        if entrada.isdigit():
            indice = int(entrada) - 1
            if 0 <= indice < len(archivos_csv):
                return archivos_csv[indice]
            print("❌ Opción inválida. Por favor, selecciona un número válido.")
            continue
        
        if os.path.isfile(entrada):
            return entrada
        
        print("❌ Archivo no encontrado: {entrada}. Por favor, selecciona un archivo válido.")

if __name__ == "__main__":
    seguir = True
    
    RESISTENCIA = 1000.0  # ohmios, resistencia en serie con el piezoeléctrico

    while seguir:
        ruta_csv = elegir_csv()

        try:
            frecuencias, vpp_gen, vpp_medida, desfase = leer_csv(ruta_csv)
            impedancia = [calcular_impedancia(vpp_gen, vpp_med, RESISTENCIA) for vpp_gen, vpp_med in zip(vpp_gen, vpp_medida)]
        except FileNotFoundError:
            print(f"❌ No se encontró el archivo: {ruta_csv}")
        except KeyError as e:
            print(f"❌ El CSV no tiene la columna esperada: {e}")
        else:
            graficar(frecuencias, vpp_medida, desfase, impedancia, ruta_csv)

        respuesta = input("¿Deseas graficar otro archivo? (s/n): ").strip().lower()
        if respuesta.startswith("n"):
            seguir = False
