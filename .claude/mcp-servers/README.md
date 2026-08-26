# MCP servers

Repo không có MCP bắt buộc. `.mcp.json` commit với `mcpServers: {}`.

Thêm server (filesystem, GitHub) chỉ khi cả team dùng. Đặt biến nhạy cảm trong `.claude/settings.local.json` hoặc môi trường `${TEN_BIEN}`, không hardcode.

Mẫu:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}" }
    }
  }
}
```
