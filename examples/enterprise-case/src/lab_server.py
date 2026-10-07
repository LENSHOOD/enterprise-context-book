"""Serve the built book and Northstar API on loopback, with no shell endpoint."""
from __future__ import annotations

import argparse
from functools import partial
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from workbench import WorkspaceStore, source_revision

CASE_ROOT = Path(__file__).resolve().parents[1]
ROOT = CASE_ROOT.parent.parent


class LabHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, store: WorkspaceStore, directory: str, **kwargs):
        self.store = store
        super().__init__(*args, directory=directory, **kwargs)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def reply(self, status: int, data: dict, cookie: str | None = None):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        if cookie:
            self.send_header("Set-Cookie", f"northstar_lab={cookie}; Path=/; HttpOnly; SameSite=Strict; Max-Age=2592000")
        self.end_headers()
        self.wfile.write(raw)

    def valid_host(self) -> bool:
        return self.headers.get("Host") in (f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}")

    def do_GET(self):
        if not self.valid_host():
            return self.reply(403, {"error": "只接受本地同源请求"})
        path = urlsplit(self.path).path
        if path == "/api/health":
            return self.reply(200, {"service": "northstar-lab", "source_revision": source_revision(), "simulation": True})
        if path.startswith("/api/"):
            return self.reply(404, {"error": "接口不存在"})
        root = Path(self.directory).resolve()
        candidate = (root / unquote(path).lstrip("/")).resolve()
        if not candidate.is_relative_to(root):
            return self.reply(403, {"error": "路径不在书站中"})
        if candidate.is_dir():
            candidate = candidate / "index.html"
        elif not candidate.suffix:
            candidate = candidate.with_suffix(".html")
        # Clean URLs and directory indexes may introduce a new symlink.
        candidate = candidate.resolve()
        if not candidate.is_relative_to(root):
            return self.reply(403, {"error": "路径不在书站中"})
        if not candidate.is_file():
            return self.reply(404, {"error": "页面不存在，请先运行 npm run docs:build"})
        self.path = "/" + candidate.relative_to(root).as_posix()
        super().do_GET()

    def do_HEAD(self):
        # Prevent SimpleHTTPRequestHandler from exposing a directory listing.
        self.send_error(405, "Use GET")

    def do_POST(self):
        origin = self.headers.get("Origin")
        if (not self.valid_host() or self.headers.get("X-Northstar-Lab") != "1"
                or (origin and origin != f"http://{self.headers.get('Host')}")
                or self.headers.get("Content-Type", "").split(";")[0] != "application/json"):
            return self.reply(403, {"error": "只接受本地页面的结构化请求"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 16384:
                return self.reply(413, {"error": "请求大小不合法"})
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError("请求必须是对象")
            path = urlsplit(self.path).path
            if path == "/api/session":
                identity = self.store.create()
                return self.reply(200, {"created": True}, cookie=identity)
            if path != "/api/lab":
                return self.reply(404, {"error": "接口不存在"})
            cookies = SimpleCookie(self.headers.get("Cookie", ""))
            identity = cookies["northstar_lab"].value if "northstar_lab" in cookies else ""
            return self.reply(200, self.store.call(identity, payload))
        except PermissionError as error:
            self.reply(403, {"error": str(error)})
        except (ValueError, KeyError, TypeError) as error:
            self.reply(400, {"error": str(error)})
        except Exception:
            self.log_error("Northstar request failed")
            self.reply(500, {"error": "本地实验处理失败；请检查服务终端"})


def make_server(port: int, database: Path, site: Path) -> ThreadingHTTPServer:
    handler = partial(LabHandler, store=WorkspaceStore(database), directory=str(site))
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--database", type=Path, default=ROOT / ".northstar-lab/workspaces.sqlite3")
    parser.add_argument("--site", type=Path, default=ROOT / "book/.vitepress/dist")
    args = parser.parse_args()
    if not (args.site / "index.html").is_file():
        parser.error("请先在仓库根目录执行 npm run docs:build")
    try:
        server = make_server(args.port, args.database, args.site)
    except OSError as error:
        parser.error(f"无法启动本地服务：{error}。可用 --port 8766 选择其他端口。")
    print(f"Northstar 教学工作台：http://127.0.0.1:{server.server_port}/lab\n数据保存：{args.database}\n业务、角色、时钟均为模拟；按 Ctrl+C 停止。", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
