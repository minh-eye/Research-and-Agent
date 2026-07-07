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

## 대화 내용 자동 저장 (SessionEnd hook)

이 저장소 디렉터리에서 로컬 Claude Code CLI 세션을 종료하면(`/clear`, 세션 종료 등),
`.claude/hooks/save-session-to-obsidian.mjs` 스크립트가 대화 내용을 Markdown 노트로 변환해
Obsidian vault에 자동 저장한다 (`Claude Conversations/` 폴더). 설정은 `.claude/settings.json`의
`SessionEnd` hook에 등록되어 있다.

이 저장소는 여러 사람이 함께 쓸 수 있으므로, 각자의 vault 경로를 코드에 직접 넣지 않고
환경 변수 `OBSIDIAN_VAULT_PATH`로 받는다. **이 환경 변수를 설정해야만 저장 기능이 동작한다**
(설정하지 않으면 조용히 건너뛴다).

### Windows에서 설정하는 방법

명령 프롬프트를 새로 열고 (한 번만 실행하면 계정에 영구 저장됨):

```
setx OBSIDIAN_VAULT_PATH "C:\Users\USER\Documents\MyVault"
```

`"C:\Users\USER\Documents\MyVault"` 자리에 실제 Obsidian vault 폴더의 전체 경로를 넣는다
(Obsidian 설정 → About → vault 위치에서 확인 가능). 설정 후 명령 프롬프트를 재시작해야 반영된다.

### macOS/Linux에서 설정하는 방법

셸 설정 파일(`~/.zshrc`, `~/.bashrc` 등)에 추가:

```bash
export OBSIDIAN_VAULT_PATH="/Users/me/Documents/MyVault"
```

### 참고

- 이 hook은 **로컬에서 실행하는 Claude Code CLI 세션에서만 동작**한다. 이 vault 폴더는 로컬
  디스크 경로이기 때문에, 원격/클라우드 세션(Claude Code on the web, Cowork 등)이나 claude.ai
  일반 채팅에서는 이 자동 저장이 동작하지 않는다.
- 그런 세션의 대화를 Obsidian에 남기고 싶다면, 로컬 Claude Code 세션 안에서 MCP로 연결된
  Obsidian에 수동으로 저장해달라고 요청하면 된다 (아래 "다른 세션(챗/Cowork) 대화 저장하기" 참고).

### 다른 세션(claude.ai 챗 / Cowork) 대화 저장하기

claude.ai 웹/앱 채팅이나 Cowork처럼 로컬 파일 접근이 없는 세션은 hook으로 자동 저장이 안 되므로,
아래 절차로 수동 저장한다.

1. 저장하고 싶은 대화를 claude.ai(또는 Cowork)에서 연 상태로, 대화 내용을 복사한다
   (메시지 하나하나 또는 전체 스레드).
2. 로컬 PC에서 이 저장소 디렉터리(`.mcp.json`이 있는 곳)로 이동해 `claude`를 실행한다.
3. 복사한 대화 내용을 붙여넣고 이렇게 요청한다:
   ```
   아래는 claude.ai에서 나눈 대화야. 이 내용을 Obsidian vault의 "Claude Conversations" 폴더에
   Markdown 노트로 저장해줘.

   (여기에 복사한 대화 붙여넣기)
   ```
4. Claude Code가 연결된 `obsidian` MCP 서버의 노트 생성 도구를 사용해 vault에 파일을 만든다.

이 방법은 완전 자동은 아니지만, 원하는 대화만 골라서 저장할 수 있다는 장점이 있다.
