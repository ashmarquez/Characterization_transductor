"""
Graficado de caracterización de piezoeléctrico - Fuspine TFM
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


def leer_csv(ruta_csv: str):
    frecuencias = []
    vpp_medida = []
    desfase = []

    with open(ruta_csv, "r", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        for fila in lector:
            frecuencias.append(float(fila["frecuencia_kHz"]))
            vpp_medida.append(float(fila["vpp_medida_V"]))
            desfase.append(float(fila["desfase_deg"]))

    return frecuencias, vpp_medida, desfase


def graficar(frecuencias, vpp_medida, desfase, ruta_csv: str):
    fig, ax_vpp = plt.subplots(figsize=(10, 6))

    color_vpp = "tab:blue"
    ax_vpp.set_xlabel("Frecuencia (kHz)")
    ax_vpp.set_ylabel("Vpp medido (V)", color=color_vpp)
    linea_vpp, = ax_vpp.plot(frecuencias, vpp_medida, color=color_vpp, label="Vpp medido")
    ax_vpp.tick_params(axis="y", labelcolor=color_vpp)

    ax_desfase = ax_vpp.twinx()
    color_desfase = "tab:red"
    ax_desfase.set_ylabel("Desfase (°)", color=color_desfase)
    linea_desfase, = ax_desfase.plot(frecuencias, desfase, color=color_desfase, label="Desfase")
    ax_desfase.tick_params(axis="y", labelcolor=color_desfase)

    plt.title("Caracterización piezoeléctrico: Vpp y desfase vs. Frecuencia")

    lineas = [linea_vpp, linea_desfase]
    etiquetas = [l.get_label() for l in lineas]
    ax_vpp.legend(lineas, etiquetas, loc="upper right")

    fig.tight_layout()

    ruta_png = ruta_csv.rsplit(".", 1)[0] + ".png"
    fig.savefig(ruta_png, dpi=150)
    print(f"💾 Gráfica guardada en: {ruta_png}")

    plt.show()


if __name__ == "__main__":
    ruta_csv = input("Nombre (o ruta) del archivo CSV a graficar > ").strip()

    try:
        frecuencias, vpp_medida, desfase = leer_csv(ruta_csv)
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {ruta_csv}")
    except KeyError as e:
        print(f"❌ El CSV no tiene la columna esperada: {e}")
    else:
        graficar(frecuencias, vpp_medida, desfase, ruta_csv)
