import 'dart:async';
import 'dart:convert';
import 'package:injectable/injectable.dart';
import 'package:frontend_flutter/src/features/chat/domain/entities/chat_message.dart';
import 'package:frontend_flutter/src/features/chat/domain/entities/cost_usage.dart';
import 'package:frontend_flutter/src/features/chat/domain/repositories/chat_repository.dart';
import 'package:frontend_flutter/src/features/chat/data/datasources/backend_ws_client.dart';
import 'package:frontend_flutter/src/features/chat/data/datasources/backend_rest_client.dart';
import 'package:frontend_flutter/src/features/chat/domain/entities/cost_rates.dart';
import 'package:frontend_flutter/src/features/chat/domain/entities/connection_status.dart';

@LazySingleton(as: ChatRepository)
class ChatRepositoryImpl implements ChatRepository {
  final BackendWsClient _ws;
  final BackendRestClient _rest;
  final Uri Function() _wsUriProvider;
  ChatRepositoryImpl(this._ws, this._rest, {Uri Function()? wsUriProvider})
      : _wsUriProvider = wsUriProvider ?? (() => Uri.parse('ws://127.0.0.1:8765/ws?token=secret'));

  final _msgCtrl = StreamController<ChatMessage>.broadcast();
  final _usageCtrl = StreamController<CostUsage>.broadcast();
  final _runningCtrl = StreamController<bool>.broadcast();
  final _statusCtrl = StreamController<ConnectionStatus>.broadcast();
  bool _wsListening = false;
  String? _currentJobId;
  String? _thinkingMsgId;
  int _historyPairsLimit = 6;
  final List<ChatMessage> _historyText = [];
  ConnectionStatus _lastWsStatus = ConnectionStatus.connecting;
  bool _lastHealthOk = false;
  Timer? _healthTimer;
  bool _wsConnecting = false;

  String? _sessionId;

  @override
  Stream<ChatMessage> messages() => _msgCtrl.stream;

  @override
  Stream<CostUsage> usage() => _usageCtrl.stream;

  @override
  Stream<bool> running() => _runningCtrl.stream;

  @override
  Stream<ConnectionStatus> connectionStatus() => _statusCtrl.stream;

  int _id = 0;
  String _nextId() => (++_id).toString();

  @override
  Future<String> createSession({String? provider}) async {
    try {
      await _ws.connect(_wsUriProvider());
      if (!_wsListening) {
        _wsListening = true;
        _ws.messages.listen(_onWs, onDone: () {
          _runningCtrl.add(false);
          _msgCtrl.add(ChatMessage(
            id: _nextId(),
            role: 'assistant',
            ts: DateTime.now(),
            kind: 'text',
            text: 'Server connection closed.',
          ));
        }, onError: (_) {
          _runningCtrl.add(false);
          _msgCtrl.add(ChatMessage(
            id: _nextId(),
            role: 'assistant',
            ts: DateTime.now(),
            kind: 'text',
            text: 'Server connection error.',
          ));
        });
        // Monitor WS status and start health checks
        _ws.connectionStatus().listen((s) {
          _lastWsStatus = s;
          _emitEffectiveStatus();
        });
        _startHealthChecks();
      }
    } catch (_) {
      _runningCtrl.add(false);
      return '';
    }
    // Immediately probe session to force early server response -> flips status to connected when backend is alive
    final pingId = _nextId();
    _ws.send({'jsonrpc': '2.0', 'id': pingId, 'method': 'session.create', 'params': {}});
    final completer = Completer<String>();
    final id = _nextId();
    void sub(Map<String, dynamic> m) {
      if (m['id'] == id && m['result'] is Map<String, dynamic>) {
        final r = m['result'] as Map<String, dynamic>;
        _sessionId = r['sessionId'] as String?;
        completer.complete(_sessionId ?? '');
      }
    }
    final s = _ws.messages.listen(sub);
    _ws.send({
      'jsonrpc': '2.0',
      'id': id,
      'method': 'session.create',
      'params': {'provider': provider},
    });
    final sid = await completer.future.timeout(const Duration(seconds: 5), onTimeout: () => '');
    await s.cancel();
    return sid;
  }

