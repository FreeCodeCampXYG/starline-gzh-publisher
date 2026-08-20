#!/usr/bin/env node
/**
 * publish-wechat.mjs — local sidecar for "发布到公众号草稿".
 *
 * Zero-dependency (Node >= 18: global fetch / FormData / Blob).
 * Two jobs:
 *   1. Serve the tool HTML files at http://127.0.0.1:PORT/ (so the publish
 *      button POSTs same-origin — no CORS / mixed-content headaches).
 *   2. POST /api/draft  → create a WeChat Official Account draft.
 *
 * Setup: copy .env.example to .env, fill in your credentials, then `npm start`.
 * See README.md for the WeChat account requirements (AppID/AppSecret + IP 白名单).
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TOOLS_DIR = path.resolve(__dirname, '..', 'tools'); // 静态文件根目录 = tools/
const CACHE_FILE = path.join(__dirname, '.cache.json');

// ── .env loader (no dependency) ──────────────────────────────────────────────
function loadEnv() {
  const file = path.join(__dirname, '.env');
  if (!fs.existsSync(file)) return {};
  const out = {};
  for (const raw of fs.readFileSync(file, 'utf8').split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    const i = line.indexOf('=');
    if (i < 0) continue;
    const key = line.slice(0, i).trim();
    let val = line.slice(i + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    out[key] = val;
  }
  return out;
}

const env = { ...loadEnv(), ...process.env };
const PORT = Number(env.PORT || 3007);
const APPID = env.WECHAT_APPID || '';
const SECRET = env.WECHAT_APPSECRET || '';
const DEFAULT_AUTHOR = env.WECHAT_AUTHOR || '';
const THUMB_MEDIA_ID = env.WECHAT_THUMB_MEDIA_ID || '';
const DEFAULT_COVER = env.WECHAT_DEFAULT_COVER || '';

const API = 'https://api.weixin.qq.com';

// Friendly hints for the WeChat error codes people actually hit.
const ERRCODE_HINT = {
  40001: 'appsecret 不对，或 access_token 失效（检查 WECHAT_APPSECRET）',
  40013: 'appid 不对（检查 WECHAT_APPID）',
  40164: '调用来源 IP 不在白名单里 —— 去公众号后台「设置与开发 → 基本配置 → IP 白名单」加上本机出口 IP',
  41001: '缺少 access_token',
  45009: '接口调用超过频率限制',
  48001: 'API 未授权 —— 去公众号后台「接口权限」确认草稿箱/发布接口可用',
  53500: '发布能力被封禁',
};
const wxError = (j) => {
  const code = j.errcode;
  const hint = ERRCODE_HINT[code];
  return `微信返回错误 ${code}: ${j.errmsg || ''}${hint ? ' —— ' + hint : ''}`;
};

// ── cache (token in-memory; default-thumb media_id on disk) ──────────────────
function readCache() {
  try { return JSON.parse(fs.readFileSync(CACHE_FILE, 'utf8')); } catch { return {}; }
}
function writeCache(patch) {
  const next = { ...readCache(), ...patch };
  try { fs.writeFileSync(CACHE_FILE, JSON.stringify(next, null, 2)); } catch { /* ignore */ }
  return next;
}

let tokenCache = { token: '', exp: 0 };
async function getAccessToken() {
  const now = Date.now();
  if (tokenCache.token && now < tokenCache.exp) return tokenCache.token;
  const url = `${API}/cgi-bin/token?grant_type=client_credential&appid=${encodeURIComponent(APPID)}&secret=${encodeURIComponent(SECRET)}`;
  const j = await fetch(url).then((r) => r.json());
  if (!j.access_token) throw new Error(wxError(j));
  // WeChat tokens last 7200s; refresh 5 min early.
  tokenCache = { token: j.access_token, exp: now + (j.expires_in - 300) * 1000 };
  return tokenCache.token;
}

