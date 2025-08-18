#include "commandHandler.h"
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include "globals.h"
#include "functions.h"
// === Pines ===
const gpio_num_t RESET_SIGNAL_PIN = GPIO_NUM_0;
const int TXD_PIN = 10;
const int RXD_PIN = 13;
const gpio_num_t READY_PIN = GPIO_NUM_48;


// === UART y Web Server ===
HardwareSerial UART1(2);
WebServer server(80);
bool uartEnabled = true; // Variable global para estado UART
// === Fragmentos HTML ===
String htmlPage = "<h1> ArchiNET </h1>";
String htmlBuffer = "";
int expectedTotalParts = 0;
int receivedParts = 0;

// === Endpoints ===
const int MAX_ENDPOINTS = 10;
EndpointData endpoints[MAX_ENDPOINTS];
int endpointCount = 0;

void handleCommand(const String &cmd)
{
  Serial.printf("[ESP32] Procesando comando: %s\n", cmd.c_str());

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
        disconnectWiFi();
      else if (target == "AP")
        stopAccessPoint();
    }
    else if (command == "AP")
    {
      String ssid = doc["ssid"] | "";
      String pass = doc["pass"] | "";
      if (ssid != "" && pass != "")
      {
        startAccessPoint(ssid, pass);
      }
      else
      {
        UART1.println("[ESP32] Faltan datos para AP");
        UART1.println("{\"end\": true}");
      }
    }
    else if (command == "PING")
    {
      IPAddress ip = (WiFi.getMode() == WIFI_AP || WiFi.getMode() == WIFI_AP_STA)
                         ? WiFi.softAPIP()
                         : WiFi.localIP();

      UART1.println("[ESP32] PING recibido. Estoy activo.");
      UART1.printf("[ESP32] IP actual: %s\n", ip.toString().c_str());
      UART1.println("{\"end\": true}");
    }
    else if (command == "POST")
    {
      String url = doc["url"] | "";
      String payload;
      if (doc.containsKey("data"))
        serializeJson(doc["data"], payload);

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
    else if (command == "WebServer")
    {
      int mode = WiFi.getMode();
      if (!(WiFi.status() == WL_CONNECTED || mode == WIFI_AP || mode == WIFI_AP_STA))
      {
        UART1.println("[ESP32] No se puede crear endpoint. No conectado a WiFi ni en modo AP.");
        return;
      }

      String ep = doc["label"] | "";
      if (ep == "")
      {
        UART1.println("[ESP32] Comando WebServer mal formado: falta 'label'");
        return;
      }

      JsonObject dataObj = doc["data"].as<JsonObject>();
      String jsonData;
      if (!dataObj.isNull())
      {
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
      IPAddress ip = (WiFi.getMode() == WIFI_AP || WiFi.getMode() == WIFI_AP_STA)
                         ? WiFi.softAPIP()
                         : WiFi.localIP();

      UART1.printf("{\"chip\":\"ESP32-S3\",\"ip\":\"%s\",\"rssi\":%d,\"heap\":%d}\n",
                   ip.toString().c_str(), WiFi.RSSI(), ESP.getFreeHeap());
      UART1.println("{\"end\": true}");
    }
    else if (command == "UART_OFF")
    {
      if (uartEnabled)
      {
        UART1.println("[ESP32] UART apagado.");
        UART1.println("{\"end\": true}");
        UART1.flush();
        UART1.end();
        uartEnabled = false;
      }
      else
      {
        Serial.println("[ESP32] UART ya estaba apagado.");
      }
    }
    else if (command == "UART_ON")
    {
      if (!uartEnabled)
      {
        UART1.begin(115200, SERIAL_8N1, RXD_PIN, TXD_PIN);
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
    else if (command == "HTML")
    {
      handleHtmlPart(doc);
    }

    return;
  }

  UART1.println("[ESP32] Comando no reconocido (no JSON y no clásico).");
}
