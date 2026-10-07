import json
import os
import queue
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path


class RobloxMCPClient:
    def __init__(self, base_url=None, timeout=15, use_mock=False):
        self.timeout = timeout
        self.use_mock = bool(use_mock)
        self.base_url = base_url or os.environ.get("ROBLOX_MCP_URL") or os.environ.get("ROBLOX_STUDIO_MCP_URL")
        self.base_urls = []
        if self.base_url and str(self.base_url).startswith("http"):
            configured = str(self.base_url).rstrip("/")
            self.base_urls = [configured]
            self.base_url = configured

        self.launcher_path = self._resolve_launcher_path()
        self.process = None
        self.stdin = None
        self.stdout = None
        self.stderr = None
        self._stdout_queue = queue.Queue()
        self._stderr_buffer = []
        self._request_counter = 0
        self._last_error = None
        self.connected = False
        self.available_tools = []
        self.available_tool_definitions = []
        self.session_initialized = False
        self.backend = "http" if self.base_urls else "stdio"

    def _resolve_launcher_path(self):
        env_value = os.environ.get("ROBLOX_MCP_BAT")
        if env_value:
            return env_value
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return str(Path(local_app_data) / "Roblox" / "mcp.bat")
        return r"%LOCALAPPDATA%\Roblox\mcp.bat"

    @staticmethod
    def _normalize_tool_list(tools):
        if tools is None:
            return []

        ordered = []
        if isinstance(tools, dict):
            tools = list(tools.keys())

        for item in tools:
            if isinstance(item, str):
                ordered.append(item)
            elif isinstance(item, dict):
                name = item.get("name") or item.get("tool") or item.get("id")
                if name:
                    ordered.append(str(name))
        return ordered

    def _log(self, message):
        print(f"[RobloxMCPClient] {message}")

    def _start_stdio_process(self):
        if self.process is not None and self.process.poll() is None:
            return True

        if not os.path.exists(self.launcher_path):
            self._last_error = FileNotFoundError(f"Roblox MCP launcher not found: {self.launcher_path}")
            self.connected = False
            self._log(f"mcp.bat not found at {self.launcher_path}")
            return False

        try:
            self.process = subprocess.Popen(
                ["cmd.exe", "/c", self.launcher_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            self._last_error = exc
            self.connected = False
            self._log(f"Failed to launch Roblox Studio MCP via cmd.exe: {exc}")
            return False

        self.stdin = self.process.stdin
        self.stdout = self.process.stdout
        self.stderr = self.process.stderr
        self._stderr_buffer.clear()
        self._stdout_queue = queue.Queue()

        threading.Thread(target=self._pump_stdout, daemon=True).start()
        threading.Thread(target=self._pump_stderr, daemon=True).start()
        self._log(f"Started Roblox MCP launcher: {self.launcher_path}")
        return True

    def _pump_stdout(self):
        if self.stdout is None:
            return
        for raw_line in self.stdout:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                self._log(f"Ignoring non-JSON stdout line: {line}")
                continue
            self._stdout_queue.put(payload)

    def _pump_stderr(self):
        if self.stderr is None:
            return
        for raw_line in self.stderr:
            line = raw_line.strip()
            if not line:
                continue
            self._stderr_buffer.append(line)
            self._log(f"stderr: {line}")

    def _wait_for_response(self, request_id, timeout=None):
        deadline = time.monotonic() + (timeout if timeout is not None else self.timeout)
        while time.monotonic() < deadline:
            try:
                payload = self._stdout_queue.get(timeout=max(0.1, deadline - time.monotonic()))
            except queue.Empty:
                if self.process is not None and self.process.poll() is not None:
                    raise RuntimeError(f"Roblox MCP child process exited unexpectedly with code {self.process.returncode}")
                continue
            if payload.get("id") == request_id:
                return payload
            if payload.get("method") is not None:
                self._log(f"Ignoring notification: {payload.get('method')}")
        raise TimeoutError(f"Timed out waiting for MCP response id={request_id}")

    def _send_jsonrpc(self, method, params=None, request_id=None):
        if self.stdin is None:
            raise RuntimeError("Roblox MCP stdio client is not connected.")

        if request_id is None:
            self._request_counter += 1
            request_id = self._request_counter

        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}
        self.stdin.write(json.dumps(payload) + "\n")
        self.stdin.flush()
        return self._wait_for_response(request_id)

    def _send_notification(self, method, params=None):
        if self.stdin is None:
            raise RuntimeError("Roblox MCP stdio client is not connected.")
        payload = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        self.stdin.write(json.dumps(payload) + "\n")
        self.stdin.flush()

    def ensure_stdio_connection(self):
        if self.use_mock:
            self._last_error = RuntimeError("Mock backend is disabled for the production bridge.")
            self.connected = False
            return False

        if self.process is not None and self.process.poll() is None:
            if not self.session_initialized:
                return self._initialize_stdio_session()
            return self.connected

        return self._initialize_stdio_session()

    def _initialize_stdio_session(self):
        if not self._start_stdio_process():
            return False

        try:
            init_response = self._send_jsonrpc(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "ai-roblox-studio-extension", "version": "0.1.0"},
                },
                request_id=1,
            )
            if "result" not in init_response:
                self._last_error = ValueError(f"MCP initialize failed: {init_response}")
                return False
            self._send_notification("notifications/initialized", {})
            self.session_initialized = True
            self.connected = True
            self._log("Roblox Studio MCP session initialized successfully")
            return True
        except (TimeoutError, RuntimeError, ValueError) as exc:
            self._last_error = exc
            self.connected = False
            self.session_initialized = False
            self._log(f"Roblox MCP initialize failed: {exc}")
            return False

    def _legacy_http_request(self, path="", payload=None):
        if not self.base_urls:
            raise urllib.error.URLError("No legacy HTTP mock endpoint configured.")

        last_error = None
        for base_url in self.base_urls:
            try:
                self.base_url = base_url.rstrip("/")
                base = self.base_url.rstrip("/")
                url = base if not path else f"{base}{path}"
                data = None if payload is None else json.dumps(payload).encode("utf-8")
                method = "GET" if payload is None else "POST"
                request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method=method)
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = response.read()
                    return json.loads(raw.decode("utf-8"))
            except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                continue
        if last_error is not None:
            raise last_error
        raise urllib.error.URLError("No legacy HTTP Roblox Studio MCP endpoint responded.")

    def _legacy_http_discover_tools(self):
        try:
            response = self._legacy_http_request("/tools")
            if isinstance(response, dict):
                tools = response.get("tools") or response.get("available_tools") or []
                normalized = self._normalize_tool_list(tools)
                if normalized:
                    self.available_tools = normalized
                    self.available_tool_definitions = [
                        item for item in tools if isinstance(item, dict) and item.get("name")
                    ]
                    self.connected = True
                    return normalized
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            pass

        self.available_tools = []
        self.available_tool_definitions = []
        self.connected = False
        return []

    def _legacy_http_call_tool(self, tool_name, arguments=None):
        if not tool_name:
            raise ValueError("Tool name is required.")
        payload = {"tool": tool_name, "arguments": arguments or {}}
        try:
            response = self._legacy_http_request("", payload)
            if isinstance(response, dict):
                self.connected = True
                if tool_name not in self.available_tools:
                    self.available_tools.append(tool_name)
                return response
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            pass

        self.connected = False
        return {"ok": False, "error": f"Tool not available: {tool_name}"}

    def _stdio_discover_tools(self):
        if not self.ensure_stdio_connection():
            self.available_tools = []
            self.connected = False
            return []

        try:
            response = self._send_jsonrpc("tools/list")
        except (TimeoutError, RuntimeError, ValueError) as exc:
            self._last_error = exc
            self.connected = False
            self.available_tools = []
            self.available_tool_definitions = []
            return []

        result = response.get("result", {}) if isinstance(response, dict) else {}
        tools = result.get("tools", []) if isinstance(result, dict) else []
        normalized = self._normalize_tool_list(tools)
        self.available_tools = normalized
        self.available_tool_definitions = [
            item for item in tools if isinstance(item, dict) and item.get("name")
        ]
        self.connected = bool(normalized)
        return normalized

    def _stdio_call_tool(self, tool_name, arguments=None):
        if not tool_name:
            raise ValueError("Tool name is required.")

        if not self.session_initialized and not self._initialize_stdio_session():
            return {"ok": False, "error": str(self._last_error) if self._last_error else "Roblox MCP is unavailable."}

        try:
            response = self._send_jsonrpc("tools/call", {"name": tool_name, "arguments": arguments or {}})
        except (TimeoutError, RuntimeError, ValueError) as exc:
            self._last_error = exc
            self.connected = False
            return {"ok": False, "error": str(exc)}

        if isinstance(response, dict) and "error" in response:
            self.connected = False
            return {"ok": False, "error": response["error"]}

        result = response.get("result", {}) if isinstance(response, dict) else {}
        if isinstance(result, dict):
            raw_content = result.get("content")
            text_rows = []
            if isinstance(raw_content, list):
                for item in raw_content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_rows.append(str(item.get("text", "")))
                        elif item.get("text"):
                            text_rows.append(str(item.get("text")))
            if result.get("isError"):
                error_text = "\n".join(text_rows) or "Roblox Studio MCP tool call failed."
                return {"ok": False, "tool": tool_name, "error": error_text, "content": raw_content}
            if text_rows:
                return {"ok": True, "tool": tool_name, "content": raw_content, "text": "\n".join(text_rows), "raw": result}
            return {"ok": True, "tool": tool_name, "raw": result}

        return {"ok": True, "tool": tool_name, "raw": response}

    def get_status_snapshot(self):
        if not self.use_mock and (not self.connected or self.process is None or self.process.poll() is not None):
            self.ensure_stdio_connection()

        launcher_exists = os.path.exists(self.launcher_path)
        process_running = self.process is not None and self.process.poll() is None
        status = "not_connected"
        if self.connected:
            status = "connected"
        elif not launcher_exists:
            status = "launcher_missing"
        elif self.process is not None and self.process.poll() is not None:
            status = "process_crashed"
        elif self.use_mock:
            status = "mock_active"
        elif self.base_urls:
            status = "http_backend"

        return {
            "backend": self.backend,
            "status": status,
            "mcp_bat_found": launcher_exists,
            "process_running": process_running,
            "process_exit_code": getattr(self.process, "returncode", None),
            "studio_connected": self.connected,
            "tools": list(self.available_tools),
            "launcher_path": self.launcher_path,
            "last_error": str(self._last_error) if self._last_error else None,
        }

    def discover_tools(self):
        if not self.use_mock and not self.base_urls and self.backend == "stdio":
            self.ensure_stdio_connection()
        if self.use_mock or self.base_urls:
            return self._legacy_http_discover_tools()
        if self.backend == "stdio":
            return self._stdio_discover_tools()
        return self._legacy_http_discover_tools()

    def call_tool(self, tool_name, arguments=None):
        if not self.use_mock and not self.base_urls and self.backend == "stdio":
            self.ensure_stdio_connection()
        if self.use_mock or self.base_urls:
            return self._legacy_http_call_tool(tool_name, arguments)
        return self._stdio_call_tool(tool_name, arguments)

    def get_tool_schema(self):
        return [
            {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "inputSchema": tool.get("inputSchema", {"type": "object", "properties": {}}),
            }
            for tool in self.available_tool_definitions
        ]

    @staticmethod
    def _fallback_call(self, tool_name, arguments=None):
        args = arguments or {}
        if tool_name == "inspect_tree":
            return {"ok": True, "children": [{"Name": "Workspace", "ClassName": "Folder"}], "path": args.get("path", "Workspace")}
        if tool_name == "read_script":
            return {"ok": True, "path": args.get("path", "Workspace"), "source": "print('mock script loaded')\n"}
        if tool_name == "write_script":
            return {"ok": True, "path": args.get("path"), "written": True}
        if tool_name == "create_instance":
            return {"ok": True, "instance": args.get("className", "Part"), "name": args.get("name", "NewPart")}
        if tool_name == "set_property":
            return {"ok": True, "target": args.get("target"), "property": args.get("property"), "value": args.get("value")}
        if tool_name == "find_instance":
            return {"ok": True, "query": args.get("query"), "matches": []}
        if tool_name == "run_luau":
            return {"ok": True, "result": "mock luau executed"}
        if tool_name == "playtest_start":
            return {"ok": True, "status": "playtest_started"}
        if tool_name == "playtest_stop":
            return {"ok": True, "status": "playtest_stopped"}
        raise ValueError(f"Tool not available: {tool_name}")
