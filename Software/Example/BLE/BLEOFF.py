import time
import board
import busio
import digitalio
import json

# Clase que gestiona la comunicación UART con el ESP32
class ESP32UART:
    def __init__(self, tx_pin, rx_pin, ready_pin, baudrate=115200, timeout=0.1):
        # Inicializa la UART con pines TX y RX, velocidad y timeout configurables
        self.uart = busio.UART(tx=tx_pin, rx=rx_pin, baudrate=baudrate, timeout=timeout)

        self.ready_pin = digitalio.DigitalInOut(ready_pin)
        self.ready_pin.direction = digitalio.Direction.INPUT
        self.ready_pin.pull = digitalio.Pull.DOWN

    def esperar_ready(self, timeout=5):
     
        inicio = time.monotonic()
        while time.monotonic() - inicio < timeout:
            if self.ready_pin.value:
                return True  # ESP32 listo
            time.sleep(0.01)  
        return False  

    def solicitar_comando(self, comando_dict):

        mensaje = json.dumps(comando_dict) + "\n"  # Delimitador '\n' para lectura por línea
        self.uart.write(mensaje.encode())  # Envía bytes por UART

    def leer_respuesta(self, timeout=5):

        buffer = b""
        inicio = time.monotonic()
        while time.monotonic() - inicio < timeout:
            data = self.uart.read(64)  # Lee hasta 64 bytes disponibles
            if data:
                buffer += data
                while b'\n' in buffer:
                    linea, buffer = buffer.split(b'\n', 1)
                    try:
                        texto = linea.decode().strip()
                    except Exception:
                        texto = "<error decoding>"

                    if texto:
                        try:
                            json_obj = json.loads(texto)
                            # Fin de respuesta si recibe un JSON con {"end": true}
                            if isinstance(json_obj, dict) and json_obj.get("end") is True:
                                return
                        except Exception:
                            pass  # No es JSON, se imprime igual
                        print(texto)

        # Si quedó algo sin \n, intentar mostrarlo también
        if buffer:
            try:
                texto = buffer.decode().strip()
            except Exception:
                texto = "<error decoding>"
            if texto:
                print("Respuesta parcial:", texto)

def main():
    # --- Reset físico del ESP32 ---
    reset_pin = digitalio.DigitalInOut(board.GP15)
    reset_pin.direction = digitalio.Direction.OUTPUT
    print("Reiniciando ESP32-S3...")
    reset_pin.value = True
    time.sleep(0.1)
    reset_pin.value = False
    time.sleep(0.1)
    reset_pin.value = True
    time.sleep(1)
    reset_pin.deinit()

    # Inicializa la clase ESP32UART con los pines específicos para TX, RX y ready
    esp = ESP32UART(tx_pin=board.GP12, rx_pin=board.GP13, ready_pin=board.GP14)

    # Espera que el ESP32 indique que está listo para comunicarse
    if not esp.esperar_ready(timeout=10):
        print("ESP32 no está listo.")
        return

    #Inicia BLE->Con el siguiente comando por defecto tiene el nombre de ARCHINET_BLEXX 
    print("\n--- TEST: CONNECT BLE---")
    esp.solicitar_comando({"cmd": "BLEINIT"})
    esp.leer_respuesta(timeout=20)

    conteo= 0
    while (True and conteo<20): #mandamos 20 despues desactivamos 
        esp.solicitar_comando({"cmd": "BLETX","data": "{pcb:archinet, version:v2}"})
        esp.solicitar_comando({"cmd": "BLERX"})
        esp.leer_respuesta(timeout=15)
        conteo= conteo +1
        time.sleep(1) 
    esp.solicitar_comando({"cmd": "BLEOFF"})
    esp.leer_respuesta(timeout=20)
    esp.solicitar_comando({"cmd": "SCAN"})
    esp.leer_respuesta(timeout=20)
    

if __name__ == "__main__":
    main()