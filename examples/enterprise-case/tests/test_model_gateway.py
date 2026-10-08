"""Real HTTP transport to a local protocol test server, not a model benchmark."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from model_gateway import ModelGateway, ModelError


class GatewayTest(unittest.TestCase):
    def setUp(self):
        test = self
        self.received = None
        self.status = 200
        self.body = {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps({
            "action": "search", "args": {"question": "退款"}, "reason": "找依据"})}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 8, "secret": "never retain"}}
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                test.received = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                raw = json.dumps(test.body).encode()
                self.send_response(test.status)
                if test.status == 302:
                    self.send_header("Location", "/other")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            def log_message(self, *args):
                pass
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.gateway = ModelGateway(f"http://127.0.0.1:{self.server.server_port}/v1/chat/completions", "test-model", "test-key")

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_real_transport_decodes_decision_and_retains_only_usage(self):
        decision, identity = self.gateway.decide("http", {"purpose": "query"})
        self.assertEqual("search", decision["action"])
        self.assertEqual("test-model", self.received["model"])
        self.assertEqual({"type": "json_object"}, self.received["response_format"])
        self.assertEqual({"prompt_tokens": 12, "completion_tokens": 8}, identity["usage"])
        self.assertNotIn("test-key", json.dumps(identity))

    def test_malformed_or_truncated_output_rejected(self):
        for choice in ({"message": {"content": "not JSON"}},
                       {"finish_reason": "length", "message": {"content": "{}"}},
                       {"message": {"content": "[]"}}):
            self.body = {"choices": [choice]}
            with self.assertRaises(ModelError):
                self.gateway.decide("http", {"purpose": "query"})

    def test_redirect_and_service_errors_are_not_followed_or_leaked(self):
        for status in (302, 401, 500):
            self.status = status
            self.body = {"error": "test-key must not be logged"}
            with self.assertRaises(ModelError) as caught:
                self.gateway.decide("http", {"purpose": "query"})
            self.assertNotIn("test-key", str(caught.exception))

    def test_wrong_envelope_types_are_reported_as_model_errors(self):
        valid_choice = self.body["choices"][0]
        for body in ([], {"choices": ["wrong"]}, {"choices": [valid_choice], "usage": None}):
            self.body = body
            with self.subTest(body=body), self.assertRaises(ModelError):
                self.gateway.decide("http", {"purpose": "query"})

    def test_config_and_input_budget_checked_before_request(self):
        for endpoint in ("http://external.example/v1", "https://user:pass@example.com/v1", "https://example.com/v1?key=secret"):
            with self.assertRaises(ModelError):
                ModelGateway(endpoint, "m", "").decide("http", {})
        with self.assertRaises(ModelError):
            ModelGateway("", "", "").decide("http", {})
        with self.assertRaises(ModelError):
            self.gateway.decide("http", {"text": "字"*160000})
        self.assertIsNone(self.received)


if __name__ == "__main__":
    unittest.main()
