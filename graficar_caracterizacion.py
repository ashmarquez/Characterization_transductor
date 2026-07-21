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
    ax_vpp.grid(True, which="major", linestyle="--", linewidth=0.5, alpha=0.4)

    plt.title("Caracterización piezoeléctrico: Vpp y desfase vs. Frecuencia")

    lineas = [linea_vpp, linea_desfase]
    etiquetas = [l.get_label() for l in lineas]
    ax_vpp.legend(lineas, etiquetas, loc="upper right")

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
            ruta =input("escriba la rta cpleta del csv >").strip()
            if os.path.isfile(ruta):
                return ruta
            print("❌ Archivo no encontrado:{ruta} ")
            continue

        print("Archivos CSV disponibles:")
        for i, nombre in enumerate(archivos_csv, start=1):
            print(f"  {i}. {nombre}")
        
        entrada = input("SSelecciona un archivo > ").strip()
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

    while seguir:
        ruta_csv = elegir_csv()

        try:
            frecuencias, vpp_medida, desfase = leer_csv(ruta_csv)
        except FileNotFoundError:
            print(f"❌ No se encontró el archivo: {ruta_csv}")
        except KeyError as e:
            print(f"❌ El CSV no tiene la columna esperada: {e}")
        else:
            graficar(frecuencias, vpp_medida, desfase, ruta_csv)

        respuesta = input("¿Deseas graficar otro archivo? (s/n): ").strip().lower()
        if respuesta.startswith("n"):
            seguir = False
