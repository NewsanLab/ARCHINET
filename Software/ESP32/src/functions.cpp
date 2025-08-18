#include <Arduino.h>
#include "globals.h"
#include "functions.h"
// ================================= Manejador de interrupción para RESET =================================
void IRAM_ATTR onResetSignalHigh()
{
    esp_restart(); // Reinicia el ESP32
}
// ================================================= Manejadores HTTP ======================================
void handleRoot()
{
    server.send(200, "text/html", htmlPage);
}

void handleHtmlPart(const JsonDocument &doc)
{
    int index = doc["index"] | -1;
    int total = doc["total"] | -1;
    String content = doc["content"] | "";

    if (index < 0 || total < 1 || content.length() == 0)
    {
        UART1.println("[ESP32] Datos HTML_PART inválidos.");
        UART1.println("{\"end\": true}");
        return;
    }

    if (index == 0)
    {
        // Primer fragmento: inicializar buffer y contadores
        htmlBuffer = "";
        expectedTotalParts = total;
        receivedParts = 0;
        Serial.printf("[ESP32] Inicio recepción HTML en %d fragmentos\n", total);
    }

    // Validar orden correcto de fragmentos
    if (index != receivedParts)
    {
        UART1.printf("[ESP32] Fragmento fuera de orden: esperado %d, recibido %d\n", receivedParts, index);
        UART1.println("{\"end\": true}");
        return;
    }

    // Concatenar fragmento al buffer
    htmlBuffer += content;
    receivedParts++;

    // UART1.printf("[ESP32] Recibido fragmento %d/%d\n", index + 1, total);

    // Cuando llegan todos los fragmentos, actualizo la página HTML
    if (receivedParts == expectedTotalParts)
    {
        htmlPage = htmlBuffer;
        // Serial.println("[ESP32] HTML actualizado con todos los fragmentos recibidos.");
        UART1.println("[ESP32] HTML actualizado");
        expectedTotalParts = 0;
        receivedParts = 0;
    }

    UART1.println("{\"end\": true}");
}

// ========================== Funciones para gestionar el Access Point (AP) =============================

// Inicia el Access Point con el SSID y la contraseña proporcionados
void startAccessPoint(const String &ssid, const String &pass)
{

    bool result = WiFi.softAP(ssid.c_str(), pass.c_str());

    if (result)
    {
        IPAddress IP = WiFi.softAPIP();
        UART1.printf("[ESP32] AP iniciado: %s | IP: %s\n", ssid.c_str(), IP.toString().c_str());
        UART1.println("{\"end\": true}");
    }
    else
    {
        UART1.println("[ESP32] Error al iniciar AP");
        UART1.println("{\"end\": true}");
    }
}
// Detiene el Access Point si está activo
void stopAccessPoint()
{
    WiFi.softAPdisconnect(true);
    UART1.println("[ESP32] AP detenido");
    UART1.println("{\"end\": true}");
}

//===============================End POINT=======================================================

// Busca endpoint, devuelve índice o -1 si no existe
int findEndpoint(const String &ep)
{
    for (int i = 0; i < endpointCount; i++)
    {
        if (endpoints[i].endpoint == ep)
            return i;
    }
    return -1;
}

//=========================================Solicitud GET ==========================================

void handleHttpGet(const String &url)
{
    if (WiFi.status() != WL_CONNECTED)
    {
        UART1.println("[ESP32] No conectado a WiFi, no se puede hacer GET.");
        UART1.println("{\"end\": true}"); //

        return;
    }

    HTTPClient http;
    http.begin(url);

    int httpCode = http.GET();
    if (httpCode > 0)
    {
        UART1.printf("[ESP32] GET %s -> Código: %d\n", url.c_str(), httpCode);
        String payload = http.getString(); // Obtener todo el contenido de la respuesta
        payload.trim();                    // Eliminar espacios o saltos al principio o final

        // Imprimir TODO el contenido en UNA SOLA LÍNEA (sin saltos de línea)
        payload.replace("\n", " ");
        payload.replace("\r", " ");

        UART1.print(payload);
        UART1.println(); // Solo un salto de línea final
    }
    else
    {
        UART1.printf("[ESP32] Error en GET -> Código: %d\n", httpCode);
    }

    http.end();
    UART1.println("{\"end\": true}"); //
}
//================================ Solicitud POST ======================================================
void handleHttpPost(const String &url, const String &jsonPayload)
{
    if (WiFi.status() != WL_CONNECTED)
    {
        UART1.println("[ESP32] No conectado a WiFi, no se puede hacer POST.");
        UART1.println("{\"end\": true}");
        return;
    }

    HTTPClient http;
    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    int httpCode = http.POST(jsonPayload);

    if (httpCode > 0)
    {
        UART1.printf("[ESP32] POST %s -> Código: %d\n", url.c_str(), httpCode);
        String response = http.getString();
        response.replace("\n", " ");
        response.replace("\r", " ");
        UART1.print(response);
        UART1.println();
    }
    else
    {
        UART1.printf("[ESP32] Error en POST -> Código: %d\n", httpCode);
    }

    http.end();
    UART1.println("{\"end\": true}");
}

