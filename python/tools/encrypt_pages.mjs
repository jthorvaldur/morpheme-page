#!/usr/bin/env node
/**
 * Encrypts HTML files with AES-256-GCM and wraps them in a password-gate page.
 * Uses Web Crypto API (Node 18+) for encryption compatible with browser decryption.
 *
 * Session flow: password entered once at index → stored in sessionStorage →
 * sub-pages auto-decrypt without re-prompting.
 *
 * Usage: node encrypt_pages.mjs <password> <input_dir> <output_dir>
 */

import { webcrypto } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from 'node:fs';
import { join, basename } from 'node:path';

const { subtle } = webcrypto;

const PASSWORD = process.argv[2];
const INPUT_DIR = process.argv[3];
const OUTPUT_DIR = process.argv[4];

if (!PASSWORD || !INPUT_DIR || !OUTPUT_DIR) {
  console.error('Usage: node encrypt_pages.mjs <password> <input_dir> <output_dir>');
  process.exit(1);
}

async function deriveKey(password, salt) {
  const enc = new TextEncoder();
  const keyMaterial = await subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveKey']);
  return subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt']
  );
}

async function encryptContent(plaintext, password) {
  const enc = new TextEncoder();
  const salt = webcrypto.getRandomValues(new Uint8Array(16));
  const iv = webcrypto.getRandomValues(new Uint8Array(12));
  const key = await deriveKey(password, salt);
  const encrypted = await subtle.encrypt({ name: 'AES-GCM', iv }, key, enc.encode(plaintext));
  return {
    salt: Buffer.from(salt).toString('base64'),
    iv: Buffer.from(iv).toString('base64'),
    data: Buffer.from(encrypted).toString('base64'),
  };
}

function subPageHTML(title, blob) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${title} — Protected</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #0a0a0a; color: #c0c0c0;
    font-family: 'JetBrains Mono', monospace;
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh;
  }
  .gate {
    text-align: center; max-width: 480px; padding: 40px;
    border: 1px solid #222; border-radius: 8px;
    background: #111;
  }
  .gate h1 { color: #c0a060; font-size: 1.1rem; margin-bottom: 8px; }
  .gate p { font-size: 0.8rem; color: #666; margin-bottom: 24px; }
  .gate input {
    background: #1a1a1a; border: 1px solid #333; color: #e0e0e0;
    padding: 12px 16px; font-family: inherit; font-size: 1rem;
    width: 100%; border-radius: 4px; margin-bottom: 12px;
    text-align: center; letter-spacing: 2px;
  }
  .gate input:focus { outline: none; border-color: #c0a060; }
  .gate button {
    background: #c0a060; color: #0a0a0a; border: none;
    padding: 10px 32px; font-family: inherit; font-size: 0.9rem;
    font-weight: 700; border-radius: 4px; cursor: pointer;
    letter-spacing: 1px;
  }
  .gate button:hover { background: #d4b470; }
  .error { color: #ff4444; font-size: 0.8rem; margin-top: 12px; display: none; }
  .lock-icon { font-size: 2rem; margin-bottom: 16px; color: #333; }
  .loading { color: #c0a060; font-size: 0.9rem; }
</style>
</head>
<body>
<div class="gate" id="gate">
  <div class="lock-icon">&#x1f512;</div>
  <h1>PROTECTED CONTENT</h1>
  <p id="gate-msg">Enter the access key to continue</p>
  <input type="password" id="pw" placeholder="access key" autofocus
    onkeydown="if(event.key==='Enter')decrypt()">
  <br>
  <button onclick="decrypt()">UNLOCK</button>
  <div class="error" id="err">Incorrect key. Try again.</div>
</div>
<script>
const BLOB = ${JSON.stringify(blob)};
const SESSION_KEY = 'qwl_key';

async function deriveKey(password, salt) {
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveKey']);
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['decrypt']
  );
}

function b64ToArr(b64) {
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return arr;
}

async function decryptWithPassword(pw) {
  const salt = b64ToArr(BLOB.salt);
  const iv = b64ToArr(BLOB.iv);
  const data = b64ToArr(BLOB.data);
  const key = await deriveKey(pw, salt);
  const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, data);
  return new TextDecoder().decode(decrypted);
}

async function decrypt() {
  const pw = document.getElementById('pw').value;
  if (!pw) return;
  try {
    const html = await decryptWithPassword(pw);
    sessionStorage.setItem(SESSION_KEY, pw);
    document.open();
    document.write(html);
    document.close();
  } catch (e) {
    document.getElementById('err').style.display = 'block';
    document.getElementById('pw').value = '';
    document.getElementById('pw').focus();
  }
}

// Auto-decrypt if session key exists (user already authenticated at index)
(async function autoDecrypt() {
  const storedKey = sessionStorage.getItem(SESSION_KEY);
  if (!storedKey) return;
  try {
    document.getElementById('gate-msg').textContent = 'Authenticating...';
    document.getElementById('pw').style.display = 'none';
    document.querySelector('button').style.display = 'none';
    const html = await decryptWithPassword(storedKey);
    document.open();
    document.write(html);
    document.close();
  } catch (e) {
    // Stored key is wrong/expired — show manual prompt
    document.getElementById('gate-msg').textContent = 'Session expired. Enter the access key.';
    document.getElementById('pw').style.display = '';
    document.querySelector('button').style.display = '';
    sessionStorage.removeItem(SESSION_KEY);
  }
})();
</script>
</body>
</html>`;
}

async function main() {
  if (!existsSync(OUTPUT_DIR)) mkdirSync(OUTPUT_DIR, { recursive: true });

  const files = readdirSync(INPUT_DIR).filter(f => f.endsWith('.html'));
  console.log(`Encrypting ${files.length} files with AES-256-GCM...`);

  for (const file of files) {
    const content = readFileSync(join(INPUT_DIR, file), 'utf-8');
    const title = file.replace('.html', '').replace(/_/g, ' ').replace(/-/g, ' ');
    const blob = await encryptContent(content, PASSWORD);
    const wrapped = subPageHTML(title, blob);
    writeFileSync(join(OUTPUT_DIR, file), wrapped);
    console.log(`  ✓ ${file} (${(content.length / 1024).toFixed(1)}KB → encrypted)`);
  }

  console.log(`\nDone. Output: ${OUTPUT_DIR}/`);
}

main().catch(e => { console.error(e); process.exit(1); });
