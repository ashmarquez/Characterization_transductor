"""
Caracterización de piezoeléctrico - Fuspine TFM
================================================
Control conjunto por terminal de:
    - Generador de funciones Tektronix AFG1022 (fija la frecuencia)
    - Osciloscopio Tektronix TBS1000C (lee Vpp y desfase)

Flujo de trabajo:
    1. Escribes un número  -> se manda como frecuencia (en kHz) al generador
    2. Escribes 'leer'     -> lee Vpp (CH1, CH2) y desfase del osciloscopio
                              y te pregunta si quieres guardar ese punto
    3. Escribes 'datos'    -> muestra todo lo guardado hasta ahora
    4. Escribes 'salir'    -> guarda el CSV final y cierra la conexión
"""

import time
import csv
from datetime import datetime


# ============================================================
#   OSCILOSCOPIO - Tektronix TBS1000C
# ============================================================
class TektronixScope:
    """Controlador para el osciloscopio Tektronix TBS1000C"""

    def __init__(self, port: str):
        self.port = port
        self.scope = None
        self.is_connected = False

    def connect(self):
        import os
        try:
            os.stat(self.port)
            self.scope = open(self.port, 'r+b', buffering=0)
            self.is_connected = True
            self._write("*IDN?")
            time.sleep(0.3)
            idn = self._read()
            print(f"✅ Osciloscopio conectado: {idn}")
            return True
        except Exception as e:
            print(f"❌ No se pudo conectar al osciloscopio: {e}")
            print(f"   - Revisa: ls -l {self.port}")
            print(f"   - Si es permiso: sudo chmod 666 {self.port}")
            return False

    def _write(self, cmd: str):
        self.scope.write(cmd.encode())

    def _read(self, nbytes: int = 1024) -> str:
        return self.scope.read(nbytes).decode('utf-8', errors='ignore').strip()

    def is_channel_active(self, channel: int) -> bool:
        self._write(f'SELect:CH{channel}?')
        time.sleep(0.2)
        return self._read().strip() == "1"

    def measure_peak_to_peak(self, channel: int) -> float:
        self._write(f'MEASUrement:IMMed:SOUrce CH{channel}')
        self._write('MEASUrement:IMMed:TYPe PK2PK')
        self._write('MEASUrement:IMMed:VALue?')
        time.sleep(0.2)
        return float(self._read())

    def measure_phase(self, channel_a: int = 1, channel_b: int = 2) -> float:
        self._write(f'MEASUrement:IMMed:SOUrce1 CH{channel_a}')
        self._write(f'MEASUrement:IMMed:SOUrce2 CH{channel_b}')
        self._write('MEASUrement:IMMed:TYPe PHASe')
        self._write('MEASUrement:IMMed:VALue?')
        time.sleep(0.2)
        return float(self._read())

    def disconnect(self):
        if self.scope:
            self.scope.close()
            self.is_connected = False


# ============================================================
#   GENERADOR DE FUNCIONES - Tektronix AFG1022
# ============================================================
class AFG1022:
    """Controlador para el generador de funciones Tektronix AFG1022"""

    def __init__(self, port: str, canal: int = 1):
        self.port = port
        self.canal = canal          # canal de salida que estamos usando (1 o 2)
        self.gen = None
        self.is_connected = False

    def connect(self):
        import os
        try:
            os.stat(self.port)
            self.gen = open(self.port, 'r+b', buffering=0)
            self.is_connected = True
            self._write("*IDN?")
            time.sleep(0.3)
            idn = self._read()
            print(f"✅ Generador conectado: {idn}")
            return True
        except Exception as e:
            print(f"❌ No se pudo conectar al generador: {e}")
            print(f"   - Revisa: ls -l {self.port}")
            print(f"   - Si es permiso: sudo chmod 666 {self.port}")
            return False

    def _write(self, cmd: str):
        self.gen.write(cmd.encode())

    def _read(self, nbytes: int = 1024) -> str:
        return self.gen.read(nbytes).decode('utf-8', errors='ignore').strip()

    def output_enabled(self) -> bool:
        """Consulta si la salida del canal está activada"""
        self._write(f'OUTPut{self.canal}:STATe?')
        time.sleep(0.2)
        return self._read().strip() in ("1", "ON")

    def get_amplitude(self) -> float:
        """Lee el Vpp configurado actualmente en el generador"""
        self._write(f'SOURce{self.canal}:VOLTage:LEVel:IMMediate:AMPLitude?')
        time.sleep(0.2)
        return float(self._read())

    def get_frequency_hz(self) -> float:
        self._write(f'SOURce{self.canal}:FREQuency?')
        time.sleep(0.2)
        return float(self._read())

    def set_frequency_khz(self, freq_khz: float):
        """Recibe la frecuencia en kHz (como tú la manejas) y la manda en Hz al equipo"""
        freq_hz = freq_khz * 1000
        self._write(f'SOURce{self.canal}:FREQuency {freq_hz}')
        time.sleep(0.2)

    def disconnect(self):
        if self.gen:
            self.gen.close()
            self.is_connected = False


