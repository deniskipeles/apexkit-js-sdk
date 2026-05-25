# ApexKit Android Kotlin SDK

A Kotlin client for the ApexKit API.

## Installation

Add dependencies to `build.gradle`:

```gradle
dependencies {
    implementation 'com.squareup.okhttp3:okhttp:4.9.3'
    implementation 'com.google.code.gson:gson:2.8.9'
}
```

## Usage

```kotlin
import com.apexkit.sdk.ApexKit

val apex = ApexKit("http://localhost:5000")

// Run on background thread
Thread {
    try {
        val auth = apex.auth.login("admin@example.com", "password")
        println("Logged in as ${auth.user.email}")

        val records = apex.collection("posts").list()
        records.items.forEach { println("Record: ${it.id}") }
    } catch (e: Exception) {
        e.printStackTrace()
    }
}.start()
```

## Realtime

```kotlin
val realtime = ApexKitRealtimeWSClient("http://localhost:5000", token)
realtime.onEvent { event ->
    println("Received: $event")
}
realtime.connect()
realtime.subscribe(mapOf("collectionId" to 1))
```
