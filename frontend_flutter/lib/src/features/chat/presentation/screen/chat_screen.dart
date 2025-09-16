import 'package:flutter/material.dart';
import 'package:frontend_flutter/src/features/chat/presentation/widgets/chat_messages_list.dart';
import 'package:frontend_flutter/src/features/chat/presentation/widgets/chat_input_composer.dart';
import 'package:provider/provider.dart';
import 'package:flutter_mobx/flutter_mobx.dart';
import 'package:frontend_flutter/src/features/chat/application/stores/chat_store.dart';
import 'package:frontend_flutter/src/presentation/stores/theme_store.dart';
import 'package:frontend_flutter/src/presentation/theme/app_theme.dart';
import 'package:frontend_flutter/src/features/chat/domain/entities/connection_status.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final store = context.read<ChatStore?>();
      store?.init();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        title: Observer(builder: (_) {
          final storeWatch = context.watch<ChatStore?>();
          final u = storeWatch?.usage;
          final totalUsd = storeWatch?.totalUsd ?? 0.0;
          final tin = storeWatch?.totalInputTokens ?? 0;
          final tout = storeWatch?.totalOutputTokens ?? 0;
          final conn = storeWatch?.connection ?? ConnectionStatus.connecting;
          final connText = () {
            switch (conn) {
              case ConnectionStatus.offline:
                return 'offline';
              case ConnectionStatus.connecting:
                return 'connecting';
              case ConnectionStatus.connected:
                return 'connected';
              case ConnectionStatus.disconnected:
                return 'disconnected';
              case ConnectionStatus.error:
                return 'error';
            }
          }();
          // If socket closed but reconnect in progress, prefer 'connecting' over stale 'connected'
          final effectiveText = conn == ConnectionStatus.disconnected ? 'connecting' : connText;
          final subtitle = (u == null || (tin + tout) == 0)
              ? 'status: ' + effectiveText
              : 'status: ' + effectiveText +
                  '   in=' + u.inputTokens.toString() + ' out=' + u.outputTokens.toString() +
                  '  Σtokens=' + (tin + tout).toString() +
                  '  \$' + u.totalUsd.toStringAsFixed(4) +
                  ' (Σ \$' + totalUsd.toStringAsFixed(4) + ')';
          final offlineDot = conn == ConnectionStatus.offline
              ? Text(' ●', style: context.theme.style((t) => t.bodySmall, (c) => c.actionOrangeBorder))
              : const SizedBox.shrink();
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text('OS AI', style: context.theme.style((t) => t.body, (c) => c.assistantBubbleFg)),
                  offlineDot,
                ],
              ),
              Text(subtitle, style: context.theme.style((t) => t.bodySmall, (c) => c.assistantBubbleFg)),
            ],
          );
        }),
        actions: [
          IconButton(
            tooltip: 'Toggle theme',
            onPressed: () {
              final ts = context.read<ThemeStore?>();
              if (ts == null) return;
              ts.toggleUsing(context);
            },
            icon: const Icon(Icons.brightness_6),
          ),
          Observer(builder: (_) {
            final running = context.watch<ChatStore?>()?.running ?? false;
            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: SizedBox(
                width: 18,
                height: 18,
                child: running
                    ? const CircularProgressIndicator(strokeWidth: 2)
                    : const SizedBox.shrink(),
              ),
            );
          }),
        ],
      ),
      body: const Column(
        children: [
          Expanded(child: ChatMessagesList()),
          ChatInputComposer(),
        ],
      ),
    );
  }
}


