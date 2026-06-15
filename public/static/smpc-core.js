// Shared SMPC protocol crypto, loaded by both party.html and aggregator.html.
//
// Everything that must be byte-identical between the two parties of a pair -
// the curve (P-256), the HKDF info string ("SMPC mask " + pair label), and
// the signed 64-bit BigInt conversion - lives here so the two pages can never
// diverge. The canonical message format and the lower-letter-adds sign
// convention must additionally match server.py (canonical_message) - keep
// them aligned if either side changes.

(function () {
  // Fixed-point scale: figures cross the wire as decimal-string integers
  // scaled by 10^6. Must match the server's interpretation.
  const SCALE = 1000000n;
  const toFixed = x => BigInt(Math.round(x * Number(SCALE)));

  // Bytes both sides sign/verify for a party-scoped POST. Must match
  // canonical_message in server.py exactly.
  function canonicalMessage(action, session, party, content) {
    return `${action}|${session}|${party}|${content}`;
  }

  // Sign convention for pair (i, j) with i < j: party i adds r_ij, party j
  // subtracts it. Returns the multiplier for `me`'s share.
  function maskSign(me, other) {
    return me < other ? 1n : -1n;
  }

  // --- Display helpers (not crypto; single-sourced so both pages agree) ---
  // fmt2: render a Number for DISPLAY at up to 2 dp, strip trailing zeros, never
  // show "-0" (RB-22). Display only - the wire/protocol arithmetic stays exact at
  // the 1e6 fixed-point SCALE; this just rounds what the user sees (e.g. an
  // average of 18835.6033... shows as 18835.6).
  function fmt2(x) {
    return x.toFixed(2).replace(/\.?0+$/, '').replace(/^-0$/, '0');
  }
  // escapeHtml: neutralise a peer/aggregator-supplied string before it touches
  // innerHTML (RB-47 defence-in-depth - the share validator already constrains
  // shares to decimals, but the guard belongs at the sink too).
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  // --- Base64 helpers (binary <-> ASCII) ---
  function b64encode(buf) {
    const bytes = new Uint8Array(buf);
    let s = '';
    for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
    return btoa(s);
  }
  function b64decode(s) {
    const bin = atob(s);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  // --- ECDH (P-256) + HKDF (SHA-256) for mask derivation ---
  async function generateECDHKeypair() {
    return crypto.subtle.generateKey(
      { name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]
    );
  }
  async function exportEcdhPubB64(kp) {
    const raw = await crypto.subtle.exportKey("raw", kp.publicKey);
    return b64encode(raw);
  }
  async function importEcdhPub(b64) {
    return crypto.subtle.importKey(
      "raw", b64decode(b64),
      { name: "ECDH", namedCurve: "P-256" }, false, []
    );
  }
  async function derivePairwiseMask(myPriv, theirPubB64, loLetter, hiLetter) {
    const theirPub = await importEcdhPub(theirPubB64);
    const sharedBits = await crypto.subtle.deriveBits(
      { name: "ECDH", public: theirPub }, myPriv, 256
    );
    const hkdfKey = await crypto.subtle.importKey(
      "raw", sharedBits, "HKDF", false, ["deriveBits"]
    );
    const info = new TextEncoder().encode("SMPC mask " + loLetter + hiLetter);
    const maskBits = await crypto.subtle.deriveBits(
      { name: "HKDF", hash: "SHA-256", salt: new Uint8Array(0), info },
      hkdfKey, 64
    );
    const bytes = new Uint8Array(maskBits);
    let u = 0n;
    for (const b of bytes) u = (u << 8n) | BigInt(b);
    return u >= (1n << 63n) ? u - (1n << 64n) : u;
  }

  // --- ECDSA (P-256, SHA-256) for share signatures ---
  async function generateSigningKeypair() {
    return crypto.subtle.generateKey(
      { name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]
    );
  }
  async function exportVkB64(kp) {
    const raw = await crypto.subtle.exportKey("raw", kp.publicKey);
    return b64encode(raw);
  }
  async function signMessage(sk, msg) {
    const sig = await crypto.subtle.sign(
      { name: "ECDSA", hash: { name: "SHA-256" } },
      sk, new TextEncoder().encode(msg)
    );
    return b64encode(sig);
  }
  async function importVk(b64) {
    return crypto.subtle.importKey(
      "raw", b64decode(b64),
      { name: "ECDSA", namedCurve: "P-256" }, false, ["verify"]
    );
  }
  async function verifyMessage(vkB64, sigB64, msg) {
    const vk = await importVk(vkB64);
    return crypto.subtle.verify(
      { name: "ECDSA", hash: { name: "SHA-256" } },
      vk, b64decode(sigB64), new TextEncoder().encode(msg)
    );
  }

  window.SMPCCore = {
    SCALE, toFixed, canonicalMessage, maskSign, fmt2, escapeHtml,
    b64encode, b64decode,
    generateECDHKeypair, exportEcdhPubB64, importEcdhPub, derivePairwiseMask,
    generateSigningKeypair, exportVkB64, signMessage, importVk, verifyMessage,
  };
})();
