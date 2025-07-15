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

        # Configura el pin 'ready_pin' como entrada digital con resistencia Pull-Down
        # Este pin se usa para detectar cuándo el ESP32 está listo para comunicarse
        self.ready_pin = digitalio.DigitalInOut(ready_pin)
        self.ready_pin.direction = digitalio.Direction.INPUT
        self.ready_pin.pull = digitalio.Pull.DOWN

    def esperar_ready(self, timeout=5):
        """
        Espera hasta que el pin 'ready_pin' se ponga en alto, indicando que el ESP32 está listo.
        Si no se activa dentro del timeout, devuelve False.
        """
        inicio = time.monotonic()
        while time.monotonic() - inicio < timeout:
            if self.ready_pin.value:
                return True  # ESP32 listo
            time.sleep(0.01)  
        return False  

    def solicitar_comando(self, comando_dict):
        """
        Envía un comando JSON al ESP32, serializado y terminado con salto de línea.
        """
        mensaje = json.dumps(comando_dict) + "\n"  # Delimitador '\n' para lectura por línea
        self.uart.write(mensaje.encode())  # Envía bytes por UART

    def leer_respuesta(self, timeout=5):
        """
        Lee respuestas UART hasta timeout o hasta recibir un mensaje JSON con {"end": true}.
        Maneja buffers parciales y decodifica línea por línea.
        """
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
    # Se reinicia el ESP32 para que no queden tareas previas o estados inconsistentes.
    reset_pin = digitalio.DigitalInOut(board.GP15)
    reset_pin.direction = digitalio.Direction.OUTPUT
    print("Reiniciando ESP32-S3...")

    # Pulso de reset: alto - bajo - alto, con pausas para asegurar que se registre
    reset_pin.value = True
    time.sleep(0.1)
    reset_pin.value = False
    time.sleep(0.1)
    reset_pin.value = True
    time.sleep(1)  # Espera a que el ESP32 arranque completamente
    reset_pin.deinit()  # Libera el pin para evitar consumo o interferencias

    # Inicializa la clase ESP32UART con los pines específicos para TX, RX y ready
    esp = ESP32UART(tx_pin=board.GP12, rx_pin=board.GP13, ready_pin=board.GP14)

    # Espera que el ESP32 indique que está listo para comunicarse
    if not esp.esperar_ready(timeout=10):
        print("ESP32 no está listo.")
        return

    # Enviar comando para conectar a WiFi (reemplazar ssid y pass por los reales)
    print("\n--- TEST: CONNECT ---")
    esp.solicitar_comando({"cmd": "CONNECT", "ssid": "xxx", "pass": "xxx"})
    esp.leer_respuesta(timeout=15)

    # Realiza un PING para ver si esta activa la conexión, lanza la ip actual
    print("\n ---------TEST:PING------------")
    esp.solicitar_comando({"cmd":"PING"})
    esp.leer_respuesta(timeout=50)

    # Muestra la informacion del CHIP, IP , Nivel de la red , RAM
    print("\n ---TEST:INFO---------------")
    esp.solicitar_comando({"cmd": "INFO"})
    esp.leer_respuesta(timeout=50)
   

if __name__ == "__main__":
    main()

