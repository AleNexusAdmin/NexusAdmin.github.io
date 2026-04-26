#!/usr/bin/env python3
"""Interface web (sem dependências externas) para conversa e envio de arquivos."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from chatbot_memoria import MemoryChatbot

HOST = "127.0.0.1"
PORT = 5000
BASE_DIR = Path(__file__).parent
INDEX_FILE = BASE_DIR / "templates" / "index.html"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

bot = MemoryChatbot()


class ChatHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, body: str, content_type: str = "text/html; charset=utf-8", status: int = 200) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            if not INDEX_FILE.exists():
                self._send_text("index.html não encontrado.", status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            html = INDEX_FILE.read_text(encoding="utf-8")
            self._send_text(html)
            return

        self._send_text("Not found", content_type="text/plain; charset=utf-8", status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/message":
            self._handle_message()
            return
        if self.path == "/api/upload":
            self._handle_upload()
            return
        if self.path == "/api/clear":
            bot.clear()
            self._send_json({"message": "Memória apagada com sucesso.", "stats": bot.stats()})
            return

        self._send_json({"error": "Endpoint não encontrado."}, status=HTTPStatus.NOT_FOUND)

    def _handle_message(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json({"error": "JSON inválido."}, status=HTTPStatus.BAD_REQUEST)
            return

        user_message = (payload.get("message") or "").strip()
        if not user_message:
            self._send_json({"error": "Mensagem vazia."}, status=HTTPStatus.BAD_REQUEST)
            return

        answer = bot.respond(user_message)
        bot.learn(user_message, source="chat")
        self._send_json({"reply": answer, "stats": bot.stats()})

    def _handle_upload(self) -> None:
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_json({"error": "Use multipart/form-data."}, status=HTTPStatus.BAD_REQUEST)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)

        boundary_marker = "boundary="
        if boundary_marker not in content_type:
            self._send_json({"error": "Boundary ausente."}, status=HTTPStatus.BAD_REQUEST)
            return

        boundary = content_type.split(boundary_marker, 1)[1].strip().encode("utf-8")
        parts = raw.split(b"--" + boundary)

        file_name = None
        file_bytes = None

        for part in parts:
            if b"Content-Disposition" not in part or b"name=\"file\"" not in part:
                continue
            header, _, body = part.partition(b"\r\n\r\n")
            if not body:
                continue
            disposition_lines = header.decode("utf-8", errors="ignore")
            if "filename=\"" in disposition_lines:
                file_name = disposition_lines.split("filename=\"", 1)[1].split("\"", 1)[0]
            file_bytes = body.rstrip(b"\r\n-")
            break

        if not file_name or file_bytes is None:
            self._send_json({"error": "Nenhum arquivo enviado."}, status=HTTPStatus.BAD_REQUEST)
            return

        safe_name = Path(file_name).name
        target = UPLOAD_DIR / safe_name
        target.write_bytes(file_bytes)

        try:
            content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = target.read_text(encoding="latin-1")

        learned = bot.learn_from_text_block(content, source=f"arquivo:{safe_name}")
        self._send_json({"message": f"Arquivo processado. {learned} linhas aprendidas.", "stats": bot.stats()})


def run_server() -> None:
    server = HTTPServer((HOST, PORT), ChatHandler)
    print(f"Servidor iniciado em http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor finalizado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
