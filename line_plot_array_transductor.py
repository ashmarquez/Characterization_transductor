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


RESISTENCIA = 1000.0  # ohmios, resistencia en serie con el piezoeléctrico


def calcular_impedancia(vpp_gen, vpp_med, resistencia):
    vpp_gen = float(vpp_gen) / (2 * (2 ** 0.5))  # Convertir de Vpp a Vrms
    vpp_med = float(vpp_med) / (2 * (2 ** 0.5))  # Convertir de Vpp a Vrms

    if vpp_med > 0:
        return resistencia * ((vpp_gen - vpp_med) / vpp_med)
    else:
        return float("nan")


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

def graficar_banda(frecuencias, media, desviacion, titulo, etiqueta_y, color, ruta_png):
    fig, ax = plt.subplots(figsize=(10, 6))

    limite_superior = [m + s for m, s in zip(media, desviacion)]
    limite_inferior = [m - s for m, s in zip(media, desviacion)]

    ax.plot(frecuencias, media, color=color, label="Promedio")
    ax.fill_between(frecuencias, limite_inferior, limite_superior,
                     color=color, alpha=0.25, label="± 1 desviación estándar")

    ax.set_xlabel("Frecuencia (kHz)")
    ax.set_ylabel(etiqueta_y, color=color)
    ax.tick_params(axis="y", labelcolor=color)
    ax.grid(True, which="major", linestyle="--", linewidth=0.5, alpha=0.4)
    ax.legend(loc="upper right")
    plt.title(titulo)

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
            carpeta_graficas = os.path.join(carpeta, "graficas")
            os.makedirs(carpeta_graficas, exist_ok=True)
            nombre_base = os.path.basename(os.path.normpath(carpeta))
            guardar_csv(frecuencias, imp_media, imp_std, desfase_media, desfase_std,
                        ruta_salida=os.path.join(carpeta_graficas, f"{nombre_base}_resumen.csv"),
            )

            graficar_banda(
                frecuencias, imp_media, imp_std,
                titulo=f"Impedancia promedio ± desv. estándar - {nombre_base}",
                etiqueta_y="Impedancia (Ω)",
                color="tab:blue",
                ruta_png=os.path.join(carpeta_graficas, f"{nombre_base}_impedancia.png"),
            )

            graficar_banda(
                frecuencias, desfase_media, desfase_std,
                titulo=f"Desfase promedio ± desv. estándar - {nombre_base}",
                etiqueta_y="Desfase (°)",
                color="tab:red",
                ruta_png=os.path.join(carpeta_graficas, f"{nombre_base}_desfase.png"),
            )

        respuesta = input("\n¿Deseas procesar otra carpeta/transductor? (s/n) > ").strip().lower()
        if respuesta.startswith("n"):
            seguir = False
