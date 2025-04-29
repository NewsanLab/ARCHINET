import board
import busio
import digitalio
import adafruit_connection_manager
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socketpool
from adafruit_httpserver import Server, Request, Response, JSONResponse

# =============================
# CONFIGURACIÓN DE ETHERNET
# =============================
cs = digitalio.DigitalInOut(board.GP9)
spi_bus = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
eth = WIZNET5K(spi_bus, cs)
pool = socketpool.SocketPool(eth)
server = Server(pool, "/static", debug=True)

# =============================
# RUTA HTML PRINCIPAL
# =============================
@server.route("/")
def pagina_switch(request: Request):
    with open("/index.html", "r") as file:
        contenido_html = file.read()
    return Response(request, contenido_html.encode("utf-8"), content_type="text/html")

# =============================
# INICIAR SERVIDOR
# =============================
print("Iniciando servidor en:", eth.pretty_ip(eth.ip_address))
server.serve_forever(str(eth.pretty_ip(eth.ip_address)))