import time
import board
import busio
import digitalio
import json

# Clase que maneja la comunicación UART con el ESP32
class ESP32UART:
    def __init__(self, tx_pin, rx_pin, ready_pin, baudrate=115200, timeout=0.1):
        # Inicializa UART con pines de transmisión y recepción
        self.uart = busio.UART(tx=tx_pin, rx=rx_pin, baudrate=baudrate, timeout=timeout)

        # Pin para detectar si el ESP32 está listo 
        self.ready_pin = digitalio.DigitalInOut(ready_pin)
        self.ready_pin.direction = digitalio.Direction.INPUT
        self.ready_pin.pull = digitalio.Pull.DOWN 

    def esperar_ready(self, timeout=5):
        """Espera hasta que el ESP32 indique que está listo o se agote el tiempo."""
        inicio = time.monotonic()
        while time.monotonic() - inicio < timeout:
            if self.ready_pin.value:
                return True  # ESP32 indicó que está listo
            time.sleep(0.01) 
        return False  
        
    def solicitar_comando(self, comando_dict):
        """Envía un comando en formato JSON por UART al ESP32."""
        mensaje = json.dumps(comando_dict) + "\n"  # Agrega \n como delimitador de mensajes
        self.uart.write(mensaje.encode())  # Envia el mensaje por UART

    def leer_respuesta(self, timeout=5):
        """Lee las respuestas del ESP32, línea por línea, hasta que se indique fin."""
        buffer = b""
        inicio = time.monotonic()
        while time.monotonic() - inicio < timeout:
            data = self.uart.read(64)  
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
                            # Si se recibe {"end": true}, se da por terminada la respuesta
                            if isinstance(json_obj, dict) and json_obj.get("end") is True:
                                return
                        except Exception:
                            pass  # No es JSON, pero igual puede imprimirse
                        print(texto)  # Muestra la respuesta

        # Si quedó algo en buffer sin \n al final, intentar decodificarlo igual
        if buffer:
            try:
                texto = buffer.decode().strip()
            except Exception:
                texto = "<error decoding>"
            if texto:
                print("Respuesta parcial:", texto)


def main():
    # --- Reset físico del ESP32 ---
    # Esto asegura que se reinicie antes de iniciar la comunicación,
    # evitando que queden tareas anteriores colgadas o el sistema en estado inestable.
    reset_pin = digitalio.DigitalInOut(board.GP11)
    reset_pin.direction = digitalio.Direction.OUTPUT
    print("Reiniciando ESP32-S3...")

    # Pulso de reset: primero lo dejamos alto (activo), luego bajo (reset), luego alto otra vez
    reset_pin.value = True
    time.sleep(0.1)
    reset_pin.value = False
    time.sleep(0.1)
    reset_pin.value = True
    time.sleep(1)  # Esperamos a que el ESP32 arranque
    reset_pin.deinit()  # Liberamos el pin

    # --- Inicializar UART con pines definidos ---
    esp = ESP32UART(tx_pin=board.GP12, rx_pin=board.GP13, ready_pin=board.GP10)

    # --- Esperar a que el ESP32 indique que está listo ---
    if not esp.esperar_ready(timeout=10):
        print("ESP32 no está listo.")
        return

    # --- Enviar comando de escaneo ---
    print("\n--- TEST: SCAN ---")
    esp.solicitar_comando({"cmd": "SCAN"})
    esp.leer_respuesta(timeout=50) 



if __name__ == "__main__":
    main()
