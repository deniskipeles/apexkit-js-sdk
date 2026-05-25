package com.apexkit.sdk;

import com.google.gson.Gson;
import okhttp3.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.HashMap;

public class ApexKitRealtimeWSClient {
    private String url;
    private OkHttpClient client;
    private WebSocket webSocket;
    private Gson gson;
    private List<OnEventListener> listeners;

    public interface OnEventListener {
        void onEvent(Map<String, Object> event);
    }

    public ApexKitRealtimeWSClient(String baseUrl, String token) {
        this.url = baseUrl.replace("http", "ws").replaceAll("/$", "") + "/ws";
        this.client = new OkHttpClient();
        this.gson = new Gson();
        this.listeners = new ArrayList<>();
    }

    public void connect() {
        Request request = new Request.Builder().url(url).build();
        webSocket = client.newWebSocket(request, new WebSocketListener() {
            @Override
            public void onMessage(WebSocket webSocket, String text) {
                Map<String, Object> msg = gson.fromJson(text, Map.class);
                for (OnEventListener listener : listeners) {
                    listener.onEvent(msg);
                }
            }
        });
    }

    public void subscribe(Map<String, Object> filter) {
        Map<String, Object> msg = new HashMap<>();
        msg.put("type", "Subscribe");
        msg.put("payload", filter);
        webSocket.send(gson.toJson(msg));
    }

    public void onEvent(OnEventListener listener) {
        listeners.add(listener);
    }

    public void disconnect() {
        if (webSocket != null) {
            webSocket.close(1000, "Goodbye");
        }
    }
}