//================================ Manejo dinámico de endpoint==========================================
void handleDynamic()
{
    String path = server.uri(); // ej. "/Temperatura" o utro (:)
    if (path.startsWith("/"))
        path = path.substring(1); // quito /

    int idx = findEndpoint(path);
    if (idx >= 0)
    {
        server.send(200, "application/json", endpoints[idx].jsonData);
    }
    else
    {
        server.send(404, "text/plain", "No encontrado");
    }
}

// Actualiza o agrega un endpoint con JSON
void setEndpointData(const String &ep, const String &jsonData)
{
    int idx = findEndpoint(ep);
    if (idx >= 0)
    {
        endpoints[idx].jsonData = jsonData;
    }
    else if (endpointCount < MAX_ENDPOINTS)
    {
        endpoints[endpointCount].endpoint = ep;
        endpoints[endpointCount].jsonData = jsonData;
        endpointCount++;
    }
    else
    {
        Serial.println("[ESP32] No hay espacio para nuevos endpoints");
    }
}

//==================================================Ready=================================================

void sendReadySignal()
{
    pinMode(READY_PIN, OUTPUT);
    digitalWrite(READY_PIN, LOW);
    delay(100);
    digitalWrite(READY_PIN, HIGH);
    Serial.println("[ESP32] READY_PIN en HIGH (listo para recibir)");
}

//===================================================SCAN===================================================

void scanNetworks()
{
    UART1.println("[ESP32] Escaneando redes WiFi...");
    int n = WiFi.scanNetworks();

    if (n <= 0)
    {
        UART1.println("[ESP32] No se encontraron redes WiFi.");
    }
    else
    {
        String ssids[50]; // Arreglo para almacenar SSIDs únicos
        int uniqueCount = 0;

        for (int i = 0; i < n; i++)
        {
            String currentSSID = WiFi.SSID(i);
            bool esRepetido = false;
            // Verificar si ya se agregó
            for (int j = 0; j < uniqueCount; j++)
            {
                if (ssids[j] == currentSSID)
                {
                    esRepetido = true;
                    break;
                }
            }
            if (!esRepetido && currentSSID.length() > 0)
            {
                ssids[uniqueCount++] = currentSSID;
                UART1.printf("SSID: %s | RSSI: %d\n", currentSSID.c_str(), WiFi.RSSI(i));
            }
        }
    }

    WiFi.scanDelete(); // Limpiar memoria
    Serial.println("[ESP32] Escaneo terminado.");
    UART1.println("{\"end\": true}"); // fin de carrera
}
//================================================Connect a WIFI ======================================================

void connectToWiFi(const String &ssid, const String &pass)
{
    // UART1.printf("[ESP32] Intentando conectar a: %s\n", ssid.c_str());

    WiFi.disconnect(true); // Borrar configuraciones anteriores
    WiFi.begin(ssid.c_str(), pass.c_str());

    unsigned long startAttemptTime = millis();
    const unsigned long timeout = 10000; // 10 segundos

    while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < timeout)
    {
        delay(500);
        // UART1.print(".");
    }

    if (WiFi.status() == WL_CONNECTED)
    {
        // UART1.println("\n[ESP32] Conexión WiFi exitosa.");
        // UART1.printf("[ESP32] IP: %s\n", WiFi.localIP().toString().c_str());
        UART1.printf("[ESP32] OK|IP: %s\n", WiFi.localIP().toString().c_str());
        UART1.println("{\"end\": true}"); // fin de carrera
    }
    else
    {
        UART1.printf("\n[ESP32] Error al conectar a la red: %s\n", ssid.c_str());
        UART1.println("{\"end\": true}"); // fin de carrera
    }
}

// Deconexion de WIFI actual
void disconnectWiFi()
{
    if (WiFi.status() == WL_CONNECTED)
    {
        WiFi.disconnect(true);
        UART1.println("[ESP32] WiFi desconectado.");
        UART1.println("{\"end\": true}");
    }
    else
    {
        UART1.println("[ESP32] No está conectado a ninguna red.");
        UART1.println("{\"end\": true}");
    }
}
