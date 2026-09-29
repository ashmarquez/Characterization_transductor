# Characterization Transductor

Script de terminal para caracterizar un transductor piezoeléctrico controlando de forma conjunta un generador de funciones Tektronix AFG1022 y un osciloscopio Tektronix TBS1000C, ambos por interfaz USBTMC.

Proyecto desarrollado en el contexto del TFM de Fuspine.

## Requisitos

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/) para la gestión del entorno
- Generador de funciones Tektronix AFG1022
- Osciloscopio Tektronix TBS1000C
- Conexión USB con acceso a los dispositivos `usbtmc` (Linux)

## Instalación

```bash
uv sync
```

## Conexión de los equipos

Por defecto el script asume los siguientes dispositivos:

- Osciloscopio: `/dev/usbtmc0`
- Generador: `/dev/usbtmc1`

Verifica los puertos disponibles con:

```bash
ls /dev/usbtmc*
```

Si no tienes permisos de lectura/escritura sobre el dispositivo:

```bash
sudo chmod 666 /dev/usbtmcX
```

Ajusta las constantes `PUERTO_OSCILOSCOPIO`, `PUERTO_GENERADOR`, `CANAL_GENERADOR_SALIDA`, `CANAL_SCOPE_GEN` y `CANAL_SCOPE_MEDIDA` al final de `caracterizacion_piezo.py` según tu montaje.

## Uso

```bash
uv run caracterizacion_piezo.py
```

Al arrancar, el script se conecta a ambos equipos, pide un identificador del elemento piezoeléctrico a evaluar y realiza un prechequeo (salida del generador activada, canales del osciloscopio activos, presencia de señal). Si todo está correcto, ejecuta un barrido automático:

1. Recorre la frecuencia de 100 kHz a 600 kHz en pasos de 1 kHz.
2. En cada paso ajusta la frecuencia del generador, espera unos segundos de estabilización y mide Vpp de ambos canales y el desfase.
3. Guarda cada punto automáticamente, sin necesidad de confirmación manual.
4. Al llegar a 600 kHz exporta el CSV con todos los puntos.
5. Pregunta si repetir el barrido con el mismo piezoeléctrico, evaluar uno nuevo (pide un nuevo identificador) o salir.

Los parámetros del barrido (frecuencia inicial/final, paso y segundos de estabilización) se ajustan en las constantes `FREQ_INICIO_KHZ`, `FREQ_FIN_KHZ`, `PASO_KHZ` y `SEGUNDOS_ESTABILIZACION` al final de `caracterizacion_piezo.py`.

## Datos de salida

Cada punto guardado incluye frecuencia (kHz), Vpp del canal del generador, Vpp del canal de medida y desfase (°) — sin timestamp. Al terminar el barrido, los datos se exportan a un archivo `caracterizacion_<identificador_piezo>_<fecha>_<hora>.csv` en el directorio actual.

## Graficado individual

`graficar_caracterizacion.py` lee un CSV de un barrido (o todos los de una carpeta, a elegir de forma interactiva), calcula la impedancia a partir de Vpp del generador, Vpp medido y una resistencia en serie (`RESISTENCIA`, por defecto 1000 Ω), y genera una figura con impedancia (kΩ) y desfase (°) frente a frecuencia, marcando los picos y valles más prominentes.

```bash
uv run graficar_caracterizacion.py
```

La gráfica se guarda como PNG en una subcarpeta `graficas/` junto al CSV de origen.

## Resumen por transductor

`line_plot_array_transductor.py` procesa todos los CSV de una carpeta (los 32 elementos de un transductor) y calcula la media y desviación estándar de impedancia y desfase para cada frecuencia, generando una gráfica de línea con banda sombreada que muestra la dispersión entre elementos.

```bash
uv run line_plot_array_transductor.py
```

Cada transductor debe tener su propia carpeta con sus CSV dentro (por ejemplo `caracterizacion_left_transducer/`, `caracterizacion_right_transducer/`). El script guarda un CSV resumen (`<carpeta>_resumen.csv`) y el PNG de la gráfica (`<carpeta>_impedancia_desfase.png`) en una subcarpeta `caracterizacion_transductor/` dentro de la carpeta del transductor.
