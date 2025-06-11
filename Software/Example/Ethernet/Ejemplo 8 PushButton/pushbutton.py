# ============================================
# IMPORTACIÓN DE MÓDULOS NECESARIOS
# ============================================
import board
import busio
import digitalio

import adafruit_connection_manager
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socketpool
from adafruit_httpserver import Server, Request, Response, JSONResponse

# ============================================
# CONFIGURACIÓN DE HARDWARE Y RED ETHERNET
# ============================================

def configurar_ethernet():
    cs = digitalio.DigitalInOut(board.GP9)  # Pin CS del W5500
    spi_bus = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)  # SPI para W5500
    wiznet = WIZNET5K(spi_bus, cs)  # Crear objeto de red
    return wiznet

# ============================================
# CONFIGURACIÓN DEL SERVIDOR HTTP
# ============================================

def configurar_servidor(eth):
    pool = socketpool.SocketPool(eth)
    servidor = Server(pool, "/static", debug=True)
    return servidor

# ============================================
# RUTA PRINCIPAL PARA SERVIR EL HTML
# ============================================

def definir_ruta_html(servidor):
    @servidor.route("/")
    def pagina_principal(request: Request):
        with open("/index.html", "r") as archivo:
            contenido = archivo.read()
        return Response(request, contenido.encode("utf-8"), content_type="text/html")

# ============================================
# RUTA PARA RECIBIR EL EVENTO DE PULSACIÓN
# ============================================

def definir_ruta_push(servidor):
    @servidor.route("/push", methods=["POST"])
    def manejar_pulsacion(request: Request):
        datos = request.json()
        if datos and datos.get("presionado", False):
            print("🔘 Botón presionado desde el navegador.")
        return JSONResponse(request, {"ok": True})

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def main():
    print("Inicializando Ethernet...")
    eth = configurar_ethernet()
    
    print("Configurando servidor HTTP...")
    servidor = configurar_servidor(eth)
    
    # Registrar rutas
    definir_ruta_html(servidor)
    definir_ruta_push(servidor)
    
    # Iniciar servidor
    ip = eth.pretty_ip(eth.ip_address)
    print("🌐 Servidor iniciado en:", ip)
    servidor.serve_forever(str(ip))

# ============================================
# EJECUCIÓN DEL PROGRAMA
# ============================================
main()

