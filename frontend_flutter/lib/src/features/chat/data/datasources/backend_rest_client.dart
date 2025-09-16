import 'package:dio/dio.dart';
import 'package:injectable/injectable.dart';

@lazySingleton
class BackendRestClient {
  final Dio _dio;
  BackendRestClient() : _dio = Dio();

  set baseUrl(String url) => _dio.options.baseUrl = url;
  set bearer(String? token) {
    if (token == null || token.isEmpty) {
      _dio.options.headers.remove('Authorization');
    } else {
      _dio.options.headers['Authorization'] = 'Bearer $token';
    }
  }

  Future<String> uploadBytes(String name, List<int> bytes, {String? mime}) async {
    final form = FormData.fromMap({
      'file': MultipartFile.fromBytes(bytes, filename: name, contentType: mime != null ? DioMediaType.parse(mime) : null),
    });
    final resp = await _dio.post('/v1/files', data: form);
    return (resp.data as Map<String, dynamic>)['fileId'] as String;
  }

  Future<Map<String, dynamic>> healthz() async {
    final resp = await _dio.get('/healthz');
    return (resp.data as Map<String, dynamic>);
  }
}


