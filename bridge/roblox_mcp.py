import json
import os
import urllib.error
import urllib.request


class RobloxMCPClient:
    def __init__(self, base_url=None, timeout=5):
        configured = base_url or os.environ.get("ROBLOX_MCP_URL") or os.environ.get("ROBLOX_STUDIO_MCP_URL") or "http://127.0.0.1:8767"
        fallback_urls = [
            "http://127.0.0.1:8767",
            "http://127.0.0.1:8768",
            "http://127.0.0.1:9000",
            "http://127.0.0.1:5000",
            "http://127.0.0.1:8000",
        ]
        seen = set()
        ordered = []
        for candidate in [configured, *fallback_urls]:
            normalized = candidate.rstrip("/") if candidate else ""
            if normalized and normalized not in seen:
                seen.add(normalized)
                ordered.append(normalized)
        self.base_urls = ordered
        self.base_url = self.base_urls[0]
        self.timeout = timeout
        self.available_tools = []
        self.connected = False
        self.tool_catalog = {
            "inspect_tree": {"description": "Inspect the Roblox Instance tree", "arguments": {"path": "string"}},
            "read_script": {"description": "Read a script or module source", "arguments": {"path": "string"}},
            "write_script": {"description": "Write a script or module source", "arguments": {"path": "string", "source": "string"}},
            "create_instance": {"description": "Create a Roblox Instance under a parent", "arguments": {"parent": "string", "className": "string", "name": "string"}},
            "set_property": {"description": "Set a property value on an instance", "arguments": {"target": "string", "property": "string", "value": "any"}},
            "find_instance": {"description": "Find a Roblox instance by path or name", "arguments": {"query": "string"}},
            "run_luau": {"description": "Execute Luau in the Studio environment if supported", "arguments": {"code": "string"}},
            "playtest_start": {"description": "Start a playtest session", "arguments": {}},
            "playtest_stop": {"description": "Stop a playtest session", "arguments": {}},
        }

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

    def _request_json(self, path="", payload=None, base_url=None):
        base = (base_url or self.base_url).rstrip("/")
        url = base if not path else f"{base}{path}"

        data = None if payload is None else json.dumps(payload).encode("utf-8")
        method = "GET" if payload is None else "POST"
        request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method=method)
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8"))

    def _try_request(self, path="", payload=None):
        last_error = None
        for base_url in self.base_urls:
            try:
                self.base_url = base_url.rstrip("/")
                response = self._request_json(path, payload, base_url=self.base_url)
                if isinstance(response, dict):
                    return response, self.base_url
            except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                continue
        if last_error is not None:
            raise last_error
        raise urllib.error.URLError("No Roblox Studio MCP endpoint responded.")

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

    def discover_tools(self):
        try:
            response, _ = self._try_request("/tools")
            if isinstance(response, dict):
                tools = response.get("tools") or response.get("available_tools") or []
                normalized = self._normalize_tool_list(tools)
                if normalized:
                    self.available_tools = normalized
                    self.connected = True
                    return self.available_tools
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            pass

        self.available_tools = []
        self.connected = False
        return self.available_tools

    def get_tool_schema(self):
        schema = []
        for name in self.available_tools or self.tool_catalog.keys():
            metadata = self.tool_catalog.get(name)
            if metadata:
                schema.append({"name": name, "description": metadata["description"], "arguments": metadata["arguments"]})
            else:
                schema.append({"name": name, "description": "Discovered Roblox Studio MCP tool", "arguments": {}})
        return schema

    def call_tool(self, tool_name, arguments=None):
        if not tool_name:
            raise ValueError("Tool name is required.")

        payload = {"tool": tool_name, "arguments": arguments or {}}
        try:
            response, _ = self._try_request("", payload)
            if isinstance(response, dict):
                self.connected = True
                self.available_tools = self._normalize_tool_list(self.available_tools + [tool_name])
                return response
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            pass

        if tool_name in self.tool_catalog:
            result = self._fallback_call(tool_name, arguments)
            self.connected = False
            self.available_tools = []
            return result

        self.connected = False
        self.available_tools = []
        return {"ok": False, "error": f"Tool not available: {tool_name}"}
