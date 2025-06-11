# ============================================
# IMPORTACIÓN DE MÓDULOS
# ============================================
import board
import busio
import digitalio

import adafruit_connection_manager
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socketpool
from adafruit_httpserver import Server, Request, Response, JSONResponse

# ============================================
# CONFIGURACIÓN ETHERNET
# ============================================
def configurar_ethernet():
    cs = digitalio.DigitalInOut(board.GP9)
    spi = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
    eth = WIZNET5K(spi, cs)
    return eth

# ============================================
# CONFIGURACIÓN SERVIDOR HTTP
# ============================================
def configurar_servidor(eth):
    pool = socketpool.SocketPool(eth)
    servidor = Server(pool, "/static", debug=True)
    return servidor

# ============================================
# RUTA: PÁGINA HTML
# ============================================
def definir_ruta_html(server):
    @server.route("/")
    def mostrar_pagina(request: Request):
        with open("/index.html", "r") as archivo:
            html = archivo.read()
        return Response(request, html.encode("utf-8"), content_type="text/html")

# ============================================
# RUTA: SLIDER (POST)
# ============================================
def definir_ruta_slider(server):
    @server.route("/slider", methods=["POST"])
    def manejar_slider(request: Request):
        datos = request.json()
        if datos and "valor" in datos:
            print(f"🎚️ Slider en: {datos['valor']}")
        return JSONResponse(request, {"ok": True})

# ============================================
# MAIN: INICIALIZACIÓN
# ============================================
def main():
    print("🌐 Inicializando Ethernet...")
    eth = configurar_ethernet()

    print("🖥️ Iniciando servidor...")
    server = configurar_servidor(eth)

    definir_ruta_html(server)
    definir_ruta_slider(server)

    ip = eth.pretty_ip(eth.ip_address)
    print("✅ Servidor activo en:", ip)
    server.serve_forever(str(ip))

main()


