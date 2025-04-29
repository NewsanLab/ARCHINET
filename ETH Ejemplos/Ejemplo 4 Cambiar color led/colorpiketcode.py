# ======================== IMPORTACIÓN DE MÓDULOS ========================
import board
import busio
import digitalio
import neopixel
import adafruit_connection_manager
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socketpool
from adafruit_httpserver import Server, Request, Response, JSONResponse
from adafruit_pixel_framebuf import PixelFramebuffer


# ======================== BLOQUE: CONFIGURACIÓN DE MATRIZ ========================
def configurar_matriz():
    pixeles = neopixel.NeoPixel(board.NEOPIXEL, 64, brightness=0.2, auto_write=False)
    matriz = PixelFramebuffer(pixeles, 8, 8, alternating=False)
    return matriz


# ======================== BLOQUE: CONFIGURACIÓN DE RED ========================
def configurar_red():
    cs = digitalio.DigitalInOut(board.GP9)
    spi_bus = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
    eth = WIZNET5K(spi_bus, cs)
    pool = socketpool.SocketPool(eth)
    server = Server(pool, "/static", debug=True)
    return eth, server


# ======================== BLOQUE: RESPUESTA CON HTML ========================
def manejar_html(request: Request) -> Response:
    with open("/index.html", "r") as f:
        html = f.read()
    return Response(request, html.encode("utf-8"), content_type="text/html")


# ======================== BLOQUE: CAMBIAR COLOR DE MATRIZ ========================
def aplicar_color_a_matriz(hex_color: str, matriz):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    for y in range(8):
        for x in range(8):
            matriz.pixel(x, y, (r, g, b))
    matriz.display()
    print(f"Color actualizado: {r}, {g}, {b}")


# ======================== BLOQUE: MANEJADOR DE RUTA COLOR ========================
def ruta_color(request: Request, matriz) -> JSONResponse:
    data = request.json()
    hex_color = data.get("color", "#000000")
    aplicar_color_a_matriz(hex_color, matriz)
    return JSONResponse(request, {"ok": True})


# ======================== BLOQUE PRINCIPAL ========================
def main():
    matriz = configurar_matriz()
    eth, server = configurar_red()

    # Ruta para cargar HTML
    @server.route("/")
    def root(request: Request):
        return manejar_html(request)

    # Ruta POST para aplicar color
    @server.route("/color", methods=["POST"])
    def post_color(request: Request):
        return ruta_color(request, matriz)

    print("Servidor en:", eth.pretty_ip(eth.ip_address))
    server.serve_forever(str(eth.pretty_ip(eth.ip_address)))


# ======================== INICIO DEL PROGRAMA ========================
main()