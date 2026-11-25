import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { test } from "node:test";
import ts from "typescript";

const module = { exports: {} };
const { outputText } = ts.transpileModule(readFileSync(new URL("../lib/utils.ts", import.meta.url), "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS },
});
new Function("require", "module", "exports", outputText)(createRequire(import.meta.url), module, module.exports);

test("INR prices preserve paise without adding decimals to whole amounts", () => {
  assert.equal(module.exports.formatCurrency(123.45), "₹123.45");
  assert.equal(module.exports.formatCurrency(25000), "₹25,000");
  assert.equal(module.exports.formatCurrency(0), "₹0");
});
