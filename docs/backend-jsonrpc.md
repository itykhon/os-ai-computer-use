Backend JSON-RPC API (WS)
=========================

WS URL: `ws://127.0.0.1:8765/ws?token=...`

Requests use JSON-RPC 2.0:

```
{"jsonrpc":"2.0","id":"1","method":"session.create","params":{"provider":"anthropic"}}
```

Methods
-------

- session.create → { sessionId, capabilities }
- agent.run { task, provider?, maxIterations? } → { jobId, sessionId }
- agent.cancel { jobId } → { ok, jobId }

Events (server notifications)
-----------------------------
- event.log { level, message, jobId }
- event.action { name, status, meta, jobId }
- event.screenshot { mime, data(base64), ts?, jobId }
- event.progress { stage, iteration?, jobId }
- event.final { text, usage{input_tokens,output_tokens}, status, jobId }

REST
----
- POST /v1/files (multipart, field "file") → { fileId, name }
- GET /v1/files/{fileId} → binary
- POST /settings.update { screenshot_enabled?, screenshot_binary_mode?, screenshot_quality?, log_level? }
- GET /metrics → counters


