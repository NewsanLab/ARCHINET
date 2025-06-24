import time
import board
import busio
import digitalio
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
                        try:
                            json_obj = json.loads(texto)
                            if isinstance(json_obj, dict) and json_obj.get("end") is True:
                                return
                        except Exception:
                            pass
                        print(texto)
        if buffer:
            try:
                texto = buffer.decode().strip()
            except Exception:
                texto = "<error decoding>"
            if texto:
                print("Respuesta parcial:", texto)

def enviar_html_fragmentado(esp, html, fragment_size=512):
    total = (len(html) + fragment_size - 1) // fragment_size
    for i in range(total):
        fragment = html[i*fragment_size:(i+1)*fragment_size]
        cmd = {
            "cmd": "HTML",
            "index": i,
            "total": total,
            "content": fragment
        }
        esp.solicitar_comando(cmd)
        esp.leer_respuesta(timeout=10)

def main():
    # --- Reset del ESP32 usando GP11 ---
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

    if not esp.esperar_ready(timeout=10):
        print("ESP32 no está listo.")
        return

    print("\n--- TEST: CONNECT ---")
    esp.solicitar_comando({"cmd": "CONNECT", "ssid": "NS-Guest-USH", "pass": "visitanewsan05"})
    esp.leer_respuesta(timeout=15)
    
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        print(f"No se pudo leer el archivo index.html: {e}")
        return

    print("\n--- TEST: HTML PARTES ---")
    enviar_html_fragmentado(esp, html)
    

if __name__ == "__main__":
    main()


