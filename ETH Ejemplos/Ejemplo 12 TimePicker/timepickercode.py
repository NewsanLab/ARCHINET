# ======================== IMPORTACIONES ========================
import board
import busio
import digitalio
import neopixel
import adafruit_connection_manager
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socketpool
from adafruit_httpserver import Server, Request, Response, JSONResponse
from adafruit_pixel_framebuf import PixelFramebuffer


# ======================== MATRIZ OPCIONAL ========================
def configurar_matriz():
    pixeles = neopixel.NeoPixel(board.NEOPIXEL, 64, brightness=0.2, auto_write=False)
    matriz = PixelFramebuffer(pixeles, 8, 8, alternating=False)
    return matriz


# ======================== RED Y SERVIDOR ========================
def configurar_red():
    cs = digitalio.DigitalInOut(board.GP9)
    spi_bus = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
    eth = WIZNET5K(spi_bus, cs)
    pool = socketpool.SocketPool(eth)
    server = Server(pool, "/static", debug=True)
    return eth, server


# ======================== CARGAR HTML ========================
def manejar_html(request: Request) -> Response:
    with open("/index.html", "r") as f:
        html = f.read()
    return Response(request, html.encode("utf-8"), content_type="text/html")


# ======================== PROCESAR FECHA Y HORA ========================
def manejar_hora(request: Request) -> JSONResponse:
    data = request.json()
    datetime_str = data.get("datetime", "")
    print("Fecha y hora recibidas:", datetime_str)
    return JSONResponse(request, {"ok": True})



# ======================== PROGRAMA PRINCIPAL ========================
def main():
    matriz = configurar_matriz()  # Si no querés usar matriz, podés comentar esta línea
    eth, server = configurar_red()

    @server.route("/")
    def root(request: Request):
        return manejar_html(request)

    @server.route("/hora", methods=["POST"])
    def recibir_hora(request: Request):
        return manejar_hora(request)

    print("Servidor en:", eth.pretty_ip(eth.ip_address))
    server.serve_forever(str(eth.pretty_ip(eth.ip_address)))


# ======================== EJECUCIÓN ========================
main()
