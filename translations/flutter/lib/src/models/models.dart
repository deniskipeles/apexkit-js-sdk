class User {
  final String id;
  final String email;
  final String role;
  final String scope;
  final Map<String, dynamic>? metadata;
  final String? lastActive;

  User({
    required this.id,
    required this.email,
    required this.role,
    required this.scope,
    this.metadata,
    this.lastActive,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      role: json['role'],
      scope: json['scope'],
      metadata: json['metadata'],
      lastActive: json['last_active'],
    );
  }
}

class AuthResponse {
  final String token;
  final User user;

  AuthResponse({required this.token, required this.user});

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      token: json['token'],
      user: User.fromJson(json['user']),
    );
  }
}

class BaseRecord {
  final String id;
  final String created;
  final String updated;
  final Map<String, dynamic> data;
  final Map<String, dynamic> expand;

  BaseRecord({
    required this.id,
    required this.created,
    required this.updated,
    required this.data,
    required this.expand,
  });

  factory BaseRecord.fromJson(Map<String, dynamic> json) {
    return BaseRecord(
      id: json['id'],
      created: json['created'],
      updated: json['updated'],
      data: json['data'] ?? {},
      expand: json['expand'] ?? {},
    );
  }
}

class ListResult<T> {
  final List<T> items;
  final int total;
  final int? page;
  final int? perPage;

  ListResult({
    required this.items,
    required this.total,
    this.page,
    this.perPage,
  });
}

class ApexError implements Exception {
  final String message;
  final int status;
  final String? code;
  final dynamic details;

  ApexError({required this.message, this.status = 500, this.code, this.details});

  @override
  String toString() => "ApexError: $message (Status: $status)";
}