// ── image helpers ────────────────────────────────────────────────────────────
async function srcToBlob(src) {
  if (src.startsWith('data:')) {
    const m = /^data:([^;,]+)?(;base64)?,(.*)$/s.exec(src);
    if (!m) throw new Error('无法解析 data URI 图片');
    const mime = m[1] || 'image/png';
    const buf = m[2] ? Buffer.from(m[3], 'base64') : Buffer.from(decodeURIComponent(m[3]), 'utf8');
    return { blob: new Blob([buf], { type: mime }), ext: (mime.split('/')[1] || 'png').replace('jpeg', 'jpg') };
  }
  if (/^https?:\/\//.test(src)) {
    const r = await fetch(src);
    if (!r.ok) throw new Error(`拉取图片失败 ${r.status}: ${src.slice(0, 80)}`);
    const mime = r.headers.get('content-type') || 'image/png';
    const buf = Buffer.from(await r.arrayBuffer());
    return { blob: new Blob([buf], { type: mime }), ext: (mime.split('/')[1] || 'png').split(';')[0].replace('jpeg', 'jpg') };
  }
  throw new Error(`不支持的图片来源: ${src.slice(0, 40)}`);
}

// Upload an inline content image → returns a wechat-hosted URL (no quota cost).
async function uploadContentImage(token, src) {
  const { blob, ext } = await srcToBlob(src);
  const fd = new FormData();
  fd.append('media', blob, `img.${ext}`);
  const j = await fetch(`${API}/cgi-bin/media/uploadimg?access_token=${token}`, { method: 'POST', body: fd }).then((r) => r.json());
  if (!j.url) throw new Error(wxError(j));
  return j.url;
}

// Upload a permanent image material → returns { media_id } (used for the cover thumb).
async function uploadPermanentImage(token, blob, ext) {
  const fd = new FormData();
  fd.append('media', blob, `cover.${ext}`);
  const j = await fetch(`${API}/cgi-bin/material/add_material?access_token=${token}&type=image`, { method: 'POST', body: fd }).then((r) => r.json());
  if (!j.media_id) throw new Error(wxError(j));
  return j.media_id;
}

