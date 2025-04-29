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
# ESTADO DEL SWITCH
# =============================
estado_switch = {"encendido": True}

# =============================
# RUTA HTML PRINCIPAL
# =============================
@server.route("/")
def pagina_switch(request: Request):
    with open("/index.html", "r") as file:
        contenido_html = file.read()
    return Response(request, contenido_html.encode("utf-8"), content_type="text/html")
# =============================
# RUTA PARA CAMBIAR ESTADO
# =============================
@server.route("/toggle", methods=["POST"])
def cambiar_estado(request: Request):
    datos = request.json()
    estado_switch["encendido"] = datos.get("encendido", False)
    print("Nuevo estado:", "ENCENDIDO" if estado_switch["encendido"] else "APAGADO")
    return JSONResponse(request, {"estado": estado_switch["encendido"]})

# =============================
# INICIAR SERVIDOR
# =============================
print("Iniciando servidor en:", eth.pretty_ip(eth.ip_address))
server.serve_forever(str(eth.pretty_ip(eth.ip_address)))
