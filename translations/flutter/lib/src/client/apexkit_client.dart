import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/models.dart';

class ApexKit {
  String baseUrl;
  String? _token;
  User? _currentUser;
  String _scopeType = 'root';
  String _scopeId = '';

  ApexKit(this.baseUrl) : baseUrl = baseUrl.replaceAll(RegExp(r'/$'), '');

  ApexKit sandbox(String uuid) {
    final instance = ApexKit('$baseUrl/sandbox/$uuid');
    instance._scopeType = 'sandbox';
    instance._scopeId = uuid;
    instance.setToken(_token ?? '', _currentUser);
    return instance;
  }

  ApexKit tenant(String tenantId) {
    final instance = ApexKit('$baseUrl/tenant/$tenantId');
    instance._scopeType = 'tenant';
    instance._scopeId = tenantId;
    instance.setToken(_token ?? '', _currentUser);
    return instance;
  }

  void setToken(String token, User? user) {
    _token = token;
    if (user != null) {
      _currentUser = user;
      _setScopeFromTag(user.scope);
    }
  }

  void _setScopeFromTag(String tag) {
    if (tag == 'root') {
      _scopeType = 'root';
      _scopeId = '';
    } else if (tag.startsWith('tenant:')) {
      _scopeType = 'tenant';
      _scopeId = tag.split(':')[1];
    } else if (tag.startsWith('sandbox:')) {
      _scopeType = 'sandbox';
      _scopeId = tag.split(':')[1];
    }
  }

  Future<dynamic> _request(String endpoint, {
    String method = 'GET',
    Map<String, String>? headers,
    dynamic body,
    Map<String, dynamic>? params,
    bool isRoot = false,
  }) async {
    String path = endpoint;
    if (!isRoot && !endpoint.startsWith('/api/v1')) {
      path = endpoint.startsWith('/') ? '/api/v1$endpoint' : '/api/v1/$endpoint';
    }

    var uri = Uri.parse('$baseUrl$path');
    if (params != null) {
      uri = uri.replace(queryParameters: params.map((key, value) => MapEntry(key, value.toString())));
    }

    final requestHeaders = <String, String>{...?(headers)};
    if (_token != null) {
      requestHeaders['Authorization'] = 'Bearer $_token';
    }

    http.Response response;
    final requestBody = body != null ? jsonEncode(body) : null;
    if (body != null) {
      requestHeaders['Content-Type'] = 'application/json';
    }

    switch (method.toUpperCase()) {
      case 'POST':
        response = await http.post(uri, headers: requestHeaders, body: requestBody);
        break;
      case 'PUT':
        response = await http.put(uri, headers: requestHeaders, body: requestBody);
        break;
      case 'PATCH':
        response = await http.patch(uri, headers: requestHeaders, body: requestBody);
        break;
      case 'DELETE':
        response = await http.delete(uri, headers: requestHeaders);
        break;
      default:
        response = await http.get(uri, headers: requestHeaders);
    }

    if (response.statusCode == 204) return null;

    final data = jsonDecode(response.body);

    if (response.statusCode >= 400) {
      throw ApexError(
        message: data['message'] ?? 'API Error',
        status: response.statusCode,
        code: data['error'],
        details: data['details'],
      );
    }

    return data;
  }

  AuthNamespace get auth => AuthNamespace(this);
  AdminsNamespace get admins => AdminsNamespace(this);
  AiNamespace get ai => AiNamespace(this);
  ScriptsNamespace get scripts => ScriptsNamespace(this);
  TemplatesNamespace get templates => TemplatesNamespace(this);
  FilesNamespace get files => FilesNamespace(this);

  CollectionNamespace collection(String id) => CollectionNamespace(this, id);

  Future<dynamic> graphql(String query, {Map<String, dynamic>? variables}) {
    return _request('/graphql', method: 'POST', isRoot: true, body: {'query': query, 'variables': variables ?? {}});
  }
}

