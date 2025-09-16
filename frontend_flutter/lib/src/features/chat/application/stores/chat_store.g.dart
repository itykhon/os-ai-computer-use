// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'chat_store.dart';

// **************************************************************************
// StoreGenerator
// **************************************************************************

// ignore_for_file: non_constant_identifier_names, unnecessary_brace_in_string_interps, unnecessary_lambdas, prefer_expression_function_bodies, lines_longer_than_80_chars, avoid_as, avoid_annotating_with_dynamic, no_leading_underscores_for_local_identifiers

mixin _$ChatStore on _ChatStore, Store {
  late final _$messagesAtom = Atom(
    name: '_ChatStore.messages',
    context: context,
  );

  @override
  ObservableList<ChatMessage> get messages {
    _$messagesAtom.reportRead();
    return super.messages;
  }

  @override
  set messages(ObservableList<ChatMessage> value) {
    _$messagesAtom.reportWrite(value, super.messages, () {
      super.messages = value;
    });
  }

  late final _$usageAtom = Atom(name: '_ChatStore.usage', context: context);

  @override
  CostUsage? get usage {
    _$usageAtom.reportRead();
    return super.usage;
  }

  @override
  set usage(CostUsage? value) {
    _$usageAtom.reportWrite(value, super.usage, () {
      super.usage = value;
    });
  }

  late final _$totalUsdAtom = Atom(
    name: '_ChatStore.totalUsd',
    context: context,
  );

  @override
  double get totalUsd {
    _$totalUsdAtom.reportRead();
    return super.totalUsd;
  }

  late final _$runningAtom = Atom(
    name: '_ChatStore.running',
    context: context,
  );

  @override
  bool get running {
    _$runningAtom.reportRead();
    return super.running;
  }

  @override
  set running(bool value) {
    _$runningAtom.reportWrite(value, super.running, () {
      super.running = value;
    });
  }

  late final _$connectionAtom = Atom(
    name: '_ChatStore.connection',
    context: context,
  );

  @override
  ConnectionStatus get connection {
    _$connectionAtom.reportRead();
    return super.connection;
  }

  @override
  set connection(ConnectionStatus value) {
    _$connectionAtom.reportWrite(value, super.connection, () {
      super.connection = value;
    });
  }

  @override
  set totalUsd(double value) {
    _$totalUsdAtom.reportWrite(value, super.totalUsd, () {
      super.totalUsd = value;
    });
  }

  late final _$sendTaskAsyncAction = AsyncAction(
    '_ChatStore.sendTask',
    context: context,
  );

  @override
  Future<void> sendTask(String text) {
    return _$sendTaskAsyncAction.run(() => super.sendTask(text));
  }

  @override
  String toString() {
    return '''
messages: ${messages},
usage: ${usage},
totalUsd: ${totalUsd},
running: ${running},
connection: ${connection}
    ''';
  }
}
