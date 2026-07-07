// 프록시 엔드포인트: 브라우저는 API 키를 절대 다루지 않는다.
// - 비밀번호(x-app-password)를 APP_PASSWORD 환경변수와 대조한다.
// - 통과하면 Anthropic Messages API로 요청을 그대로 전달한다.
// - Vercel Serverless Function과 번들 Node 서버(server.js) 양쪽에서 재사용한다.

const ANTHROPIC_URL = "https://api.anthropic.com/v1/messages";
const ANTHROPIC_VERSION = "2023-06-01";
const DEFAULT_APP_PASSWORD = "AISTP26";

function readJsonBody(req) {
  if (req.body !== undefined && req.body !== null) {
    if (typeof req.body === "string") {
      return Promise.resolve(req.body.trim() ? JSON.parse(req.body) : {});
    }
    return Promise.resolve(req.body);
  }
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (chunk) => { data += chunk; });
    req.on("end", () => {
      try { resolve(data.trim() ? JSON.parse(data) : {}); }
      catch (e) { reject(new Error("잘못된 JSON 요청입니다.")); }
    });
    req.on("error", reject);
  });
}

function sendJson(res, status, payload) {
  res.writeHead(status, { "content-type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(payload));
}

module.exports = async function messagesHandler(req, res) {
  if (req.method !== "POST") {
    return sendJson(res, 405, { error: { message: "Method Not Allowed" } });
  }

  let body;
  try {
    body = await readJsonBody(req);
  } catch (e) {
    return sendJson(res, 400, { error: { message: (e && e.message) || "잘못된 요청입니다." } });
  }

  // APP_PASSWORD를 비워두면(빈 문자열) 게이트를 사용하지 않는다.
  // 값을 지정하지 않으면 기본값(AISTP26)을 사용한다.
  const required = process.env.APP_PASSWORD === "" ? "" : (process.env.APP_PASSWORD || DEFAULT_APP_PASSWORD);
  const provided = req.headers["x-app-password"] || "";

  if (required && provided !== required) {
    return sendJson(res, 401, { error: { message: "비밀번호가 올바르지 않습니다." } });
  }

  // 게이트 통과 확인용 핑 — Anthropic을 호출하지 않는다.
  if (body && body.__authcheck) {
    return sendJson(res, 200, { ok: true });
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return sendJson(res, 500, { error: { message: "서버에 ANTHROPIC_API_KEY가 설정되지 않았습니다." } });
  }

  const upstreamBody = {
    model: body.model,
    max_tokens: body.max_tokens,
    system: body.system,
    messages: body.messages
  };
  if (body.tools) upstreamBody.tools = body.tools;

  try {
    const upstream = await fetch(ANTHROPIC_URL, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": ANTHROPIC_VERSION
      },
      body: JSON.stringify(upstreamBody)
    });
    const text = await upstream.text();
    res.writeHead(upstream.status, { "content-type": "application/json; charset=utf-8" });
    res.end(text);
  } catch (e) {
    sendJson(res, 502, { error: { message: "Anthropic API 호출에 실패했습니다: " + ((e && e.message) || String(e)) } });
  }
};
