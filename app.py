"""
ScopeGuard AI - Local Web Dashboard & API Server
Zero-dependency HTTP server with REST endpoints for live proposal auditing and SOW generation.
"""

import os
import json
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from analyzer import analyze_proposal
from engine import GemmaEngine
from sow_generator import calculate_quote, format_pricing_table

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
PORT = 8000

class ScopeGuardHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict, status_code: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            engine = GemmaEngine()
            is_active = engine.is_ollama_available()
            self._send_json({
                "status": "ok",
                "local_ollama": is_active,
                "model": engine.model,
                "engine_type": "Gemma (Open-Weight Local)" if is_active else "Deterministic Heuristics Engine"
            })
            return

        # Serve static assets
        if path == "/" or path == "":
            file_path = os.path.join(STATIC_DIR, "index.html")
        else:
            rel_path = path.lstrip("/")
            file_path = os.path.join(STATIC_DIR, rel_path)

        # Basic path traversal protection
        if not os.path.abspath(file_path).startswith(STATIC_DIR):
            self.send_error(403, "Forbidden")
            return

        if os.path.exists(file_path) and os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            mime_type = mime_type or "application/octet-stream"
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(500, f"Error reading file: {e}")
        else:
            self.send_error(404, "File Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length)

        try:
            payload = json.loads(post_body.decode("utf-8")) if post_body else {}
        except Exception:
            self._send_json({"error": "Invalid JSON"}, 400)
            return

        proposal_text = payload.get("text", "")
        if not proposal_text.strip():
            self._send_json({"error": "Empty proposal text"}, 400)
            return

        if path == "/api/audit":
            analysis = analyze_proposal(proposal_text)
            self._send_json({
                "success": True,
                "analysis": analysis
            })
            return

        elif path == "/api/generate-sow":
            hours = float(payload.get("hours", 40))
            rate = float(payload.get("rate", 95))
            model_name = payload.get("model", "gemma2:2b")

            analysis = analyze_proposal(proposal_text)
            engine = GemmaEngine(model=model_name)
            sow_result = engine.generate_hardened_sow(proposal_text, analysis)

            quote = calculate_quote(hours, rate, sow_result["buffer_pct"])
            pricing_table = format_pricing_table(quote)

            full_sow_doc = f"{sow_result['sow_markdown']}\n\n## 6. Financial Estimate & Risk Pricing Schedule\n{pricing_table}"

            self._send_json({
                "success": True,
                "analysis": analysis,
                "sow_result": sow_result,
                "quote": quote,
                "full_document": full_sow_doc
            })
            return

        self.send_error(404, "Unknown Endpoint")

def run(port=PORT):
    server_address = ("", port)
    httpd = HTTPServer(server_address, ScopeGuardHandler)
    print(f"============================================================")
    print(f"  ScopeGuard AI Web Server Running at http://localhost:{port}")
    print(f"  Open in your browser: http://localhost:{port}")
    print(f"  Local Privacy Mode: Active (No cloud API dependencies)")
    print(f"============================================================")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
