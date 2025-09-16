import 'package:flutter/foundation.dart';

class AppConfig extends ChangeNotifier {
  String host;
  int port;
  String token;
  int historyPairsLimit;

  AppConfig({this.host = '127.0.0.1', this.port = 8765, this.token = 'secret', this.historyPairsLimit = 6});

  Uri wsUri() => Uri.parse('ws://$host:$port/ws?token=$token');
  String restBase() => 'http://$host:$port';

  void update({String? host, int? port, String? token, int? historyPairsLimit}) {
    bool changed = false;
    if (host != null && host != this.host) {
      this.host = host;
      changed = true;
    }
    if (port != null && port != this.port) {
      this.port = port;
      changed = true;
    }
    if (token != null && token != this.token) {
      this.token = token;
      changed = true;
    }
    if (historyPairsLimit != null && historyPairsLimit != this.historyPairsLimit) {
      this.historyPairsLimit = historyPairsLimit;
      changed = true;
    }
    if (changed) notifyListeners();
  }
}


