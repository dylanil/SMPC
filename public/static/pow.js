// Pure-JS SHA-256 + Hashcash-style PoW miner.
// Used by aggregator.html (before /api/session/new) and party.html (before
// /api/join) to make memory-DoS and invite-brute-force expensive per-request.
// See server.py mint_pow_challenge / verify_pow for the matching server side.
//
// We use a hand-rolled SHA-256 instead of crypto.subtle.digest because the
// per-call promise overhead in WebCrypto kills throughput when you're hashing
// millions of tiny inputs in a tight loop.

(function () {
  const K = new Uint32Array([
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
  ]);

  function rotr(x, n) { return ((x >>> n) | (x << (32 - n))) >>> 0; }

  // SHA-256 of an ASCII string. Returns lowercase hex (64 chars).
  // Inputs in this app are short (challenge + ":" + nonce ~ 200 chars max),
  // so we don't bother with multi-block streaming.
  function sha256Hex(msg) {
    const bytes = new TextEncoder().encode(msg);
    const len = bytes.length;
    const padLen = Math.ceil((len + 9) / 64) * 64;
    const padded = new Uint8Array(padLen);
    padded.set(bytes);
    padded[len] = 0x80;
    const view = new DataView(padded.buffer);
    view.setBigUint64(padLen - 8, BigInt(len) * 8n);

    const h = new Uint32Array([
      0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
      0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
    ]);
    const w = new Uint32Array(64);

    for (let i = 0; i < padLen; i += 64) {
      for (let t = 0; t < 16; t++) w[t] = view.getUint32(i + t * 4);
      for (let t = 16; t < 64; t++) {
        const s0 = rotr(w[t - 15], 7) ^ rotr(w[t - 15], 18) ^ (w[t - 15] >>> 3);
        const s1 = rotr(w[t - 2], 17) ^ rotr(w[t - 2], 19) ^ (w[t - 2] >>> 10);
        w[t] = (w[t - 16] + s0 + w[t - 7] + s1) >>> 0;
      }
      let a = h[0], b = h[1], c = h[2], d = h[3];
      let e = h[4], f = h[5], g = h[6], hh = h[7];
      for (let t = 0; t < 64; t++) {
        const S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        const ch = (e & f) ^ (~e & g);
        const t1 = (hh + S1 + ch + K[t] + w[t]) >>> 0;
        const S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        const mj = (a & b) ^ (a & c) ^ (b & c);
        const t2 = (S0 + mj) >>> 0;
        hh = g; g = f; f = e;
        e = (d + t1) >>> 0;
        d = c; c = b; b = a;
        a = (t1 + t2) >>> 0;
      }
      h[0] = (h[0] + a) >>> 0; h[1] = (h[1] + b) >>> 0;
      h[2] = (h[2] + c) >>> 0; h[3] = (h[3] + d) >>> 0;
      h[4] = (h[4] + e) >>> 0; h[5] = (h[5] + f) >>> 0;
      h[6] = (h[6] + g) >>> 0; h[7] = (h[7] + hh) >>> 0;
    }
    let out = "";
    for (let i = 0; i < 8; i++) out += h[i].toString(16).padStart(8, "0");
    return out;
  }

  function leadingZeroBitsHex(hex) {
    let bits = 0;
    for (let i = 0; i < hex.length; i++) {
      const v = parseInt(hex[i], 16);
      if (v === 0) { bits += 4; continue; }
      // Math.clz32 counts leading zeros in 32 bits; for a single hex digit
      // (4 bits) we subtract 28 to get the leading zeros in those 4 bits.
      bits += Math.clz32(v) - 28;
      return bits;
    }
    return bits;
  }

  // Mine until SHA-256(challenge + ":" + nonce) clears `difficulty` leading
  // zero bits. Yields to the event loop every few thousand iterations so the
  // page stays responsive and `onProgress` can update a "verifying…" label.
  async function minePoW(challenge, difficulty, onProgress) {
    const yieldEvery = 5000;
    for (let n = 0; ; n++) {
      if (n > 0 && n % yieldEvery === 0) {
        if (onProgress) onProgress(n);
        await new Promise((r) => setTimeout(r, 0));
      }
      if (leadingZeroBitsHex(sha256Hex(challenge + ":" + n)) >= difficulty) return n;
    }
  }

  // Convenience: GET a fresh challenge from the server, mine it, return the
  // pair the caller should attach to their gated POST.
  async function getPoWAndMine(onProgress) {
    const r = await fetch("/api/pow-challenge");
    if (!r.ok) throw new Error("failed to fetch PoW challenge");
    const { challenge, difficulty } = await r.json();
    const pow_nonce = await minePoW(challenge, difficulty, onProgress);
    return { challenge, pow_nonce, difficulty };
  }

  window.SMPCPoW = { sha256Hex, leadingZeroBitsHex, minePoW, getPoWAndMine };
})();
