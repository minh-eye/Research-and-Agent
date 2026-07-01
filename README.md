# Research-and-Agent

에이전트 팀 설계 및 스킬 자동 생성을 위한 하네스(harness) 기반 프로젝트.

`revfactory/harness` v1.2.0을 Claude Code 환경에 맞게 설치하여 사용한다.

## Obsidian 연동 (MCP)

[obsidian-claude-code-mcp](https://github.com/iansinnott/obsidian-claude-code-mcp) 플러그인을 통해
Claude Code가 로컬 Obsidian vault를 읽고 조작할 수 있도록 연동한다. 이 저장소의 `.mcp.json`에
`obsidian` MCP 서버가 이미 등록되어 있으므로, 아래 절차대로 Obsidian 쪽 설정만 마치면 이 프로젝트
디렉터리에서 `claude`를 실행할 때 자동으로 연결된다.

### 설정 방법

1. Obsidian의 **커뮤니티 플러그인(Community plugins)** 마켓플레이스에서 `Claude Code MCP` 플러그인을
   설치하고 활성화한다.
2. 플러그인 설정에서 서버가 켜져 있는지 확인한다. 기본 포트는 `22360`이며, 충돌 시 플러그인
   설정에서 변경할 수 있다. 포트를 바꾼 경우 이 저장소의 `.mcp.json`에 있는 URL도 동일하게
   수정해야 한다.
3. Obsidian에서 연동할 vault를 열어둔 상태로 유지한다 (서버는 Obsidian이 실행 중일 때만 동작).
4. 이 저장소 루트에서 `claude`를 실행하면 `.mcp.json`에 정의된 `obsidian` 서버(SSE,
   `http://localhost:22360/sse`)에 자동으로 연결된다. Claude Code 안에서 `/mcp` 명령으로 연결
   상태를 확인할 수 있다.

### Claude Desktop에서 사용하는 경우

Claude Desktop은 원격 MCP 서버에 접속하기 위해 `mcp-remote` 브리지가 필요하다.
`claude_desktop_config.json`(macOS: `$HOME/Library/Application Support/Claude/claude_desktop_config.json`,
Windows: `%APPDATA%\Claude\claude_desktop_config.json`)에 아래 내용을 추가한 뒤 Claude Desktop을
재시작한다.

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "npx",
      "args": ["mcp-remote", "http://localhost:22360/sse"],
      "env": {}
    }
  }
}
```
