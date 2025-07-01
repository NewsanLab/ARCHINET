# ARCHINET
Archi Net es una placa de desarrollo diseñada para facilitar la conectividad mediante WiFi, Ethernet y Bluetooth Low Energy (BLE). Cuenta con 4 entradas analógicas y 7 entradas/salidas digitales.

El diseño está pensado para que todas las funciones puedan ser programadas y controladas directamente desde el microcontrolador ARCHI (basado en RP2040), sin necesidad de programar el ESP32 por separado. Este actúa como un coprocesador de comunicaciones, operando mediante comandos enviados en formato Json.


## Especificaciones

## Diagrama en Bloques 

## Fuente de alimentación

## Uso de Pines
---

# 💻 Software

## Conexión a Ethernet

Para realizar una conexión por medio de Ethernet se deben tener cargadas las siguientes librerías en la carpeta `CIRCUITPY/lib`:

- `Adafruit_Bus_Device`
- `Adafruit_Wiznet5K`
- `Adafruit_Connection_Manager`
- `Adafruit_Requests`
- `Adafruit_Ticks`

### ⚙️ Configuración de pines

- **SPI**:
  - `SCK` → `GP10`
  - `MOSI` → `GP11`
  - `MISO` → `GP12`
  - `Chip Select (CS)` → `GP9`

###  Prueba de conexión inicial con ETHERNET

Este script permite comprobar que el dispositivo se conecta correctamente a la red mediante Ethernet.

### ¿Qué hace el script?

1. Configura el bus SPI y el pin CS.
2. Inicializa el módulo Ethernet `WIZNET5K`.
3. Crea una sesión HTTP con `adafruit_requests`.
4. Muestra:
   - Versión del chip
   - Dirección MAC
   - Dirección IP asignada

## Ejemplo: Consulta de IP por Ethernet

<a href="https://github.com/NewsanLab/ARCHINET/blob/main/Software/Example/Ethernet/Ejemplo%201%20Consulta%20IP/01.py" target="_blank" style="text-decoration:none; padding:6px 12px; background-color:#0366d6; color:white; border-radius:6px; font-weight:bold;"> Ver código completo en GitHub</a>

###  Fragmento del código 
```python
import board
import busio
import digitalio
import adafruit_connection_manager
import adafruit_requests
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K

spi = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
cs = digitalio.DigitalInOut(board.GP9)
eth = WIZNET5K(spi, cs)

pool = adafruit_connection_manager.get_radio_socketpool(eth)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(eth)
requests = adafruit_requests.Session(pool, ssl_context)

print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))

```
## ESP32 como Coprocesador (modo UART)

El ESP32 se utiliza como coprocesador encargado de gestionar la conexión WiFi. La comunicación entre el microcontrolador principal (ej. RP2040, Archi u otros) y el ESP32 se realiza mediante UART o SPI, mediante el envío de **comandos en formato JSON**.



---

###  Modos de operación

- **UART**: Se comunica a través de pines TX/RX, usando comandos y respuestas JSON.
- **SPI**: Alternativamente, se puede implementar una versión basada en SPI (no cubierta en este ejemplo, pero compatible).

---

## 📶 Conexión WiFi vía UART

Este ejemplo muestra cómo controlar el ESP32 como coprocesador para conectarse a una red WiFi mediante UART.

### Conceptos clave

- Comunicación UART entre el microcontrolador principal y el ESP32.
- El pin `ready` indica cuándo el ESP32 está disponible para recibir comandos.
- Uso de JSON para enviar comandos como `CONNECT`, `SCAN`, `STATUS`, etc.
- Reset físico al ESP32 para asegurar un arranque limpio.

---

### ⚙️ Configuración de pines

| Función        | Pin GPIO |
|----------------|----------|
| UART TX        | GP12     |
| UART RX        | GP13     |
| Pin `ready`    | GP10     |
| Pin `reset`    | GP11     |

---

### ¿Qué hace el script?

