# ApexKit Android Java SDK

A Java client for the ApexKit API.

## Installation

Add dependencies to `build.gradle`:

```gradle
dependencies {
    implementation 'com.squareup.okhttp3:okhttp:4.9.3'
    implementation 'com.google.code.gson:gson:2.8.9'
}
```

## Usage

```java
import com.apexkit.sdk.ApexKit;
import com.apexkit.sdk.models.AuthResponse;

ApexKit apex = new ApexKit("http://localhost:5000");

new Thread(() -> {
    try {
        AuthResponse auth = apex.auth().login("admin@example.com", "password");
        System.out.println("Logged in as " + auth.user.email);
    } catch (Exception e) {
        e.printStackTrace();
    }
}).start();
```
