import 'package:equatable/equatable.dart';

class ChatMessage extends Equatable {
  final String id;
  final String role; // 'user' | 'assistant' | 'system'
  final String? kind; // 'thought' | 'action' | 'screenshot' | 'usage' | 'text'
  final String? text;
  final String? imageBase64; // optional screenshot
  final Map<String, dynamic>? meta; // additional data for rendering
  final DateTime ts;

  const ChatMessage({
    required this.id,
    required this.role,
    required this.ts,
    this.kind,
    this.text,
    this.imageBase64,
    this.meta,
  });

  @override
  List<Object?> get props => [id, role, kind, text, imageBase64, meta, ts];
}


