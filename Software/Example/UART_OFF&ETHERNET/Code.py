import time
import board
import busio
import digitalio
import json

# Librerías WIZnet
import adafruit_connection_manager
import adafruit_requests
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K

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

    def cerrar(self):
        # Libera el UART
        if hasattr(self.uart, 'deinit'):
            self.uart.deinit()

def reiniciar_ESP():
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

def main():
    reiniciar_ESP()

    esp = ESP32UART(tx_pin=board.GP12, rx_pin=board.GP13, ready_pin=board.GP14)

    if not esp.esperar_ready(timeout=10):
        print("ESP32 no está listo.")
        return

    print("\n--- Comando: SCAN ---")
    esp.solicitar_comando({"cmd": "SCAN"})
    esp.leer_respuesta(timeout=10)
    #cerras el uart ESP32, se puede probar los ejemplos de ethernet 
    #para usar nuevamente el UART reiniciar ESP32 
    print("\n--- Comando: UART_OFF ---")
    esp.solicitar_comando({"cmd": "UART_OFF"})
    esp.leer_respuesta(timeout=10)

    #  libera el UART para usar GP12 como MISO SPI #
    esp.cerrar()

    #  inicializamos el SPI con GP12 como MISO
    spi = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
    cs = digitalio.DigitalInOut(board.GP9)

    eth = WIZNET5K(spi, cs)
    pool = adafruit_connection_manager.get_radio_socketpool(eth)
    ssl_context = adafruit_connection_manager.get_radio_ssl_context(eth)
    requests = adafruit_requests.Session(pool, ssl_context)

    print("Chip Version:", eth.chip)
    print("MAC Address:", [hex(i) for i in eth.mac_address])
    print("My IP address is:", eth.pretty_ip(eth.ip_address))

if __name__ == "__main__":
    main()
