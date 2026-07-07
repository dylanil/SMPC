#!/usr/bin/env node
// Dependency-free contract tests for the browser numeric helpers in
// public/static/smpc-core.js. Run with Node:
//   node tests_numeric.js

global.window = global;
global.atob = global.atob || (s => Buffer.from(s, "base64").toString("binary"));
global.btoa = global.btoa || (s => Buffer.from(s, "binary").toString("base64"));

require("./public/static/smpc-core.js");

const {
  parseDecimalToFixed,
  formatFixed,
  formatAverageFixed,
  canonicalMessage,
  maskSign,
  escapeHtml,
} = global.SMPCCore;

let passed = 0;

function check(name, actual, expected) {
  if (actual !== expected) {
    throw new Error(`${name}: got ${actual}, expected ${expected}`);
  }
  passed++;
  console.log("PASS:", name);
}

function rejects(name, input) {
  try {
    parseDecimalToFixed(input);
  } catch (_) {
    passed++;
    console.log("PASS:", name);
    return;
  }
  throw new Error(`${name}: ${input} was accepted`);
}

check(
  "large integer above Number.MAX_SAFE_INTEGER stays exact",
  parseDecimalToFixed("9007199254740993").toString(),
  "9007199254740993000000",
);
check("negative decimal parses exactly", parseDecimalToFixed("-12.345678").toString(), "-12345678");
check("more than 6dp rounds to nearest micro-unit", parseDecimalToFixed("1.2345678").toString(), "1234568");
check("positive half micro-unit rounds away from zero", parseDecimalToFixed("0.0000005").toString(), "1");
check("negative half micro-unit rounds away from zero", parseDecimalToFixed("-0.0000005").toString(), "-1");

rejects("reject exponent notation", "1e6");
rejects("reject trailing junk", "12abc");
rejects("reject commas", "1,000");
rejects("reject Infinity", "Infinity");
rejects("reject blank input", "   ");
rejects("reject non-ASCII digits", "١٠");

check(
  "formatFixed avoids Number precision loss",
  formatFixed(9007199254740993000000n),
  "9007199254740993",
);
check("formatFixed strips trailing zeros", formatFixed(12345000n), "12.35");
check("formatFixed never renders -0", formatFixed(-1n), "0");
check(
  "formatAverageFixed avoids Number precision loss",
  formatAverageFixed(27021597764222979000000n, 3),
  "9007199254740993",
);
check("formatAverageFixed rounds display exactly", formatAverageFixed(1000000n, 3), "0.33");

// GAP-T3: the JS half of the cross-language contract, previously only
// exercised implicitly. The canonical string must byte-match the Python pin
// in tests.py's test_contract_vector; the sign convention is load-bearing for
// mask cancellation; escapeHtml is the RB-47 sink guard.
check(
  "canonicalMessage pins the cross-language format",
  canonicalMessage("share", "ABCDEF", "A", "123"),
  "share|ABCDEF|A|123",
);
check("maskSign: lower letter adds", maskSign("A", "B"), 1n);
check("maskSign: higher letter subtracts", maskSign("B", "A"), -1n);
check(
  "escapeHtml neutralises the five sensitive characters",
  escapeHtml("<a href=\"x\" onclick='y'>&"),
  "&lt;a href=&quot;x&quot; onclick=&#39;y&#39;&gt;&amp;",
);
check("escapeHtml passes plain text through", escapeHtml("Average claim severity"), "Average claim severity");

console.log(`\nALL ${passed} NUMERIC CHECKS PASSED`);
