/*
 * Proyecto: Comunicación ESP32 - RP2040
 * Descripción: Este programa gestiona la conexión WiFi y la comunicación UART entre el ESP32 y un RP2040.
 * Autor: A.S
 * Fecha: 1-06-2025
 */
// ======== Librerias ================================================================================== //
#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
bool uartEnabled = true; // Variable global para estado UART

// ======== Definición de pines ======================================================================== //

#define RESET_SIGNAL_PIN GPIO_NUM_0 // Pin para enviar señal de reinicio
#define TXD_PIN 10                  // TX del ESP32 (hacia RX del otro dispositivo)
#define RXD_PIN 13                  // RX del ESP32 (desde TX del otro dispositivo)
#define READY_PIN GPIO_NUM_48       // Pin para recibir señal de "listo" desde el otro dispositivo

#define BUF_SIZE 1024 // Tamaño del buffer para comunicaciones UART

// =========================================== UART y Web Server ===========================================
HardwareSerial UART1(2); // UART2 para comunicación con RP2040
WebServer server(80);    // Servidor en el puerto 80

// Variables globales para manejar fragmentos HTML
String htmlPage = "<h1> ArchiNET </h1>"; // HTML por defecto
String htmlBuffer = "";
int expectedTotalParts = 0;
int receivedParts = 0;

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

struct EndpointData
{
  String endpoint;
  String jsonData;
};

#define MAX_ENDPOINTS 10 // modificable
EndpointData endpoints[MAX_ENDPOINTS];
int endpointCount = 0;

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

//=======================================Lista de commandos =================================================

