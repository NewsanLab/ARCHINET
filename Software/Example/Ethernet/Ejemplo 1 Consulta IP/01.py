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
# INICIALIZAR SESIÓN REQUESTS
# ================================
def crear_sesion_requests(eth):
    """Crea una sesión de requests usando adafruit_connection_manager"""
    pool = adafruit_connection_manager.get_radio_socketpool(eth)
    ssl_context = adafruit_connection_manager.get_radio_ssl_context(eth)
    return adafruit_requests.Session(pool, ssl_context)


# ================================
# MOSTRAR INFORMACIÓN DE RED
# ================================
def mostrar_info_red(eth):
    """Muestra información del chip, MAC, IP, y resolución DNS"""
    print("Chip Version:", eth.chip)
    print("MAC Address:", [hex(i) for i in eth.mac_address])
    print("My IP address is:", eth.pretty_ip(eth.ip_address))


# ================================
# FUNCIÓN PRINCIPAL
# ================================
def main():
    print("Wiznet5k WebClient Test")

    # Configurar hardware
    spi_bus, cs = configurar_spi_cs()

    # Inicializar Ethernet
    eth = inicializar_ethernet(spi_bus, cs)

    # Crear sesión de requests
    requests = crear_sesion_requests(eth)

    # Mostrar información de red
    mostrar_info_red(eth)

    # eth._debug = True  # Descomentar si deseas ver más logs


# ================================
# PUNTO DE ENTRADA
# ================================
if __name__ == "__main__":
    main()

