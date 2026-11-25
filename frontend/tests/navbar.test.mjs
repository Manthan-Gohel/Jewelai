import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { test } from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const source = readFileSync(new URL("../components/Navbar.tsx", import.meta.url), "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS, esModuleInterop: true },
});
const component = { exports: {} };
new Function("require", "module", "exports", outputText)(createRequire(import.meta.url), component, component.exports);
const Navbar = component.exports.default;
const props = { activeTab: "overview", setActiveTab() {}, onToggleAutoReply() {} };

test("disconnected header shows no invented business, handle, price, or active controls", () => {
  const html = renderToStaticMarkup(React.createElement(Navbar, { ...props, settings: null, isConnected: false }));
  assert.doesNotMatch(html, /Luxe Aura|luxeaurajewels|72,000|META V21/);
  assert.match(html, /Your workspace/);
  assert.match(html, /Not connected/);
  assert.match(html, /<button[^>]*disabled=""[^>]*>.*?AI Paused/s);
});

test("connected header distinguishes an unconfigured zero rate", () => {
  const html = renderToStaticMarkup(React.createElement(Navbar, {
    ...props, isConnected: true,
    settings: { business_name: "Example Jewels", gold_rate_22k_per_10g: 0, auto_reply_enabled: true },
  }));
  assert.match(html, /Example Jewels/);
  assert.match(html, /Not set/);
  assert.doesNotMatch(html, /₹0/);
  assert.match(html, /Instagram connected/);
  assert.match(html, /AI Auto-Reply Active/);
});

test("connected header shows the saved positive rate as manual", () => {
  const html = renderToStaticMarkup(React.createElement(Navbar, {
    ...props, isConnected: true,
    settings: { business_name: "Client Jeweller", gold_rate_22k_per_10g: 81234, auto_reply_enabled: false },
  }));
  assert.match(html, /₹81,234 \/ 10g/);
  assert.match(html, /Saved 22K/);
});
