# ================================
# IMPORTACIONES
# ================================
import time
import board
import busio
import digitalio

import adafruit_connection_manager
import adafruit_requests
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K


# ================================
# CONSTANTES
# ================================
JSON_POST_URL = "http://httpbin.org/post"
DATA_A_ENVIAR = "31F"


# ================================
# CONFIGURACIÓN DE HARDWARE
# ================================
def configurar_spi_cs():
    """Configura el bus SPI y el pin CS para el WIZnet5K"""
    cs = digitalio.DigitalInOut(board.GP9)
    spi_bus = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
    return spi_bus, cs


# ================================
# INICIALIZAR ETHERNET
# ================================
def inicializar_ethernet(spi_bus, cs):
    """Inicializa la interfaz Ethernet usando WIZNET5K"""
    return WIZNET5K(spi_bus, cs)


# ================================
# SESIÓN DE REQUESTS
# ================================
def crear_sesion_requests(eth):
    """Crea una sesión de requests usando adafruit_connection_manager"""
    pool = adafruit_connection_manager.get_radio_socketpool(eth)
    ssl_context = adafruit_connection_manager.get_radio_ssl_context(eth)
    return adafruit_requests.Session(pool, ssl_context)


# ================================
# PETICIÓN POST
# ================================
def enviar_dato_post(requests, url, data):
    """Envía un dato como POST a una URL y muestra la respuesta"""
    print(f"POSTing data to {url}: {data}")
    with requests.post(url, data=data) as response:
        print("-" * 40)
        json_resp = response.json()
        print("Data received from server:", json_resp["data"])
        print("-" * 40)


# ================================
# FUNCIÓN PRINCIPAL
# ================================
def main():
    print("Wiznet5k WebClient Test")

    # Inicialización de hardware y red
    spi_bus, cs = configurar_spi_cs()
    eth = inicializar_ethernet(spi_bus, cs)
    requests = crear_sesion_requests(eth)

    # Enviar POST
    enviar_dato_post(requests, JSON_POST_URL, DATA_A_ENVIAR)


# ================================
# PUNTO DE ENTRADA
# ================================
if __name__ == "__main__":
    main()