class AuthNamespace {
  final ApexKit client;
  AuthNamespace(this.client);

  Future<AuthResponse> login(String email, String password) async {
    final res = await client._request('/auth/login', method: 'POST', body: {'email': email, 'password': password});
    final authRes = AuthResponse.fromJson(res);
    client.setToken(authRes.token, authRes.user);
    return authRes;
  }

  Future<AuthResponse> register(String email, String password) async {
    final res = await client._request('/auth/register', method: 'POST', body: {'email': email, 'password': password});
    final authRes = AuthResponse.fromJson(res);
    client.setToken(authRes.token, authRes.user);
    return authRes;
  }

  Future<User> getMe() async {
    final res = await client._request('/auth/me');
    final user = User.fromJson(res);
    client._setScopeFromTag(user.scope);
    return user;
  }

  void logout() {
    client.setToken('', null);
  }
}

class CollectionNamespace {
  final ApexKit client;
  final String id;
  CollectionNamespace(this.client, this.id);

  Future<ListResult<BaseRecord>> list({Map<String, dynamic>? options}) async {
    final res = await client._request('/collections/$id/records', params: options);
    return ListResult(
      items: (res['items'] as List).map((i) => BaseRecord.fromJson(i)).toList(),
      total: res['total'],
      page: res['page'],
      perPage: res['per_page'],
    );
  }

  Future<BaseRecord> create(Map<String, dynamic> data) async {
    final res = await client._request('/collections/$id/records', method: 'POST', body: {'data': data});
    return BaseRecord.fromJson(res);
  }

  Future<BaseRecord> get(String recordId, {Map<String, dynamic>? options}) async {
    final res = await client._request('/collections/$id/records/$recordId', params: options);
    return BaseRecord.fromJson(res);
  }

  Future<BaseRecord> update(String recordId, Map<String, dynamic> data) async {
    final res = await client._request('/collections/$id/records/$recordId', method: 'PUT', body: {'data': data});
    return BaseRecord.fromJson(res);
  }

  Future<BaseRecord> patch(String recordId, Map<String, dynamic> data) async {
    final res = await client._request('/collections/$id/records/$recordId', method: 'PATCH', body: {'data': data});
    return BaseRecord.fromJson(res);
  }

  Future<void> delete(String recordId) async {
    await client._request('/collections/$id/records/$recordId', method: 'DELETE');
  }
}

class AdminsNamespace {
  final ApexKit client;
  AdminsNamespace(this.client);

  Future<List<dynamic>> listCollections() async {
    return await client._request('/collections');
  }

  Future<dynamic> createCollection(String name, dynamic schema) async {
    return await client._request('/collections', method: 'POST', body: {'name': name, 'schema': schema});
  }

  Future<void> deleteCollection(String id) async {
    await client._request('/collections/$id', method: 'DELETE');
  }
}

class AiNamespace {
  final ApexKit client;
  AiNamespace(this.client);

  Future<dynamic> run(String slug, Map<String, dynamic> variables) async {
    return await client._request('/ai/run/$slug', method: 'POST', body: {'variables': variables});
  }
}

class ScriptsNamespace {
  final ApexKit client;
  ScriptsNamespace(this.client);

  Future<dynamic> run(String name, dynamic variables) async {
    return await client._request('/run/$name', method: 'POST', body: variables);
  }
}

class FilesNamespace {
  final ApexKit client;
  FilesNamespace(this.client);

  String getFileUrl(String filename) {
    if (filename.startsWith('http://') || filename.startsWith('https://')) return filename;
    return '${client.baseUrl}/api/v1/storage/file/${filename.replaceFirst(RegExp(r'^/'), '')}';
  }
}

class TemplatesNamespace {
  final ApexKit client;
  TemplatesNamespace(this.client);

  Future<List<dynamic>> list() async {
    return await client._request('/admin/templates');
  }
}
