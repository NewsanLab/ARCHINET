#ifndef GLOBALS_H
#define GLOBALS_H

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>

// === Pines ===
extern const gpio_num_t RESET_SIGNAL_PIN;
extern const int TXD_PIN;
extern const int RXD_PIN;
extern const gpio_num_t READY_PIN;

extern const size_t BUF_SIZE;

// === UART y Web Server ===
extern HardwareSerial UART1;
extern WebServer server;
extern bool uartEnabled;

// === Fragmentos HTML ===
extern String htmlPage;
extern String htmlBuffer;
extern int expectedTotalParts;
extern int receivedParts;

// === Endpoints ===
struct EndpointData {
  String endpoint;
  String jsonData;
};

extern const int MAX_ENDPOINTS;
extern EndpointData endpoints[];
extern int endpointCount;

#endif