  void _onWs(Map<String, dynamic> m) {
    // ignore: avoid_print
    print('[Repo] WS <- ' + (m['method']?.toString() ?? 'resp id=' + (m['id']?.toString() ?? 'unknown')));
    if (m.containsKey('method')) {
      final method = m['method'] as String;
      if (method == 'event.log') {
        final p = m['params'] as Map<String, dynamic>;
        final msg = (p['message'] as String?) ?? '';
        // ignore: avoid_print
        print('[Repo] event.log: ' + msg);
        // Если это tool_result ок, рисуем галочку
        if (msg.startsWith('done:') || msg.startsWith('ok') || msg.toLowerCase().contains('tool_result')) {
          final lastAction = _lastActionNameFromQueue();
          _msgCtrl.add(ChatMessage(
            id: _nextId(),
            role: 'assistant',
            ts: DateTime.now(),
            kind: 'action',
            text: '✔ ' + (lastAction ?? 'ok'),
            meta: {'name': lastAction ?? 'ok', 'status': 'ok'},
          ));
          return;
        }
        // Fallback: планы Anthropic в логах
        if (msg.startsWith('ANTHROPIC_TOOL_USE:')) {
          try {
            final raw = msg.substring('ANTHROPIC_TOOL_USE:'.length);
            final parsed = jsonDecode(raw);
            if (parsed is List) {
              for (final b in parsed) {
                String? name;
                Map<String, dynamic>? input;
                if (b is Map) {
                  name = b['name'] as String?;
                  final i = b['input'];
                  if (i is Map) input = i.cast<String, dynamic>();
                }
                _msgCtrl.add(ChatMessage(
                  id: _nextId(),
                  role: 'assistant',
                  ts: DateTime.now(),
                  kind: 'action',
                  text: _formatPlannedActionText(name, input),
                  meta: {'name': name, 'status': 'plan', 'meta': input},
                ));
              }
              return;
            }
          } catch (_) {}
        }
        final cmThought = ChatMessage(
          id: _nextId(),
          role: 'assistant',
          ts: DateTime.now(),
          kind: 'thought',
          text: msg.isEmpty ? null : msg,
        );
        _msgCtrl.add(cmThought);
        _recordHistory(cmThought);
      } else if (method == 'event.screenshot') {
        final p = m['params'] as Map<String, dynamic>;
        // ignore: avoid_print
        print('[Repo] event.screenshot len=' + ((p['data'] as String?)?.length.toString() ?? '0'));
        _msgCtrl.add(ChatMessage(
          id: _nextId(),
          role: 'assistant',
          ts: DateTime.now(),
          kind: 'screenshot',
          imageBase64: p['data'] as String?,
        ));
      } else if (method == 'event.action') {
        final p = m['params'] as Map<String, dynamic>;
        final name = p['name'] as String?;
        final status = p['status'] as String?;
        final meta = (p['meta'] as Map?)?.cast<String, dynamic>();
        // ignore: avoid_print
        print('[Repo] event.action: ' + (name ?? '') + ' [' + (status ?? '') + ']');
        _rememberActionName(meta, name);
        final cmAction = ChatMessage(
          id: _nextId(),
          role: 'assistant',
          ts: DateTime.now(),
          kind: 'action',
          text: _formatActionText(name, status, meta),
          meta: {'name': name, 'status': status, 'meta': meta},
        );
        _msgCtrl.add(cmAction);
      } else if (method == 'event.usage') {
        final p = m['params'] as Map<String, dynamic>;
        final inTok = (p['input_tokens'] as num? ?? 0).toInt();
        final outTok = (p['output_tokens'] as num? ?? 0).toInt();
        // ignore: avoid_print
        print('[Repo] event.usage in=' + inTok.toString() + ' out=' + outTok.toString());
        final u = CostUsage(
          inputTokens: inTok,
          outputTokens: outTok,
          inputUsd: CostRates.inputUsdFor(inTok),
          outputUsd: CostRates.outputUsdFor(outTok),
        );
        _usageCtrl.add(u);
        final cmUsage = ChatMessage(
          id: _nextId(),
          role: 'assistant',
          ts: DateTime.now(),
          kind: 'usage',
          text: 'in=' + inTok.toString() + ' out=' + outTok.toString() + '  cost=\$' + u.totalUsd.toStringAsFixed(6) + ' (input=\$' + u.inputUsd.toStringAsFixed(6) + ', output=\$' + u.outputUsd.toStringAsFixed(6) + ')',
          meta: {
            'inputTokens': inTok,
            'outputTokens': outTok,
            'inputUsd': u.inputUsd,
            'outputUsd': u.outputUsd,
            'totalUsd': u.totalUsd,
          },
        );
        _msgCtrl.add(cmUsage);
      } else if (method == 'event.final') {
        final p = m['params'] as Map<String, dynamic>;
        // ignore: avoid_print
        print('[Repo] event.final');
        final text = p['text'] as String?;
        if (text != null && text.isNotEmpty) {
          final cmFinal = ChatMessage(
            id: _nextId(),
            role: 'assistant',
            ts: DateTime.now(),
            kind: 'text',
            text: text,
          );
          _msgCtrl.add(cmFinal);
          _recordHistory(cmFinal);
        }
        // remove the Thinking... bubble when job finishes
        _thinkingMsgId = null;
        _currentJobId = null;
        _runningCtrl.add(false);
      }
      return;
    }
    // Handle responses by id if needed
  }