// Replace every <img src> in the html with a wechat-hosted url.
async function rewriteImages(token, html) {
  const srcs = [...html.matchAll(/<img[^>]+src=(["'])(.*?)\1/gis)].map((m) => m[2]);
  const uniq = [...new Set(srcs)].filter((s) => s.startsWith('data:') || /^https?:\/\//.test(s));
  let out = html;
  let uploaded = 0;
  for (const src of uniq) {
    if (/mmbiz\.qpic\.cn/.test(src)) continue; // already a wechat image
    try {
      const url = await uploadContentImage(token, src);
      out = out.split(src).join(url);
      uploaded++;
    } catch (e) {
      console.warn('  ! 图片上传失败，保留原图:', e.message);
    }
  }
  return { html: out, uploaded, total: uniq.length };
}

// Resolve the cover thumb_media_id (required by draft/add).
async function resolveThumb(token, bodyThumb, firstImageSrc) {
  if (bodyThumb) return bodyThumb;
  if (THUMB_MEDIA_ID) return THUMB_MEDIA_ID;
  if (DEFAULT_COVER) {
    const abs = path.isAbsolute(DEFAULT_COVER) ? DEFAULT_COVER : path.join(__dirname, DEFAULT_COVER);
    if (!fs.existsSync(abs)) throw new Error(`WECHAT_DEFAULT_COVER 指向的文件不存在: ${abs}`);
    const mtime = fs.statSync(abs).mtimeMs;
    const cache = readCache();
    if (cache.coverPath === abs && cache.coverMtime === mtime && cache.coverMediaId) return cache.coverMediaId;
    const ext = (path.extname(abs).slice(1) || 'png').replace('jpeg', 'jpg');
    const blob = new Blob([fs.readFileSync(abs)], { type: `image/${ext}` });
    const mediaId = await uploadPermanentImage(token, blob, ext);
    writeCache({ coverPath: abs, coverMtime: mtime, coverMediaId: mediaId });
    return mediaId;
  }
  if (firstImageSrc) {
    const { blob, ext } = await srcToBlob(firstImageSrc);
    return uploadPermanentImage(token, blob, ext);
  }
  throw new Error('缺少封面图：正文没有图片，且未配置 WECHAT_THUMB_MEDIA_ID / WECHAT_DEFAULT_COVER');
}

// ── the draft flow ───────────────────────────────────────────────────────────
async function createDraft({ title, author, digest, contentHtml, thumbMediaId }) {
  if (!APPID || !SECRET) throw new Error('未配置凭据：请在 server/.env 填写 WECHAT_APPID 和 WECHAT_APPSECRET');
  if (!title || !title.trim()) throw new Error('缺少标题');
  if (!contentHtml || !contentHtml.trim()) throw new Error('缺少正文内容');

  const token = await getAccessToken();

  const firstImg = (/<img[^>]+src=(["'])(.*?)\1/is.exec(contentHtml) || [])[2] || '';
  const thumb = await resolveThumb(token, thumbMediaId, firstImg);

  const { html, uploaded, total } = await rewriteImages(token, contentHtml);
  console.log(`  · 图片处理：${uploaded}/${total} 张上传到微信`);

  const article = {
    title: title.slice(0, 64),
    author: (author || DEFAULT_AUTHOR || '').slice(0, 8),
    digest: (digest || '').slice(0, 120),
    content: html,
    thumb_media_id: thumb,
    need_open_comment: 0,
    only_fans_can_comment: 0,
  };

  const j = await fetch(`${API}/cgi-bin/draft/add?access_token=${token}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    // WeChat wants raw UTF-8 bytes, not ascii-escaped JSON.
    body: Buffer.from(JSON.stringify({ articles: [article] }), 'utf8'),
  }).then((r) => r.json());

  if (!j.media_id) throw new Error(wxError(j));
  return { media_id: j.media_id, images: `${uploaded}/${total}`, thumb_media_id: thumb };
}

// ── static file serving ──────────────────────────────────────────────────────
const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.otf': 'font/otf',
};
function serveStatic(req, res) {
  let rel = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (rel === '/' || rel === '') rel = '/index.html';
  const abs = path.join(TOOLS_DIR, rel);
  if (!abs.startsWith(TOOLS_DIR)) { res.writeHead(403).end('forbidden'); return; }
  fs.readFile(abs, (err, data) => {
    if (err) { res.writeHead(404).end('not found'); return; }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(abs).toLowerCase()] || 'application/octet-stream' });
    res.end(data);
  });
}

// ── server ───────────────────────────────────────────────────────────────────
function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on('data', (c) => { size += c.length; if (size > 25 * 1024 * 1024) reject(new Error('请求体过大（>25MB）')); chunks.push(c); });
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}
const cors = (res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
};
const sendJson = (res, code, obj) => {
  cors(res);
  res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(obj));
};

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');

  if (req.method === 'OPTIONS') { cors(res); res.writeHead(204).end(); return; }

  if (url.pathname === '/health') {
    return sendJson(res, 200, { ok: true, hasCreds: Boolean(APPID && SECRET), port: PORT });
  }

  if (url.pathname === '/api/draft') {
    if (req.method !== 'POST') return sendJson(res, 405, { ok: false, error: 'method not allowed' });
    try {
      const body = JSON.parse(await readBody(req) || '{}');
      console.log(`→ /api/draft  「${(body.title || '').slice(0, 30)}」`);
      const result = await createDraft(body);
      console.log(`✓ 草稿已创建 media_id=${result.media_id}`);
      return sendJson(res, 200, { ok: true, ...result });
    } catch (e) {
      console.error('✗', e.message);
      return sendJson(res, 200, { ok: false, error: e.message });
    }
  }

  return serveStatic(req, res);
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`\n烁皓工具 · 公众号发布服务`);
  console.log(`  本地地址: http://127.0.0.1:${PORT}/`);
  console.log(`  打开工具: http://127.0.0.1:${PORT}/md-to-wechat.html`);
  console.log(`  凭据状态: ${APPID && SECRET ? 'APPID/SECRET 已配置 ✓' : '⚠️  未配置，去 server/.env 填写'}`);
  console.log(`  停止服务: Ctrl+C\n`);
});
