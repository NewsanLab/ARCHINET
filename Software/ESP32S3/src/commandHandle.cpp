#include "Arduino.h"
#include "main.h"
#include "FS.h"
#include "WiFi.h"

//respuesta -> Formato Json response: | datacommand | 

String scanNetwork(){
    String scanNetwork="";
    int n = WiFi.scanNetworks();
    for (int i = 0; i < 3; ++i) {
        scanNetwork = scanNetwork + String(i+1) + ": " + String(WiFi.SSID(i)) + "( " + String(WiFi.RSSI(i))+")" + String((WiFi.encryptionType(i) == WIFI_AUTH_OPEN)?" ":"*");
        delay(10);
    }
    return scanNetwork;
}

String apNetwork(char* ssid, char* password){

    if(WiFi.softAP(ssid, password) != WL_CONNECTED){
        return "AP creada";
    }else{
        return "error en crear AP";
    };
}

String connectAp(char* SSID, char* PASSWORD){
    
    WiFi.begin(SSID, PASSWORD);
    Serial.print("Conectando a WiFi");
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
        }

    return "Conectado AP" ;
}

String getRequest(char* request, boolean type){

}

String postRequest(char* request, boolean type){

}
String ipConfig(){

}
String ipResult(){

}

void commandWifi(String command){
    String send = "";
    if (strcmp(command.c_str(), "COMANDO1") == 0) {
        
        send= apNetwork("unidad", "123456789");
        response(send.c_str());
    
    } else if (strcmp(command.c_str(), "COMANDO2") == 0) {
        send = scanNetwork();
        const char* cts = send.c_str();
        response(cts);
        delay(20);
    } else if (strcmp(command.c_str(),"COMANDO3")==0){
        send = connectAp("iPhone de Angela","angie088");
        response(send.c_str());

    } else {
        Serial.println("Comando no reconocido");
    }
    
}