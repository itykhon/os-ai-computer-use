import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import 'package:frontend_flutter/src/features/chat/application/stores/chat_store.dart';
import 'package:frontend_flutter/src/features/chat/domain/repositories/chat_repository.dart';

class ChatInputComposer extends StatefulWidget {
  const ChatInputComposer({super.key});

  @override
  State<ChatInputComposer> createState() => _ChatInputComposerState();
}

class _ChatInputComposerState extends State<ChatInputComposer> {
  final controller = TextEditingController();

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final store = context.read<ChatStore?>();
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: controller,
                minLines: 1,
                maxLines: 5,
                decoration: const InputDecoration(
                  hintText: 'Describe your task…',
                  border: OutlineInputBorder(),
                ),
                onSubmitted: (v) async {
                  final txt = controller.text.trim();
                  if (txt.isEmpty || store == null) return;
                  await store.sendTask(txt);
                  controller.clear();
                },
              ),
            ),
            const SizedBox(width: 8),
            FilledButton.icon(
              onPressed: () async {
                final txt = controller.text.trim();
                if (txt.isEmpty || store == null) return;
                await store.sendTask(txt);
                controller.clear();
              },
              icon: const Icon(Icons.send),
              label: const Text('Send'),
            ),
            const SizedBox(width: 8),
            Selector<ChatStore?, bool>(
              selector: (_, s) => s?.running ?? false,
              builder: (_, running, __) => running
                  ? FilledButton.icon(
                      style: FilledButton.styleFrom(backgroundColor: Colors.red),
                      onPressed: () async {
                        final repo = context.read<ChatRepository?>();
                        await repo?.cancelCurrentJob();
                      },
                      icon: const Icon(Icons.stop),
                      label: const Text('Stop'),
                    )
                  : const SizedBox.shrink(),
            ),
            const SizedBox(width: 8),
            IconButton(
              tooltip: 'Attach file',
              onPressed: () async {
                final res = await FilePicker.platform.pickFiles(withData: true);
                if (res == null) return;
                final f = res.files.single;
                final repo = context.read<ChatRepository?>();
                if (repo == null || f.bytes == null) return;
                final id = await repo.uploadFile(f.name, f.bytes!, mime: f.extension);
                if (!mounted) return;
                final s = context.read<ChatStore?>();
                await s?.sendTask('File uploaded: $id');
              },
              icon: const Icon(Icons.attach_file),
            )
          ],
        ),
      ),
    );
  }
}


