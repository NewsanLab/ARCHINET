/*
 * Proyecto: Comunicación ESP32 - RP2040
 * Descripción: Este programa gestiona la conexión WiFi y la comunicación UART entre el ESP32 y un RP2040.
 * Autor: A.S
 * Fecha: 8-08-2025
 */
// ======== Librerias ================================================================================== //
#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "globals.h"
#include "functions.h"
#include "commandHandler.h"
const size_t BUF_SIZE = 1024;

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