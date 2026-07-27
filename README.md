# FastMCP 测试服务

这是一个使用 FastMCP 创建的本地 MCP 测试服务，包含客户信息、收货地址、最近订单等模拟接口，并支持 `stdio`、`streamable-http`、`sse` 以及双路由兼容模式。

## 1. 创建本地虚拟环境

在项目根目录执行：

```powershell
D:/Programs/python/Python312/python.exe -m venv .venv
```

激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 阻止脚本执行，可以在当前窗口临时放开策略：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2. 安装依赖

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. 启动服务

### 推荐：双路由兼容模式

默认启动方式就是 `dual` 模式，会同时提供 `/mcp` 和 `/sse`：

```powershell
.\.venv\Scripts\python.exe .\server.py --host 0.0.0.0 --port 8000
```

等价于：

```powershell
.\.venv\Scripts\python.exe .\server.py --transport dual --host 0.0.0.0 --port 8000
```

启动后可用地址：

```text
http://127.0.0.1:8000/mcp
http://127.0.0.1:8000/sse
```

内网访问时，把 `127.0.0.1` 替换成本机 IPv4，例如：

```text
http://10.10.31.111:8000/mcp
http://10.10.31.111:8000/sse
```

查询本机 IPv4：

```powershell
ipconfig
```

### 只启动 streamable HTTP

```powershell
.\.venv\Scripts\python.exe .\server.py --transport http --host 0.0.0.0 --port 8000 --path /mcp
```

访问地址：

```text
http://127.0.0.1:8000/mcp
```

### 只启动 SSE

```powershell
.\.venv\Scripts\python.exe .\server.py --transport sse --host 0.0.0.0 --port 8000
```

默认 SSE 地址：

```text
http://127.0.0.1:8000/sse
```

也可以显式指定：

```powershell
.\.venv\Scripts\python.exe .\server.py --transport sse --host 0.0.0.0 --port 8000 --path /sse
```

### 只启动 stdio

`stdio` 主要用于 VS Code、Claude Desktop 等本地 MCP 客户端直接拉起进程，不提供 HTTP 地址。

```powershell
.\.venv\Scripts\python.exe .\server.py --transport stdio
```

## 4. 已暴露的 MCP 能力

### Tools

- `add(a: float, b: float) -> float`：两个数相加，当前模拟逻辑为 `a + b + 3`
- `get_customer_info(customer_code: str) -> dict`：根据客户编码获取客户信息
- `get_customer_receiving_addresses(customer_code: str) -> dict`：根据客户编码获取收货地址信息
- `get_customer_recent_orders(customer_code: str) -> dict`：根据客户编码获取最近订单信息，包含订单头和订单明细

### Resource

- `demo://status`：服务状态资源

### Prompt

- `greeting_prompt(name: str = "developer") -> str`：示例 prompt

## 5. MCP 路由说明

MCP 不是 REST API，所以不能直接访问下面这种地址来获取能力列表：

```text
http://127.0.0.1:8000/tools
http://127.0.0.1:8000/prompts
```

标准能力是通过 MCP JSON-RPC 方法获取的，例如：

```text
tools/list
tools/call
prompts/list
prompts/get
resources/list
resources/read
```

其中：

- `/mcp` 是 streamable HTTP MCP endpoint
- `/sse` 是 SSE 长连接入口
- `/messages/?session_id=...` 是 SSE 模式下客户端发送 JSON-RPC 消息的地址

## 6. 使用 FastMCP Client 验证

验证 `/mcp`：

```powershell
.\.venv\Scripts\python.exe -c "
import asyncio
from fastmcp import Client

async def main():
    async with Client('http://127.0.0.1:8000/mcp') as client:
        tools = await client.list_tools()
        print([tool.name for tool in tools])
        result = await client.call_tool('get_customer_info', {'customer_code': '21444887'})
        print(result.data)

asyncio.run(main())
"
```

验证 `/sse`：

```powershell
.\.venv\Scripts\python.exe -c "
import asyncio
from fastmcp import Client

async def main():
    async with Client('http://127.0.0.1:8000/sse') as client:
        tools = await client.list_tools()
        print([tool.name for tool in tools])
        result = await client.call_tool('get_customer_info', {'customer_code': '21444887'})
        print(result.data)

asyncio.run(main())
"
```

## 7. SSE 模式 curl 示例

先在第一个窗口打开 SSE 长连接：

```powershell
curl.exe -N http://127.0.0.1:8000/sse
```

输出中会出现类似：

```text
event: endpoint
data: /messages/?session_id=xxxx
```

把 `session_id` 对应的地址复制出来，在第二个窗口发送 MCP JSON-RPC 请求。

初始化：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/messages/?session_id=xxxx" `
  -H "Content-Type: application/json" `
  -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"curl-demo\",\"version\":\"1.0.0\"}}}"
```

发送 initialized 通知：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/messages/?session_id=xxxx" `
  -H "Content-Type: application/json" `
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\",\"params\":{}}"
```

获取 prompt 列表：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/messages/?session_id=xxxx" `
  -H "Content-Type: application/json" `
  -d "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"prompts/list\",\"params\":{}}"
```

调用客户信息 tool：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/messages/?session_id=xxxx" `
  -H "Content-Type: application/json" `
  -d "{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"get_customer_info\",\"arguments\":{\"customer_code\":\"21444887\"}}}"
```

响应内容会返回到第一个 `curl.exe -N /sse` 窗口。

## 8. VS Code MCP 配置示例

如果使用 stdio 模式，可以在 VS Code MCP 配置中使用：

```json
{
  "servers": {
    "fastmcp-demo": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/Scripts/python.exe",
      "args": ["${workspaceFolder}/server.py", "--transport", "stdio"]
    }
  }
}
```

## 9. 常见问题

### 8000 端口被占用

如果启动时报错 `WinError 10048`，说明端口已被占用。可以换端口：

```powershell
.\.venv\Scripts\python.exe .\server.py --host 0.0.0.0 --port 8001
```

### 内网 IP 不能访问

确认启动时使用了：

```text
--host 0.0.0.0
```

如果仍然不能访问，检查 Windows 防火墙是否放行对应端口，例如 `8000`。

### 浏览器打开 /mcp 或 /sse 看起来不正常

这是正常现象。MCP endpoint 不是普通网页，需要 MCP 客户端按协议发送 `initialize`、`tools/list`、`tools/call` 等 JSON-RPC 消息。