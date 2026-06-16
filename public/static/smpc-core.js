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
  const SCALE_DP = 6;

  function pow10(n) {
    return 10n ** BigInt(n);
  }

  // Parse a user-entered ASCII decimal string into the 1e6 fixed-point integer
  // used on the wire. This deliberately has no magnitude cap,
  // but it rejects JS numeric shortcuts like 1e6/Infinity and non-ASCII digits
  // so the browser path is as exact as the BigInt wire story claims.
  function parseDecimalToFixed(raw) {
    const s = String(raw).trim();
    if (!/^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)$/.test(s)) {
      throw new Error("Enter a plain decimal number using ASCII digits, with no commas or exponent notation.");
    }
    let body = s;
    let sign = 1n;
    if (body[0] === "-" || body[0] === "+") {
      sign = body[0] === "-" ? -1n : 1n;
      body = body.slice(1);
    }
    let [whole, frac = ""] = body.split(".");
    if (whole === "") whole = "0";
    const micros = frac.slice(0, SCALE_DP).padEnd(SCALE_DP, "0");
    let fixed = BigInt(whole) * SCALE + BigInt(micros);
    const rest = frac.slice(SCALE_DP);
    if (rest && rest[0] >= "5") fixed += 1n; // nearest micro-unit, half away from zero
    return sign * fixed;
  }

  // Compatibility alias for older call sites. New code should pass the raw
  // user string to parseDecimalToFixed so it never goes through Number.
  const toFixed = parseDecimalToFixed;

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
  function displayUnitsToString(units, maxDp) {
    if (units === 0n) return "0";
    const neg = units < 0n;
    let abs = neg ? -units : units;
    const scale = pow10(maxDp);
    const whole = abs / scale;
    let frac = (abs % scale).toString().padStart(maxDp, "0");
    frac = frac.replace(/0+$/, "");
    return (neg ? "-" : "") + whole.toString() + (frac ? "." + frac : "");
  }

  function roundedDisplayUnits(numerFixed, denom, maxDp) {
    if (!Number.isInteger(maxDp) || maxDp < 0 || maxDp > SCALE_DP) {
      throw new Error("maxDp must be an integer from 0 to 6");
    }
    const d = BigInt(denom);
    if (d <= 0n) throw new Error("denom must be positive");
    const neg = numerFixed < 0n;
    const abs = neg ? -numerFixed : numerFixed;
    const divisor = d * SCALE;
    let q = abs * pow10(maxDp);
    let units = q / divisor;
    const rem = q % divisor;
    if (rem * 2n >= divisor) units += 1n; // display rounding, half away from zero
    return neg ? -units : units;
  }

  // Render a fixed-point integer for display at up to maxDp decimal places,
  // stripping trailing zeros and never rendering "-0".
  function formatFixed(fixed, maxDp = 2) {
    return displayUnitsToString(roundedDisplayUnits(BigInt(fixed), 1, maxDp), maxDp);
  }

  // Render (sumFixed / n) exactly, without first converting either side to
  // Number. This keeps huge demo figures honest while preserving the 2dp UI.
  function formatAverageFixed(sumFixed, n, maxDp = 2) {
    return displayUnitsToString(roundedDisplayUnits(BigInt(sumFixed), n, maxDp), maxDp);
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
    SCALE, toFixed, parseDecimalToFixed, formatFixed, formatAverageFixed,
    canonicalMessage, maskSign, escapeHtml,
    b64encode, b64decode,
    generateECDHKeypair, exportEcdhPubB64, importEcdhPub, derivePairwiseMask,
    generateSigningKeypair, exportVkB64, signMessage, importVk, verifyMessage,
  };
})();
