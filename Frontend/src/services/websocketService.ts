import { API_WS_BASE_URL } from '../config';

type MessageHandler = (data: any) => void;

export const websocketService = {
  createDeviceTimeLeftSocket: (deviceId: number, onMessage: MessageHandler): WebSocket => {
    const ws = new WebSocket(`${API_WS_BASE_URL}/device/ws/timeleft/${deviceId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };
    
    ws.onerror = (error) => {
      console.error(`WebSocket error for device ${deviceId}:`, error);
    };
    
    ws.onclose = () => {
      console.log(`WebSocket closed for device ${deviceId}`);
    };
    
    return ws;
  },
  
  createDeviceStatusSocket: (deviceId: number, onMessage: MessageHandler): WebSocket => {
    const ws = new WebSocket(`${API_WS_BASE_URL}/device/ws/status/${deviceId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };
    
    ws.onerror = (error) => {
      console.error(`WebSocket error for device ${deviceId}:`, error);
    };
    
    ws.onclose = () => {
      console.log(`WebSocket closed for device ${deviceId}`);
    };
    
    return ws;
  },
  
  closeWebSocket: (ws: WebSocket): void => {
    if (ws && ws.readyState !== WebSocket.CLOSED) {
      ws.close();
    }
  }
};