# ============================================================
#   CHEQUEO PREVIO (ambos equipos)
# ============================================================
def prechequeo(scope: TektronixScope, gen: AFG1022, canal_scope_gen: int, canal_scope_medida: int) -> bool:
    print("\n🔎 Verificando equipos antes de empezar...\n")
    todo_bien = True

    # --- Generador ---
    print(f"Generador AFG1022 - canal de salida usado: CH{gen.canal}")
    if gen.output_enabled():
        print(f"  ✅ Salida CH{gen.canal} activada")
    else:
        print(f"  ❌ Salida CH{gen.canal} DESACTIVADA (actívala en el equipo o con OUTPut{gen.canal}:STATe ON)")
        todo_bien = False

    vpp_configurado = gen.get_amplitude()
    freq_actual_hz = gen.get_frequency_hz()
    print(f"  Vpp configurado en el generador: {vpp_configurado:.3f} V")
    print(f"  Frecuencia actual: {freq_actual_hz/1000:.3f} kHz ({freq_actual_hz:.1f} Hz)")

    # --- Osciloscopio ---
    print(f"\nOsciloscopio TBS1000C:")
    for ch in (canal_scope_gen, canal_scope_medida):
        activo = scope.is_channel_active(ch)
        print(f"  CH{ch}: {'✅ activado' if activo else '❌ DESACTIVADO'}")
        if not activo:
            todo_bien = False

    umbral_v = 0.005
    vpp_gen_leido = scope.measure_peak_to_peak(canal_scope_gen)
    vpp_medida = scope.measure_peak_to_peak(canal_scope_medida)
    print(f"  Vpp leído en CH{canal_scope_gen} (generador): {vpp_gen_leido:.4f} V")
    print(f"  Vpp leído en CH{canal_scope_medida} (medida): {vpp_medida:.4f} V")

    if vpp_gen_leido < umbral_v:
        print(f"  ⚠️  CH{canal_scope_gen} parece no tener señal")
        todo_bien = False
    if vpp_medida < umbral_v:
        print(f"  ⚠️  CH{canal_scope_medida} parece no tener señal")
        todo_bien = False

    print()
    if todo_bien:
        print("✅ Todo listo para empezar.\n")
    else:
        print("⚠️  Revisa los puntos marcados antes de continuar.\n")

    return todo_bien


