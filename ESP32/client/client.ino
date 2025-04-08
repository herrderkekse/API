#include <WebSocketsClient.h>
#include "secrets.h"
WebSocketsClient webSocket;

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  if (type == WStype_TEXT) {
    Serial.printf("Received: %s\n", payload);
  }
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, wifi_psw);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.print("\n successfully connected to ");
  Serial.println(ssid);

  webSocket.begin(server_ip, 8000, "/ws");
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);
}
void loop() {
  webSocket.loop();
  webSocket.sendTXT("Hello from ESP32");
  delay(5000);
}
