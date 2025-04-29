# ============================================
# IMPORTAR MÓDULOS
# ============================================
import board
import busio
import digitalio

from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socketpool
from adafruit_httpserver import Server, Request, Response, JSONResponse

# ============================================
# CONFIGURAR ETHERNET
# ============================================
def configurar_ethernet():
    cs = digitalio.DigitalInOut(board.GP9)
    spi = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
    eth = WIZNET5K(spi, cs)
    return eth

# ============================================
# CONFIGURAR SERVIDOR
# ============================================
def configurar_servidor(eth):
    pool = socketpool.SocketPool(eth)
    server = Server(pool, "/static", debug=True)
    return server

# ============================================
# RUTAS
# ============================================
def rutas(server):
    @server.route("/")
    def index(request: Request):
        with open("/index.html", "r") as archivo:
            contenido = archivo.read()
        return Response(request, contenido.encode("utf-8"), content_type="text/html")

    @server.route("/mensaje", methods=["POST"])
    def recibir_mensaje(request: Request):
        datos = request.json()
        if datos and "texto" in datos:
            print("📩 Mensaje recibido:", datos["texto"])
        return JSONResponse(request, {"ok": True})

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================
def main():
    eth = configurar_ethernet()
    server = configurar_servidor(eth)
    rutas(server)

    ip = eth.pretty_ip(eth.ip_address)
    print("🟢 Servidor escuchando en:", ip)
    server.serve_forever(str(ip))

main()