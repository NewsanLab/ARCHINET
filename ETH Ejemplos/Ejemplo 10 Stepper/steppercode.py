# ============================================
# IMPORTACIÓN DE MÓDULOS
# ============================================
import board
import busio
import digitalio

from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socketpool
from adafruit_httpserver import Server, Request, Response, JSONResponse

# ============================================
# CONFIGURACIÓN DE ETHERNET
# ============================================
def configurar_ethernet():
    cs = digitalio.DigitalInOut(board.GP9)
    spi = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
    eth = WIZNET5K(spi, cs)
    return eth

# ============================================
# CONFIGURACIÓN DE SERVIDOR
# ============================================
def configurar_servidor(eth):
    pool = socketpool.SocketPool(eth)
    server = Server(pool, "/static", debug=True)
    return server

# ============================================
# RUTA PRINCIPAL: HTML
# ============================================
def ruta_html(server):
    @server.route("/")
    def index(request: Request):
        with open("/index.html", "r") as archivo:
            contenido = archivo.read()
        return Response(request, contenido.encode("utf-8"), content_type="text/html")

# ============================================
# RUTA: VALOR DEL STEPPER
# ============================================
def ruta_stepper(server):
    @server.route("/stepper", methods=["POST"])
    def actualizar_valor(request: Request):
        datos = request.json()
        if datos and "valor" in datos:
            print(f"🔁 Stepper actualizado a: {datos['valor']}")
        return JSONResponse(request, {"ok": True})

# ============================================
# INICIO
# ============================================
def main():
    print("🌐 Configurando Ethernet...")
    eth = configurar_ethernet()

    print("🖥️ Iniciando servidor HTTP...")
    server = configurar_servidor(eth)

    ruta_html(server)
    ruta_stepper(server)

    ip = eth.pretty_ip(eth.ip_address)
    print("✅ Servidor corriendo en:", ip)
    server.serve_forever(str(ip))

main()