1. Reinicia el ESP32 con un pulso en el pin `reset`.
2. Espera la señal `ready` del ESP32.
3. Envía el comando `CONNECT` con SSID y contraseña.
4. Recibe las respuestas en formato JSON.
5. Finaliza cuando se recibe `{"end": true}` desde el ESP32.

---

###  Ejemplo: Primera conexión a la red

<a href="https://github.com/NewsanLab/ARCHINET/blob/main/Software/Example/WiFi/Conectar%20a%20WiFi/code.py" target="_blank" style="text-decoration:none; padding:6px 12px; background-color:#0366d6; color:white; border-radius:6px; font-weight:bold;"> Ver código completo en GitHub</a>

### Fragmento del código

```python
esp = ESP32UART(tx_pin=board.GP12, rx_pin=board.GP13, ready_pin=board.GP10)

if esp.esperar_ready(timeout=10):
    esp.solicitar_comando({"cmd": "CONNECT", "ssid": "tu_ssid", "pass": "tu_password"})
    esp.leer_respuesta(timeout=20)
else:
    print("ESP32 no está listo.")

```
---

### 📋 Lista de comandos

| Comando       | Parámetros                      | Descripción                                                                 | 📄 Código de ejemplo                                                                 |
|---------------|----------------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| `SCAN`        | *(ninguno)*                     | Escanea y lista redes WiFi disponibles.                                    | [🔗 Ver ejemplo](https://github.com/NewsanLab/ARCHINET/blob/main/Software/Example/WiFi/Escanear/code.py)          |
| `CONNECT`     | `ssid`, `pass`                  | Conecta a una red WiFi específica.                                         | [🔗 Ver ejemplo](https://github.com/NewsanLab/ARCHINET/blob/main/Software/Example/WiFi/Conectar%20a%20WiFi/code.py)       |
| `DISCONNECT`  | `target` (`"WiFi"` o `"AP"`)    | Desconecta de la red o cierra el punto de acceso.                          | [🔗 Ver ejemplo](https://github.com/NewsanLab/ARCHINET/blob/main/Software/Example/WiFi/Desconectar%20Red/code.py)    |
| `AP`          | `ssid`, `pass`                  | Crea un punto de acceso (Access Point).                                    | [🔗 Ver ejemplo](https://github.com/NewsanLab/ARCHINET/blob/main/Software/Example/WiFi/Conectar%20a%20AP/code.py)            |
| `PING`        | *(ninguno)*                     | Verifica si el ESP32 está activo y responde con su IP.                     | [🔗 Ver ejemplo](https://github.com/NewsanLab/ARCHINET/blob/main/Software/Example/WiFi/Informaci%C3%B3n%20de%20conexi%C3%B3n/code.py)          |
| `INFO`        | *(ninguno)*                     | Devuelve información del sistema: IP, RSSI y memoria disponible.           | [🔗 Ver ejemplo](https://github.com/NewsanLab/ARCHINET/blob/main/Software/Example/WiFi/Informaci%C3%B3n%20de%20conexi%C3%B3n/code.py)          |
| `GET`         | `url`                           | Realiza una petición HTTP GET a la URL indicada.                           | [🔗 Ver ejemplo](https://github.com/NewsanLab/ARCHINET/blob/main/Software/Example/WiFi/Consulta%20GET/code.py)           |
| `POST`        | `url`, `data`                   | Envía datos mediante HTTP POST (JSON) a la URL especificada.               | [🔗 Ver ejemplo](https://github.com/NewsanLab/ARCHINET/blob/main/Software/Example/WiFi/Consulta%20POST/code.py)          |
| `WebServer`   | `label`, `data`                 | Crea o actualiza un endpoint en el servidor embebido del ESP32.            | [🔗 Ver ejemplo](https://github.com/NewsanLab/ARCHINET/blob/main/Software/Example/WiFi/WebServer-API-WiFi/code.py)     |
| `HTML`        | `html`                          | Inyecta HTML personalizado en el servidor web embebido.                    | [🔗 Ver ejemplo](https://github.com/NewsanLab/ARCHINET/blob/main/Software/Example/WiFi/A%C3%B1adir%20HTML/codehtml.py)          |
