import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_mobx/flutter_mobx.dart';
import 'package:provider/provider.dart';
import 'package:frontend_flutter/src/features/chat/application/stores/chat_store.dart';
import 'package:frontend_flutter/src/presentation/theme/app_theme.dart';

class ChatMessagesList extends StatelessWidget {
  const ChatMessagesList({super.key});

  @override
  Widget build(BuildContext context) {
    return Observer(
      builder: (_) {
        final store = context.read<ChatStore?>();
        final len = store?.messages.length ?? 0;
        return ListView.builder(
          padding: const EdgeInsets.all(12),
          itemCount: len,
          itemBuilder: (_, i) {
            final m = store!.messages[i];
            if (m.kind == 'screenshot' && m.imageBase64 != null && m.imageBase64!.isNotEmpty) {
              return Align(
                alignment: Alignment.centerLeft,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      margin: const EdgeInsets.symmetric(vertical: 6),
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        border: Border.all(color: context.themeColors.surfaceBorder),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Screenshot (${m.ts.toIso8601String().substring(11, 19)})',
                              style: Theme.of(context).textTheme.bodySmall),
                          const SizedBox(height: 6),
                          _ZoomableBase64Image(base64Data: m.imageBase64!),
                        ],
                      ),
                    )
                  ],
                ),
              );
            }
            if (m.kind == 'usage') {
              return Align(
                alignment: Alignment.centerLeft,
                child: Container(
                  margin: const EdgeInsets.symmetric(vertical: 6),
                  padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 10),
                  decoration: BoxDecoration(
                    color: context.themeColors.usageFill,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: context.themeColors.usageBorder),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('📈'),
                      const SizedBox(width: 6),
                      Text(
                        m.text ?? '',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
              );
            }
            if (m.kind == 'action') {
              final meta = (m.meta ?? const {});
              final inner = (meta['meta'] is Map) ? (meta['meta'] as Map) : const {};
              final actionName = (inner['action'] as String?) ?? (meta['name'] as String? ?? '');
              final status = (m.meta?['status'] as String? ?? '').toLowerCase();
              final badge = _actionBadgeFor(context, actionName);
              final Color border = badge.$2;
              final Color fill = badge.$3;
              final String icon = badge.$1;
              return Align(
                alignment: Alignment.centerLeft,
                child: Container(
                  margin: const EdgeInsets.symmetric(vertical: 6),
                  padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 10),
                  decoration: BoxDecoration(
                    color: fill,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: border),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(icon),
                      const SizedBox(width: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(vertical: 2, horizontal: 6),
                        decoration: BoxDecoration(
                          color: border.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: border.withOpacity(0.4)),
                        ),
                        child: Text(status.isEmpty ? 'start' : status, style: Theme.of(context).textTheme.labelSmall),
                      ),
                      const SizedBox(width: 8),
                      Flexible(
                        child: Text(
                          m.text ?? '',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }
            if (m.kind == 'thought') {
              final isThinking = (m.meta?['thinking'] as bool?) == true;
              return Align(
                alignment: Alignment.centerLeft,
                child: Container(
                  width: double.infinity,
                  margin: const EdgeInsets.symmetric(vertical: 6),
                  padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 10),
                  decoration: BoxDecoration(
                    color: context.themeColors.assistantBubbleBg,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: context.themeColors.surfaceBorder),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.max,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('🧠'),
                      const SizedBox(width: 8),
                      Flexible(
                        child: Text(
                          m.text ?? '',
                          softWrap: true,
                          style: context.theme.style((t) => t.bodySmall, (c) => c.assistantBubbleFg),
                        ),
                      ),
                      if (isThinking) ...[
                        const SizedBox(width: 8),
                        SizedBox(width: 12, height: 12, child: CircularProgressIndicator(strokeWidth: 2, color: context.themeColors.assistantBubbleFg)),
                      ]
                    ],
                  ),
                ),
              );
            }
            return _MessageBubble(role: m.role, text: m.text ?? '');
          },
        );
      },
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final String role;
  final String text;
  const _MessageBubble({required this.role, required this.text});

  @override
  Widget build(BuildContext context) {
    final isUser = role == 'user';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6),
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
        decoration: BoxDecoration(
          color: isUser ? context.themeColors.userBubbleBg : context.themeColors.assistantBubbleBg,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text(
          text,
          style: isUser
              ? context.theme.style((t) => t.body, (c) => c.userBubbleFg)
              : context.theme.style((t) => t.body, (c) => c.assistantBubbleFg),
        ),
      ),
    );
  }
}

// Returns (icon, borderColor, fillColor)
(String, Color, Color) _actionBadgeFor(BuildContext context, String name) {
  final n = name.toLowerCase();
  if (n == 'screenshot') {
    return ('📸', context.themeColors.actionTealBorder, context.themeColors.actionTealFill);
  }
  if (n == 'mouse_move') {
    return ('🖱️', context.themeColors.actionIndigoBorder, context.themeColors.actionIndigoFill);
  }
  if (n == 'left_click' || n == 'double_click' || n == 'triple_click' || n == 'right_click' || n == 'middle_click') {
    return ('🖱️', context.themeColors.actionPurpleBorder, context.themeColors.actionPurpleFill);
  }
  if (n == 'left_click_drag') {
    return ('🖱️', context.themeColors.actionPurpleBorder, context.themeColors.actionPurpleFill);
  }
  if (n == 'type') {
    return ('⌨️', context.themeColors.actionBlueGreyBorder, context.themeColors.actionBlueGreyFill);
  }
  if (n == 'key' || n == 'hold_key') {
    return ('⌨️', context.themeColors.actionBlueGreyBorder, context.themeColors.actionBlueGreyFill);
  }
  if (n == 'scroll') {
    return ('🌀', context.themeColors.actionGreenBorder, context.themeColors.actionGreenFill);
  }
  if (n == 'wait') {
    return ('⏱️', context.themeColors.actionOrangeBorder, context.themeColors.actionOrangeFill);
  }
  return ('🔧', context.themeColors.actionPurpleBorder, context.themeColors.actionPurpleFill);
}

class _ZoomableBase64Image extends StatefulWidget {
  final String base64Data;
  const _ZoomableBase64Image({required this.base64Data});

  @override
  State<_ZoomableBase64Image> createState() => _ZoomableBase64ImageState();
}

class _ZoomableBase64ImageState extends State<_ZoomableBase64Image> {
  bool zoomed = false;

  @override
  Widget build(BuildContext context) {
    final bytes = const Base64Decoder().convert(widget.base64Data);
    final img = Image.memory(bytes, gaplessPlayback: true);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: double.infinity,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: zoomed
                ? InteractiveViewer(
                    minScale: 0.5,
                    maxScale: 4,
                    child: img,
                  )
                : SizedBox(
                    width: 150,
                    height: 150,
                    child: FittedBox(
                      fit: BoxFit.cover,
                      child: img,
                    ),
                  ),
          ),
        ),
        const SizedBox(height: 6),
        Align(
          alignment: Alignment.centerRight,
          child: TextButton.icon(
            onPressed: () => setState(() => zoomed = !zoomed),
            icon: Icon(zoomed ? Icons.zoom_out : Icons.zoom_in),
            label: Text(zoomed ? 'Zoom out' : 'Zoom in'),
          ),
        ),
      ],
    );
  }
}