void handleCommand(const String &cmd)
{
  Serial.printf("[ESP32] Procesando comando: %s\n", cmd.c_str());

  // Verificar si parece un JSON
  if (cmd.startsWith("{") && cmd.endsWith("}"))
  {
    StaticJsonDocument<4096> doc;
    DeserializationError error = deserializeJson(doc, cmd);
    if (error)
    {
      UART1.printf("[ESP32] Error al parsear JSON: %s\n", error.c_str());
      return;
    }

    String command = doc["cmd"] | "";
    if (command == "SCAN")
    {
      scanNetworks();
    }
    else if (command == "CONNECT")
    {
      String ssid = doc["ssid"] | "";
      String pass = doc["pass"] | "";
      if (ssid != "" && pass != "")
      {
        connectToWiFi(ssid, pass);
      }
      else
      {
        UART1.println("[ESP32] Falta SSID o PASS en CONNECT.");
      }
    }
    else if (command == "DISCONNECT")
    {
      String target = doc["target"] | "WiFi";
      if (target == "WiFi")
      {
        disconnectWiFi();
      }
      else if (target == "AP")
      {
        stopAccessPoint();
      }
    }
    else if (command == "AP")
    {
      String ssid = doc["ssid"] | "";
      String pass = doc["pass"] | "";
      if (ssid != "" && pass != "")
      {
        startAccessPoint(ssid, pass);
        // UART1.println("{\"end\": true}");
      }
      else
      {
        UART1.println("[ESP32] Faltan datos para AP");
        UART1.println("{\"end\": true}");
      }
    }
    else if (command == "PING")
    {
      IPAddress ip;
      if (WiFi.getMode() == WIFI_AP || WiFi.getMode() == WIFI_AP_STA)
        ip = WiFi.softAPIP();
      else
        ip = WiFi.localIP();

      UART1.println("[ESP32] PING recibido. Estoy activo.");
      UART1.printf("[ESP32] IP actual: %s\n", ip.toString().c_str());
      UART1.println("{\"end\": true}");
    }

    else if (command == "POST")
    {
      String url = doc["url"] | "";
      String payload;
      if (doc.containsKey("data"))
      {
        serializeJson(doc["data"], payload);
      }
      if (url != "" && payload != "")
      {
        handleHttpPost(url, payload);
      }
      else
      {
        UART1.println("[ESP32] POST mal formado: falta 'url' o 'data'");
        UART1.println("{\"end\": true}");
      }
    }
    if (command == "WebServer")
    {
      int mode = WiFi.getMode();
      if (!(WiFi.status() == WL_CONNECTED || mode == WIFI_AP || mode == WIFI_AP_STA))
      {
        UART1.println("[ESP32] No se puede crear endpoint. No conectado a WiFi ni en modo AP.");
        return;
      }

      String ep = doc["label"] | ""; // aquí el nombre del endpoint viene en "label"
      if (ep == "")
      {
        UART1.println("[ESP32] Comando WebServer mal formado: falta 'label'");
        return;
      }

      // Para obtener el objeto JSON en "data" y convertirlo a string
      JsonObject dataObj = doc["data"].as<JsonObject>();
      String jsonData;
      if (!dataObj.isNull())
      {
        // Serializar dataObj a string JSON
        serializeJson(dataObj, jsonData);
      }
      else
      {
        jsonData = "{}";
      }

      setEndpointData(ep, jsonData);
      UART1.printf("[ESP32] Endpoint /%s actualizado\n", ep.c_str());
      UART1.println("{\"end\": true}");
    }
    else if (command == "GET")
    {
      String url = doc["url"] | "";
      if (url != "")
        handleHttpGet(url);
    }
    else if (command == "INFO")
    {
      IPAddress ip;
      if (WiFi.getMode() == WIFI_AP || WiFi.getMode() == WIFI_AP_STA)
        ip = WiFi.softAPIP();
      else
        ip = WiFi.localIP();

      UART1.printf("{\"chip\":\"ESP32-S3\",\"ip\":\"%s\",\"rssi\":%d,\"heap\":%d}\n",
                   ip.toString().c_str(), WiFi.RSSI(), ESP.getFreeHeap());
      UART1.println("{\"end\": true}");
    }
    if (command == "UART_OFF")
    {
      if (uartEnabled)
      {
        UART1.println("[ESP32] UART apagado."); // mensaje para apagar
        UART1.println("{\"end\": true}");
        UART1.flush(); // esperar a que se envíe todo
        UART1.end();   // cierra el puerto UART
        uartEnabled = false;
      }
      else
      {
        Serial.println("[ESP32] UART ya estaba apagado."); // debug en Serial
      }
    }
    else if (command == "UART_ON")
    {
      if (!uartEnabled)
      {
        UART1.begin(115200, SERIAL_8N1, RXD_PIN, TXD_PIN); // Reabre UART
        uartEnabled = true;
        UART1.println("[ESP32] UART encendido.");
        UART1.println("{\"end\": true}");
      }
      else
      {
        UART1.println("[ESP32] UART ya estaba encendido.");
        UART1.println("{\"end\": true}");
      }
    }

    /* else if (command == "HTML")
     {
       if (doc.containsKey("html"))
       {
         String html = doc["html"].as<String>();
         if (html.length() > 0)
         {
           htmlPage = html;
           UART1.println("[ESP32] HTML actualizado");
         }
         else
         {
           UART1.println("[ESP32] Campo 'html' vacío.");
         }
       }
       else
       {
         UART1.println("[ESP32] No se encontró el campo 'html'.");
       }
       UART1.println("{\"end\": true}");
     }*/
    else if (command == "HTML")
    {
      handleHtmlPart(doc);
    }

    return;
  }

  UART1.println("[ESP32] Comando no reconocido (no JSON y no clásico).");
}
//=================================SETUP & LOOP ============================================================
void setup()
{
  Serial.begin(115200); // Debug
  UART1.begin(115200, SERIAL_8N1, RXD_PIN, TXD_PIN);
  pinMode(RESET_SIGNAL_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(RESET_SIGNAL_PIN), onResetSignalHigh, RISING);
  sendReadySignal();
  WiFi.mode(WIFI_AP_STA);
  server.onNotFound(handleDynamic);
  server.on("/", handleRoot);
  server.begin();
  delay(100);
  Serial.println("[ESP32] Setup completado.");
}

void loop()
{
  static char buffer[BUF_SIZE];
  static size_t index = 0;

  while (UART1.available() > 0)
  {
    char c = UART1.read();
    if (c == '\n' || c == '\r')
    {
      buffer[index] = '\0';
      String cmd(buffer);
      cmd.trim();
      if (!cmd.isEmpty())
      {
        handleCommand(cmd);
      }
      index = 0;
    }
    else
    {
      if (index < BUF_SIZE - 1)
      {
        buffer[index++] = c;
      }
    }
  }
  server.handleClient();
}