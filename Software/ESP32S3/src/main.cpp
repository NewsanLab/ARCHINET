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

// Definición de pines
#define MOSI_PIN 11
#define MISO_PIN 13
#define SCK_PIN 12
#define CS_PIN 10


#define SPI_BUFFER_LEN SPI_MAX_DMA_LEN

uint8_t* commandBuffer;   // Puntero para el buffer de comandos
uint8_t* responseBuffer;  // Puntero para el buffer de respuestas

const char* mensajeInicial = "mensaje enviar"; // Mensaje inicial
void newmensaje(char* newMesj);
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
    
    // Verificar que la asignación fue exitosa
    if (!commandBuffer || !responseBuffer) {
        Serial.println("Error al asignar memoria para los buffers.");
        while (1);
    }

    size_t mensajeLength = strlen(mensajeInicial);
    memcpy(commandBuffer, mensajeInicial, mensajeLength); // Copia el mensaje inicial al buffer de comandos
    commandBuffer[mensajeLength] = '\0'; 
}

void loop() {
    // Transferir el commandBuffer y recibir la respuesta en responseBuffer
    int longitudRecibida = SPIS.transfer(commandBuffer, responseBuffer, strlen((const char*)commandBuffer));

    String mensajeRecibido = "";
    for (int i = 0; i < longitudRecibida; i++) {
        mensajeRecibido += (char)responseBuffer[i]; 
    }

    Serial.printf("Mensaje enviado: %s\n", commandBuffer);
    Serial.printf("Mensaje recibido: %s\n", mensajeRecibido.c_str()); 

    if (strcmp(mensajeRecibido.c_str(), "COMANDO1") == 0) {
        Serial.println("activando 1 ");
        newmensaje("modificado ");

    } else if (strcmp(mensajeRecibido.c_str(), "COMANDO2") == 0) {
        Serial.println("activando 2 ");
        newmensaje("modificado mensaje por segunda vez");
    } else {
        Serial.println("Comando no reconocido");
    }

}
void newmensaje(char* newMesj){
        const char* nuevoMensaje2 = newMesj;
        size_t nuevoMensaje2Length = strlen(nuevoMensaje2);
        
        if (nuevoMensaje2Length < SPI_BUFFER_LEN) {
            memcpy(commandBuffer, nuevoMensaje2, nuevoMensaje2Length); 
            commandBuffer[nuevoMensaje2Length] = '\0'; 
        }
}
void cleanup() {
    free(commandBuffer);
    free(responseBuffer);
}
