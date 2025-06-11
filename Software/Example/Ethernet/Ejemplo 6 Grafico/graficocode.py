import board
import busio
import digitalio
import random
import json
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socketpool
from adafruit_httpserver import Server, Request, Response

# Configuración del hardware para Adafruit Ethernet FeatherWing
cs = digitalio.DigitalInOut(board.GP9)
spi_bus = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)

# Inicializa la interfaz Ethernet con DHCP
eth = WIZNET5K(spi_bus, cs)

# Crea un socket pool
pool = socketpool.SocketPool(eth)

# Inicializa el servidor HTTP
server = Server(pool, "/static", debug=True)

@server.route("/")
def serve_temperature_page(request: Request):
    """
    Sirve una página HTML que actualiza dinámicamente los valores de temperatura y muestra un gráfico más grande.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Temperatura en Tiempo Real</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 20px;
            }
            .temperature {
                font-size: 2em;
                color: #007BFF;
            }
            canvas {
                margin: 30px auto;
                display: block;
                max-width: 800px;
                max-height: 400px;
                width: 90%;
                height: auto;
            }
        </style>
    </head>
    <body>
        <h1>Temperatura en Tiempo Real</h1>
        <p class="temperature" id="temperature">Cargando...</p>
        <canvas id="temperatureChart" style="width: 100%; height: 500px;"></canvas>
        <script>
            const ctx = document.getElementById('temperatureChart').getContext('2d');
            const temperatureChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [], // Etiquetas del eje X (tiempo)
                    datasets: [{
                        label: 'Temperatura (°C)',
                        data: [], // Valores del eje Y (temperatura)
                        borderColor: 'rgba(0, 123, 255, 1)',
                        backgroundColor: 'rgba(0, 123, 255, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Tiempo'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Temperatura (°C)'
                            },
                            min: 0,
                            max: 50
                        }
                    }
                }
            });

            function fetchTemperature() {
                fetch('/temperature')
                    .then(response => response.json())
                    .then(data => {
                        // Actualiza el valor de temperatura en la página
                        document.getElementById('temperature').textContent = data.temperature + " °C";

                        // Añade nuevos datos al gráfico
                        const now = new Date().toLocaleTimeString();
                        temperatureChart.data.labels.push(now);
                        temperatureChart.data.datasets[0].data.push(data.temperature);

                        // Mantén un máximo de 10 puntos en el gráfico
                        if (temperatureChart.data.labels.length > 10) {
                            temperatureChart.data.labels.shift();
                            temperatureChart.data.datasets[0].data.shift();
                        }

                        // Actualiza el gráfico
                        temperatureChart.update();
                    })
                    .catch(error => {
                        console.error('Error al obtener la temperatura:', error);
                    });
            }

            // Actualizar la temperatura cada 2 segundos
            setInterval(fetchTemperature, 2000);
            // Obtener la temperatura al cargar la página
            fetchTemperature();
        </script>
    </body>
    </html>
    """
    return Response(request, html_content.encode("utf-8"), content_type="text/html")


@server.route("/temperature")
def serve_temperature_data(request: Request):
    """
    Devuelve un valor de temperatura aleatorio en formato JSON.
    """
    temperature = round(random.uniform(20.0, 30.0), 2)
    temperature_data = json.dumps({"temperature": temperature})
    return Response(request, temperature_data.encode("utf-8"), content_type="application/json")

# Inicia el servidor indefinidamente
print("Iniciando servidor en:", eth.pretty_ip(eth.ip_address))
server.serve_forever(str(eth.pretty_ip(eth.ip_address)))