# ============================================================
#   MODO INTERACTIVO
# ============================================================
def modo_interactivo(scope: TektronixScope, gen: AFG1022, canal_scope_gen: int, canal_scope_medida: int):
    datos = []
    freq_actual_khz = gen.get_frequency_hz() / 1000

    print("=" * 60)
    print("MODO INTERACTIVO")
    print("=" * 60)
    print("  - Escribe un NÚMERO en kHz  -> ajusta la frecuencia del generador")
    print("    (ej: 260   ->  se manda como 260 kHz = 260000 Hz)")
    print("  - Escribe 'leer'            -> lee Vpp y desfase del osciloscopio")
    print("  - Escribe 'datos'           -> muestra la tabla guardada hasta ahora")
    print("  - Escribe 'salir'           -> guarda el CSV y termina")
    print("=" * 60)
    print(f"Frecuencia actual: {freq_actual_khz:.3f} kHz\n")

    while True:
        entrada = input(f"[{freq_actual_khz:.3f} kHz] Frecuencia (kHz) / 'leer' / 'datos' / 'salir' > ").strip()

        if entrada == "":
            continue

        if entrada.lower() in ("salir", "exit", "q"):
            break

        if entrada.lower() == "datos":
            if not datos:
                print("   (todavía no has guardado ningún punto)\n")
            else:
                print(f"\n{'Frecuencia (kHz)':>18} | {'Vpp CH_gen (V)':>15} | {'Vpp CH_med (V)':>15} | {'Desfase (°)':>12}")
                for d in datos:
                    print(f"{d['frecuencia_kHz']:>18} | {d['vpp_generador_V']:>15} | {d['vpp_medida_V']:>15} | {d['desfase_deg']:>12}")
                print()
            continue

        if entrada.lower() == "leer":
            vpp_gen = scope.measure_peak_to_peak(canal_scope_gen)
            vpp_med = scope.measure_peak_to_peak(canal_scope_medida)
            desfase = scope.measure_phase(canal_scope_gen, canal_scope_medida)

            print(f"   → Vpp CH{canal_scope_gen} (generador): {vpp_gen:.4f} V")
            print(f"   → Vpp CH{canal_scope_medida} (medida):    {vpp_med:.4f} V")
            print(f"   → Desfase: {desfase:.2f}°")

            ultima_lectura = {
                "frecuencia_kHz": round(freq_actual_khz, 3),
                "vpp_generador_V": round(vpp_gen, 4),
                "vpp_medida_V": round(vpp_med, 4),
                "desfase_deg": round(desfase, 2),
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }

            confirmar = input("   ¿Guardar este punto? (s/n) > ").strip().lower()
            if confirmar == "s":
                datos.append(ultima_lectura)
                print("   💾 Punto guardado.\n")
            else:
                print("   Punto descartado.\n")
            continue

        # Si no es 'leer', 'datos' ni 'salir' -> intentamos interpretarlo como frecuencia en kHz
        try:
            freq_khz = float(entrada.replace(",", "."))
            gen.set_frequency_khz(freq_khz)
            freq_actual_khz = freq_khz
            print(f"   ✅ Generador ajustado a {freq_khz:.3f} kHz ({freq_khz*1000:.1f} Hz)\n")
        except ValueError:
            print("   ⚠️  No entendí ese valor. Escribe un número (kHz), 'leer', 'datos' o 'salir'.\n")

    return datos


# ============================================================
#   GUARDAR CSV
# ============================================================
def guardar_csv(datos, ruta_salida: str = None):
    if not datos:
        print("No hay datos guardados, no se genera CSV.")
        return
    if ruta_salida is None:
        ruta_salida = f"caracterizacion_piezo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(ruta_salida, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(datos[0].keys()))
        writer.writeheader()
        writer.writerows(datos)
    print(f"💾 Datos guardados en: {ruta_salida}")


# ============================================================
#   MAIN
# ============================================================
if __name__ == "__main__":
    # Ajusta estos puertos según tu sistema (revisa con: ls /dev/usbtmc*)
    PUERTO_OSCILOSCOPIO = "/dev/usbtmc0"
    PUERTO_GENERADOR = "/dev/usbtmc1"

    CANAL_GENERADOR_SALIDA = 1   # canal físico del AFG1022 que estás usando
    CANAL_SCOPE_GEN = 1          # canal del osciloscopio conectado a la salida del generador
    CANAL_SCOPE_MEDIDA = 2       # canal del osciloscopio conectado a la caída en la resistencia

    scope = TektronixScope(PUERTO_OSCILOSCOPIO)
    gen = AFG1022(PUERTO_GENERADOR, canal=CANAL_GENERADOR_SALIDA)

    if scope.connect() and gen.connect():
        if prechequeo(scope, gen, CANAL_SCOPE_GEN, CANAL_SCOPE_MEDIDA):
            datos = modo_interactivo(scope, gen, CANAL_SCOPE_GEN, CANAL_SCOPE_MEDIDA)
            guardar_csv(datos)
        else:
            print("No se inició el proceso. Revisa los puntos marcados arriba.")

        scope.disconnect()
        gen.disconnect()
    else:
        print("No se pudo conectar a uno de los dos equipos. Revisa los puertos y permisos.")