  @override
  Future<String> runTask({required String task}) async {
    final id = _nextId();
    _msgCtrl.add(ChatMessage(id: _nextId(), role: 'user', ts: DateTime.now(), kind: 'text', text: task));
    _thinkingMsgId = _nextId();
    _msgCtrl.add(ChatMessage(id: _thinkingMsgId!, role: 'assistant', ts: DateTime.now(), kind: 'thought', text: 'Thinking...', meta: const {'thinking': true}));
    _runningCtrl.add(true);
    _ws.send({
      'jsonrpc': '2.0',
      'id': id,
      'method': 'agent.run',
      'params': {
        'task': task,
        'maxIterations': 30,
        // передаем короткий контекст из последних сообщений как текстовые пары
        'context': _buildContext(),
      },
    });
    _currentJobId = id;
    return id;
  }

  @override
  Future<void> cancelJob(String jobId) async {
    final id = _nextId();
    _ws.send({'jsonrpc': '2.0', 'id': id, 'method': 'agent.cancel', 'params': {'jobId': jobId}});
  }

  @override
  Future<void> cancelCurrentJob() async {
    final jid = _currentJobId;
    if (jid == null) return;
    await cancelJob(jid);
    _msgCtrl.add(ChatMessage(id: _nextId(), role: 'assistant', ts: DateTime.now(), kind: 'text', text: 'Stopped by user.'));
  }

  @override
  Future<String> uploadFile(String name, List<int> bytes, {String? mime}) async {
    return _rest.uploadBytes(name, bytes, mime: mime);
  }

  String _formatActionText(String? name, String? status, Map<String, dynamic>? meta) {
    final b = StringBuffer();
    if (name != null) b.write(name);
    if (status != null) b.write(' [' + status + ']');
    if (meta != null && meta.isNotEmpty) {
      b.write(' ');
      b.write(meta.toString());
    }
    return b.toString();
  }

  String _formatPlannedActionText(String? name, Map<String, dynamic>? input) {
    final b = StringBuffer('PLAN: ');
    if (name != null) b.write(name);
    if (input != null && input.isNotEmpty) {
      b.write(' ');
      b.write(input.toString());
    }
    return b.toString();
  }

  void _startHealthChecks() {
    _healthTimer ??= Timer.periodic(const Duration(seconds: 5), (_) async {
      try {
        final res = await _rest.healthz().timeout(const Duration(seconds: 2));
        _lastHealthOk = res.isNotEmpty;
      } catch (_) {
        _lastHealthOk = false;
      }
      // If backend is healthy but WS isn't connected, try to (re)connect
      if (_lastHealthOk && _lastWsStatus != ConnectionStatus.connected && !_wsConnecting) {
        _wsConnecting = true;
        try {
          await _ws.connect(_wsUriProvider());
        } catch (_) {}
        _wsConnecting = false;
      }
      _emitEffectiveStatus();
    });
  }

  void _emitEffectiveStatus() {
    ConnectionStatus eff;
    switch (_lastWsStatus) {
      case ConnectionStatus.offline:
        eff = ConnectionStatus.offline;
        break;
      case ConnectionStatus.error:
        eff = ConnectionStatus.error;
        break;
      case ConnectionStatus.disconnected:
        eff = ConnectionStatus.connecting;
        break;
      case ConnectionStatus.connecting:
        eff = ConnectionStatus.connecting;
        break;
      case ConnectionStatus.connected:
        eff = _lastHealthOk ? ConnectionStatus.connected : ConnectionStatus.connecting;
        break;
    }
    _statusCtrl.add(eff);
  }

  List<Map<String, String>> _buildContext({int maxPairs = 6}) {
    try {
      final list = <Map<String, String>>[];
      // Берём накопленную лёгкую историю текстов
      for (final m in _historyText.take(maxPairs)) {
        final t = m.text?.trim();
        if (t == null || t.isEmpty) continue;
        final role = (m.role == 'user' || m.role == 'assistant') ? m.role : 'assistant';
        list.add({'role': role, 'text': t});
      }
      return list;
    } catch (_) {
      return const [];
    }
  }

  String? _lastActionNameFromQueue() {
    // Небольшой хак: пробуем найти последнее действие по последним action-сообщениям
    // (в рамках этой простой реализации можно расширить хранением отдельной очереди)
    return null;
  }

  void _rememberActionName(Map<String, dynamic>? meta, String? name) {
    // Заготовка под будущий state, чтобы знать последнее действие
  }

  void _recordHistory(ChatMessage m) {
    if (m.kind == 'text' || m.kind == 'thought') {
      _historyText.insert(0, m);
      final cap = _historyPairsLimit * 2;
      if (_historyText.length > cap) {
        _historyText.removeRange(cap, _historyText.length);
      }
    }
  }
}


