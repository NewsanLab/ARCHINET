import time
import board
import busio
import digitalio
import random
import json

class ESP32UART:
    def __init__(self, tx_pin, rx_pin, ready_pin, baudrate=115200, timeout=0.1):
        self.uart = busio.UART(tx=tx_pin, rx=rx_pin, baudrate=baudrate, timeout=timeout)
        self.ready_pin = digitalio.DigitalInOut(ready_pin)
        self.ready_pin.direction = digitalio.Direction.INPUT
        self.ready_pin.pull = digitalio.Pull.DOWN

    def esperar_ready(self, timeout=5):
        inicio = time.monotonic()
        while time.monotonic() - inicio < timeout:
            if self.ready_pin.value:
                return True
            time.sleep(0.01)
        return False

    def solicitar_comando(self, comando_dict):
        mensaje = json.dumps(comando_dict) + "\n"
        self.uart.write(mensaje.encode())

    def leer_respuesta(self, timeout=5):
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
                        print(texto)
        if buffer:
            try:
                texto = buffer.decode().strip()
            except Exception:
                texto = "<error decoding>"
            if texto:
                print("Respuesta parcial:", texto)

def main():
    # --- Reset del ESP32 usando GP11 como pin temporal ---
    reset_pin = digitalio.DigitalInOut(board.GP11)
    reset_pin.direction = digitalio.Direction.OUTPUT
    print("Reiniciando ESP32-S3...")
    reset_pin.value = True
    time.sleep(0.1)
    reset_pin.value = False
    time.sleep(0.1)
    reset_pin.value = True
    time.sleep(1)
    reset_pin.deinit()

    esp = ESP32UART(tx_pin=board.GP12, rx_pin=board.GP13, ready_pin=board.GP10)

    html = """
    <html><head><style>
    body { background-color: #222; color: #fff; text-align: center; font-family: sans-serif; }
    h1 { color: #4CAF50; }
    </style></head><body><h1>Hola desde RP2040</h1></body></html>
    """

    if not esp.esperar_ready(timeout=10):
        print("ESP32 no está listo.")
        return

    # === PRUEBA DE COMANDOS ===

    print("\n--- TEST: SCAN ---")
    esp.solicitar_comando({"cmd": "SCAN"})
    esp.leer_respuesta(timeout=15)

    print("\n--- TEST: CONNECT ---")
    esp.solicitar_comando({"cmd": "CONNECT", "ssid": "xxxx", "pass": "xxxx"})
    esp.leer_respuesta(timeout=10)

    print("\n--- TEST: HTML ---")
    esp.solicitar_comando({"cmd": "HTML", "html": html})
    esp.leer_respuesta(timeout=5)

    print("\n--- TEST: GET (api) ---")
    esp.solicitar_comando({
        "cmd": "GET",
        "url": "http://wifitest.adafruit.com/testwifi/index.html"
    })
    esp.leer_respuesta(timeout=10)
    print("\n--- TEST: GET (api) ---")
    esp.solicitar_comando({
        "cmd": "GET",
        "url": "http://jsonplaceholder.typicode.com/todos/1"
    })
    esp.leer_respuesta(timeout=10)

    print("\n--- TEST: AP (crear punto de acceso) ---")
    esp.solicitar_comando({
        "cmd": "AP",
        "ssid": "RP2040_AP",
        "pass": "clave1234"
    })
    esp.leer_respuesta(timeout=5)

    print("\n--- TEST: DISCONNECT (WiFi) ---")
    esp.solicitar_comando({"cmd": "DISCONNECT", "target": "WiFi"})
    esp.leer_respuesta(timeout=3)

    print("\n--- TEST: DISCONNECT (AP) ---")
    esp.solicitar_comando({"cmd": "DISCONNECT", "target": "AP"})
    esp.leer_respuesta(timeout=3)
    print("\n--- TEST: CONNECT ---")
    esp.solicitar_comando({"cmd": "CONNECT", "ssid": "xxxx", "pass": "xxxx"})
    esp.leer_respuesta(timeout=10)

    print("\n--- INICIANDO ENVÍO PERIÓDICO ---")
    time.sleep(3)

    # === LOOP PERIÓDICO CON TEMPERATURA ===
    while True:
        if esp.esperar_ready(timeout=1):
            temperatura = round(random.uniform(20, 30), 1)
            esp.solicitar_comando({
                "cmd": "WebServer",
                "label": "Temperatura",
                "data": {"dato1": temperatura}
            })
            esp.leer_respuesta(timeout=2)
        else:
            print("ESP32 no listo.")
        time.sleep(5)

if __name__ == "__main__":
    main()
