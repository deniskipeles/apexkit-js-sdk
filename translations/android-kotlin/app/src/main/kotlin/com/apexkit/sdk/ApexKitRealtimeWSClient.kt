package com.apexkit.sdk

import com.google.gson.Gson
import okhttp3.*
import java.util.concurrent.TimeUnit

class ApexKitRealtimeWSClient(baseUrl: String, private val token: String?) {
    private val url = baseUrl.replace("http", "ws").removeSuffix("/") + "/ws"
    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .build()
    private var webSocket: WebSocket? = null
    private val gson = Gson()
    private val listeners = mutableListOf<(Map<String, Any>) -> Unit>()

    fun connect() {
        val request = Request.Builder().url(url).build()
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                val msg = gson.fromJson(text, Map::class.java) as Map<String, Any>
                listeners.forEach { it(msg) }
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(1000, null)
            }
        })
    }

    fun subscribe(filter: Map<String, Any>) {
        val msg = mapOf(
            "type" to "Subscribe",
            "payload" to mapOf(
                "collection_id" to filter["collectionId"],
                "record_id" to filter["recordId"],
                "event_type" to filter["eventType"],
                "filter" to filter["dataFilter"],
                "channel" to filter["channel"],
                "custom_event" to filter["customEvent"]
            )
        )
        webSocket?.send(gson.toJson(msg))
    }

    fun sendSignal(channel: String, event: String, data: Any) {
        val msg = mapOf(
            "type" to "Signal",
            "payload" to mapOf("channel" to channel, "event" to event, "data" to data)
        )
        webSocket?.send(gson.toJson(msg))
    }

    fun onEvent(listener: (Map<String, Any>) -> Unit) {
        listeners.add(listener)
    }

    fun disconnect() {
        webSocket?.close(1000, "Goodbye")
    }
}
