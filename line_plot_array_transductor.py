"""
Line plot with shaded band de piezoeléctricos - Fuspine
==========================================================
Lee todos los CSV de caracterización dentro de una carpeta indicando el 
transductor a evaluar, calcula la impedancia, y grafica dos figuras:

    1. Impedancia promedio ± desviación estándar vs. Frecuencia
    2. Desfase promedio ± desviación estándar vs. Frecuencia

La banda sombreada representa qué tan uniformes (o dispersos) son los
32 elementos entre sí en cada punto de frecuencia.

Cada transductor debe tener su propia carpeta con sus 32 CSV dentro.
"""

import csv
import glob
import os
import statistics
import matplotlib.pyplot as plt
from scipy.signal import find_peaks


RESISTENCIA = 1000.0  # ohmios, resistencia en serie con el piezoeléctrico


def calcular_impedancia(vpp_gen, vpp_med, resistencia):
    vpp_gen = float(vpp_gen) / (2 * (2 ** 0.5))  # Convertir de Vpp a Vrms
    vpp_med = float(vpp_med) / (2 * (2 ** 0.5))  # Convertir de Vpp a Vrms

    if vpp_med > 0:
        return resistencia * ((vpp_gen - vpp_med) / vpp_med)
    else:
        return float("nan")

def encontrar_valles(valores, frecuencias, min_separacion_khz=10):
    valores_invertidos = [-v for v in valores]
    indices, propiedades = find_peaks(valores_invertidos, distance=min_separacion_khz, prominence=0)

    if len(indices) == 0:
        return []

    orden = sorted(range(len(indices)), key=lambda k: propiedades["prominences"][k], reverse=True)
    top_indices = [indices[k] for k in orden[:2]]
    top_indices.sort()

    return [(frecuencias[i], valores[i]) for i in top_indices]

def elegir_carpeta() -> str:

    while True:
        carpetas = sorted(
            d for d in os.listdir(".")
            if os.path.isdir(d) and d != "graficas"
        )

        if not carpetas:
            print("❌ No se encontraron subcarpetas en el directorio actual.")
            ruta = input("Escribe la ruta completa de la carpeta > ").strip()
            if os.path.isdir(ruta):
                return ruta
            print(f"❌ Carpeta no encontrada: {ruta}\n")
            continue

        print("Carpetas disponibles:")
        for i, nombre in enumerate(carpetas, start=1):
            cantidad_csv = len(glob.glob(os.path.join(nombre, "*.csv")))
            print(f"  {i}. {nombre}  ({cantidad_csv} CSV dentro)")

        entrada = input("Selecciona una carpeta > ").strip()

        if entrada.isdigit():
            indice = int(entrada) - 1
            if 0 <= indice < len(carpetas):
                return carpetas[indice]
            print(f"❌ Número fuera de rango, elige entre 1 y {len(carpetas)}\n")
            continue

        if os.path.isdir(entrada):
            return entrada

        print(f"❌ Carpeta no encontrada: {entrada}\n")


def procesar_datos(carpeta: str):
    
    archivos_csv = sorted(glob.glob(os.path.join(carpeta, "*.csv")))

    if not archivos_csv:
        raise FileNotFoundError(f"No se encontraron CSV dentro de: {carpeta}")

    valores_por_frecuencia = {}  # frecuencia_kHz -> {"impedancia": [...], "desfase": [...]}

    for ruta_csv in archivos_csv:
        with open(ruta_csv, "r", encoding="utf-8") as f:
            lector = csv.DictReader(f)
            for fila in lector:
                freq = round(float(fila["frecuencia_kHz"]), 3)
                vpp_gen = float(fila["vpp_generador_V"])
                vpp_med = float(fila["vpp_medida_V"])
                desfase = float(fila["desfase_deg"])

                impedancia = calcular_impedancia(vpp_gen, vpp_med, RESISTENCIA)

                if freq not in valores_por_frecuencia:
                    valores_por_frecuencia[freq] = {"impedancia": [], "desfase": []}

                valores_por_frecuencia[freq]["impedancia"].append(impedancia)
                valores_por_frecuencia[freq]["desfase"].append(desfase)

    print(f"📄 {len(archivos_csv)} CSV procesados desde: {carpeta}")

    frecuencias = sorted(valores_por_frecuencia.keys())

    imp_media, imp_std = [], []
    desfase_media, desfase_std = [], []

    for freq in frecuencias:
        valores_imp = valores_por_frecuencia[freq]["impedancia"]
        valores_des = valores_por_frecuencia[freq]["desfase"]

        imp_media.append(statistics.mean(valores_imp))
        desfase_media.append(statistics.mean(valores_des))

        imp_std.append(statistics.stdev(valores_imp) if len(valores_imp) > 1 else 0.0)
        desfase_std.append(statistics.stdev(valores_des) if len(valores_des) > 1 else 0.0)

    return frecuencias, imp_media, imp_std, desfase_media, desfase_std

