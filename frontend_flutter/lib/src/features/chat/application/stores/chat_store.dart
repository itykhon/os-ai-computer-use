import 'package:mobx/mobx.dart';
import 'package:frontend_flutter/src/features/chat/domain/entities/chat_message.dart';
import 'package:frontend_flutter/src/features/chat/domain/entities/cost_usage.dart';
import 'package:frontend_flutter/src/features/chat/domain/repositories/chat_repository.dart';
import 'package:injectable/injectable.dart';
import 'package:frontend_flutter/src/features/chat/domain/entities/connection_status.dart';

part 'chat_store.g.dart';

@injectable
class ChatStore = _ChatStore with _$ChatStore;

abstract class _ChatStore with Store {
  final ChatRepository repo;
  _ChatStore(this.repo) {
    repo.messages().listen((m) => messages.add(m));
    repo.usage().listen((u) {
      usage = u;
      totalUsd += u.totalUsd;
      totalInputTokens += u.inputTokens;
      totalOutputTokens += u.outputTokens;
    });
    repo.running().listen((r) => running = r);
    repo.connectionStatus().listen((s) => connection = s);
  }

  @observable
  ObservableList<ChatMessage> messages = ObservableList.of([]);

  @observable
  CostUsage? usage;

  @observable
  double totalUsd = 0.0;

  @observable
  int totalInputTokens = 0;

  @observable
  int totalOutputTokens = 0;

  @observable
  bool running = false;

  @observable
  ConnectionStatus connection = ConnectionStatus.connecting;

  @action
  Future<void> sendTask(String text) async {
    await repo.runTask(task: text);
  }

  @action
  Future<void> init() async {
    await repo.createSession();
    // подтягиваем части конфига с бэка (history_pairs_limit)
    try {
      // Repo сейчас не проксирует REST, поэтому воспользуемся ServiceLocator позднее.
      // В текущем MVP это можно подтянуть в AppRoot и применить к AppConfig.
    } catch (_) {}
  }
}


