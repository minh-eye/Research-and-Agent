// 로컬/자체 호스팅용 번들 Node 서버.
// 정적 파일(index.html)을 서빙하고, /api/messages 요청은 api/messages.js가 처리한다.
// 실행: ANTHROPIC_API_KEY=... APP_PASSWORD=AISTP26 node server.js

const http = require("http");
const fs = require("fs");
const path = require("path");
const messagesHandler = require("./api/messages.js");

const PORT = process.env.PORT || 8787;
const ROOT = __dirname;

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml"
};

function serveStatic(req, res, urlPath) {
  const rel = urlPath === "/" ? "index.html" : urlPath.replace(/^\/+/, "");
  const filePath = path.join(ROOT, rel);
  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403); res.end("Forbidden"); return;
  }
  fs.readFile(filePath, (err, data) => {
    if (err) { res.writeHead(404); res.end("Not found"); return; }
    res.writeHead(200, { "content-type": MIME[path.extname(filePath)] || "application/octet-stream" });
    res.end(data);
  });
}

const server = http.createServer((req, res) => {
  const urlPath = req.url.split("?")[0];
  if (urlPath === "/api/messages") return messagesHandler(req, res);
  serveStatic(req, res, urlPath);
});

server.listen(PORT, () => {
  console.log("Project Review app: http://localhost:" + PORT);
  if (!process.env.ANTHROPIC_API_KEY) {
    console.warn("경고: ANTHROPIC_API_KEY가 설정되지 않았습니다. 분석 요청이 실패합니다.");
  }
});
