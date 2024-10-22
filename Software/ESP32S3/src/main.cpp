#include <Arduino.h>
#include <driver/gpio.h>
#include <driver/spi_slave.h>
#include "SPIS.h"
#include <rom/uart.h>
#include "WiFi.h"

extern "C" {
    #include <driver/periph_ctrl.h>
    #include <driver/uart.h>
    #include <driver/adc.h>
    #include <esp_bt.h>
}

#include "commandHandle.h"

// Definición de pines
#define MOSI_PIN 11
#define MISO_PIN 13
#define SCK_PIN 12
#define CS_PIN 10


#define SPI_BUFFER_LEN SPI_MAX_DMA_LEN

uint8_t* commandBuffer;   // Puntero para el buffer de comandos
uint8_t* responseBuffer;  // Puntero para el buffer de respuestas

const char* mensajeInicial = "iniciando_ESP32"; // Mensaje inicial
void response(char* res);

void setup() {
    Serial.begin(115200);

    // Inicializar el pin CS
    pinMode(CS_PIN, OUTPUT);
    digitalWrite(CS_PIN, HIGH); 

    // Control de inicio de SPI
    if (SPIS.begin() == 1) {
        Serial.println("SPI iniciado.");
    } else {
        Serial.println("Error al iniciar SPI.");
        while (1); 
    }

    // Asignar memoria para los buffers
    commandBuffer = (uint8_t*)malloc(SPI_BUFFER_LEN);
    responseBuffer = (uint8_t*)malloc(SPI_BUFFER_LEN);
    
    // Verificar que la asignación 
    if (!commandBuffer || !responseBuffer) {
        Serial.println("Error al asignar memoria para los buffers.");
        while (1);
    }
    // Copia el mensaje inicial al buffer de comandos
    size_t mensajeLength = strlen(mensajeInicial);
    memcpy(commandBuffer, mensajeInicial, mensajeLength); 
    commandBuffer[mensajeLength] = '\0'; 
}

void loop() {
    // Transferir el commandBuffer y recibir la respuesta en responseBuffer
    int longitudRecibida = SPIS.transfer(commandBuffer, responseBuffer, strlen((const char*)commandBuffer));
    String mensajeRecibido = "";
    for (int i = 0; i < longitudRecibida; i++) {
        mensajeRecibido += (char)responseBuffer[i]; 
    }
   //!serial ESP
  //  Serial.printf("Mensaje enviado: %s\n", commandBuffer);
  //  Serial.printf("Mensaje recibido: %s\n", mensajeRecibido.c_str()); 
    commandWifi(mensajeRecibido);

}

//Mensaje recibo por el Archi
void response(const char* res){
        const char* respuesta = res;
        size_t len_response = strlen(respuesta);

        //Serial.println(len_response);
        
        if (len_response < SPI_BUFFER_LEN) {
            memcpy(commandBuffer, respuesta, len_response); 
            commandBuffer[len_response] = '\0'; 
        }
}
void cleanup() {
    free(commandBuffer);
    free(responseBuffer);
}
