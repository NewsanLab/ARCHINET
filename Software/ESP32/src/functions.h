#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include <Arduino.h>
#include <WebServer.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ===================== Interrupciones =====================
void IRAM_ATTR onResetSignalHigh();

// ===================== HTTP handlers =====================
void handleRoot();
void handleHtmlPart(const JsonDocument &doc);

// ===================== Access Point =====================
void startAccessPoint(const String &ssid, const String &pass);
void stopAccessPoint();

// ===================== Endpoints =====================
int findEndpoint(const String &ep);
void setEndpointData(const String &ep, const String &jsonData);
void handleDynamic();

// ===================== HTTP Requests =====================
void handleHttpGet(const String &url);
void handleHttpPost(const String &url, const String &jsonPayload);

// ===================== Señal READY =====================
void sendReadySignal();

// ===================== Escaneo WiFi =====================
void scanNetworks();

// ===================== Conexión WiFi =====================
void connectToWiFi(const String &ssid, const String &pass);
void disconnectWiFi();

#endif