def guardar_csv(frecuencias, imp_media, imp_std, desfase_media, desfase_std, ruta_salida):
    with open(ruta_salida, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "frecuencia_kHz",
            "impedancia_media_ohm",
            "impedancia_std_ohm",
            "desfase_media_deg",
            "desfase_std_deg",
        ])
        for freq, im, istd, dm, dstd in zip(frecuencias, imp_media, imp_std, desfase_media, desfase_std):
            writer.writerow([freq, round(im, 2), round(istd, 2), round(dm, 2), round(dstd, 2)])

    print(f"💾 Resumen guardado en: {ruta_salida}")

def grafica(frecuencias, imp_media, imp_std, desfase_media, desfase_std, nombre_base, ruta_png):
    fig, ax_imp = plt.subplots(figsize=(10, 6))

    # --- IMPEDANCIA ---
    color_imp = "tab:blue"
    imp_media = [z / 1000 for z in imp_media]
    imp_std = [z / 1000 for z in imp_std]
    imp_sup = [m + s for m, s in zip(imp_media, imp_std)]
    imp_inf = [m - s for m, s in zip(imp_media, imp_std)]

    ax_imp.set_xlabel("Frecuencia (kHz)")
    ax_imp.set_ylabel("Impedancia (kΩ)", color=color_imp)
    linea_imp, = ax_imp.plot(frecuencias, imp_media, color=color_imp, label="Impedancia (promedio)")
    ax_imp.fill_between(frecuencias, imp_inf, imp_sup, color=color_imp, alpha=0.25)
    ax_imp.tick_params(axis="y", labelcolor=color_imp)
    ax_imp.grid(True, which="major", linestyle="--", linewidth=0.5, alpha=0.4)

    # --- DESFASE ---
    ax_desfase = ax_imp.twinx()
    color_desfase = "tab:red"
    des_sup = [m + s for m, s in zip(desfase_media, desfase_std)]
    des_inf = [m - s for m, s in zip(desfase_media, desfase_std)]

    ax_desfase.set_ylabel("Desfase (°)", color=color_desfase)
    linea_desfase, = ax_desfase.plot(frecuencias, desfase_media, color=color_desfase, label="Desfase (promedio)")
    ax_desfase.fill_between(frecuencias, des_inf, des_sup, color=color_desfase, alpha=0.25)
    ax_desfase.tick_params(axis="y", labelcolor=color_desfase)

    # Línea horizontal en 0°
    ax_desfase.axhline(0, color="gray", linestyle="-", linewidth=0.8, zorder=1)

    plt.title(f"Impedancia y desfase (promedio ± desv. estándar) - {nombre_base}")

    # --- Valles ---
    valles_imp = encontrar_valles(imp_media, frecuencias)
    color_valle = "black"
    for freq_valle, val_valle in valles_imp:
        ax_imp.axvline(freq_valle, color=color_valle, linestyle=":", alpha=0.8)
        ax_imp.annotate(f"{freq_valle:.1f} kHz",
                         xy=(freq_valle, val_valle),
                         xytext=(5, -12), textcoords="offset points",
                         color=color_valle, fontsize=8)

    lineas = [linea_imp, linea_desfase]
    etiquetas = [l.get_label() for l in lineas]
    ax_imp.legend(lineas, etiquetas, loc="upper right")

    fig.tight_layout()
    fig.savefig(ruta_png, dpi=150)
    print(f"💾 Gráfica guardada en: {ruta_png}")

    plt.show(block=False)
    plt.pause(0.5)


if __name__ == "__main__":
    seguir = True

    while seguir:
        carpeta = elegir_carpeta()

        try:
            frecuencias, imp_media, imp_std, desfase_media, desfase_std = procesar_datos(carpeta)
        except FileNotFoundError as e:
            print(f"❌ {e}")
        except KeyError as e:
            print(f"❌ Algún CSV no tiene la columna esperada: {e}")
        else:
            carpeta_graficas = os.path.join(carpeta, "caracterizacion_transductor")
            os.makedirs(carpeta_graficas, exist_ok=True)
            nombre_base = os.path.basename(os.path.normpath(carpeta))
            guardar_csv(frecuencias, imp_media, imp_std, desfase_media, desfase_std,
                        ruta_salida=os.path.join(carpeta_graficas, f"{nombre_base}_resumen.csv"),
            )

            grafica(
                frecuencias, imp_media, imp_std, desfase_media, desfase_std,
                nombre_base = nombre_base,
                ruta_png=os.path.join(carpeta_graficas, f"{nombre_base}_impedancia_desfase.png"),
            )

        respuesta = input("\n¿Deseas procesar otra carpeta/transductor? (s/n) > ").strip().lower()
        if respuesta.startswith("n"):
            seguir = False
