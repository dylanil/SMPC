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

console.log(`\nALL ${passed} NUMERIC CHECKS PASSED`);
