# ApexKit Flutter SDK

A Flutter client for the ApexKit API.

## Installation

Add this to your `pubspec.yaml`:

```yaml
dependencies:
  apexkit:
    path: ./translations/flutter
```

## Usage

```dart
import 'package:apexkit/apexkit.dart';

final apex = ApexKit("http://localhost:5000");

// Login
final auth = await apex.auth.login("admin@example.com", "password");
print("Logged in as ${auth.user.email}");

// List records
final records = await apex.collection("posts").list();
for (var record in records.items) {
  print("Record: ${record.id}");
}
```

## Realtime

```dart
final realtime = ApexKitRealtimeWSClient("http://localhost:5000", token);
realtime.onEvent.listen((event) {
  print("Event received: $event");
});
realtime.connect();
realtime.subscribe({'collectionId': 1});
```
