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

Al arrancar, el script se conecta a ambos equipos y realiza un prechequeo (salida del generador activada, canales del osciloscopio activos, presencia de señal). Si todo está correcto, entra en modo interactivo:

| Entrada | Acción |
|---|---|
| Un número (kHz) | Ajusta la frecuencia del generador, p. ej. `260` fija 260 kHz |
| `leer` | Mide Vpp de ambos canales y el desfase, y pregunta si guardar el punto |
| `datos` | Muestra la tabla de puntos guardados hasta el momento |
| `salir` | Guarda el CSV final y cierra la conexión con los equipos |

## Datos de salida

Cada punto guardado incluye frecuencia (kHz), Vpp del canal del generador, Vpp del canal de medida, desfase (°) y timestamp. Al salir, los datos se exportan a un archivo `caracterizacion_piezo_<fecha>_<hora>.csv` en el directorio actual.
