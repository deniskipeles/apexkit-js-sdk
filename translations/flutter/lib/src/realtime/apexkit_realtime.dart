import 'dart:convert';
import 'dart:async';
import 'package:web_socket_channel/web_socket_channel.dart';

class ApexKitRealtimeWSClient {
  final String url;
  final String? token;
  WebSocketChannel? _channel;
  bool isConnected = false;
  final _eventController = StreamController<dynamic>.broadcast();
  Map<String, dynamic>? _currentFilter;

  ApexKitRealtimeWSClient(String baseUrl, this.token)
      : url = baseUrl.replaceFirst('http', 'ws').replaceAll(RegExp(r'/$'), '') + '/ws';

  void connect() {
    _channel = WebSocketChannel.connect(Uri.parse(url));
    isConnected = true;

    _channel!.stream.listen((message) {
      final msg = jsonDecode(message);
      _eventController.add(msg);
    }, onDone: () {
      isConnected = false;
      // Reconnect logic would go here
    });

    if (_currentFilter != null) {
      subscribe(_currentFilter!);
    }
  }

  void subscribe(Map<String, dynamic> filter) {
    _currentFilter = filter;
    if (isConnected && _channel != null) {
      _channel!.sink.add(jsonEncode({
        'type': 'Subscribe',
        'payload': {
          'collection_id': filter['collectionId'],
          'record_id': filter['recordId'],
          'event_type': filter['eventType'],
          'filter': filter['dataFilter'],
          'channel': filter['channel'],
          'custom_event': filter['customEvent'],
        }
      }));
    }
  }

  void sendSignal(String channel, String eventName, dynamic data) {
    if (isConnected && _channel != null) {
      _channel!.sink.add(jsonEncode({
        'type': 'Signal',
        'payload': {'channel': channel, 'event': eventName, 'data': data}
      }));
    }
  }

  Stream<dynamic> get onEvent => _eventController.stream;

  void disconnect() {
    _channel?.sink.close();
    isConnected = false;
  }
}
