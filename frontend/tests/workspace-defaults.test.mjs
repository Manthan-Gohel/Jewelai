import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { test } from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const require = createRequire(import.meta.url);
function renderComponent(name, settings) {
  const source = readFileSync(new URL(`../components/${name}.tsx`, import.meta.url), "utf8");
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS, esModuleInterop: true },
  });
  const component = { exports: {} };
  new Function("require", "module", "exports", outputText)((id) => {
    if (id === "@/lib/api") return { api: {} };
    if (id === "@/lib/utils") return { formatDate: String };
    return require(id);
  }, component, component.exports);
  return renderToStaticMarkup(React.createElement(component.exports.default, { settings, onUpdateSettings() {} }));
}

test("settings and knowledge forms never prefill demo business facts", () => {
  for (const name of ["SettingsView", "KnowledgeView"]) {
    const html = renderComponent(name, null);
    assert.doesNotMatch(html, /Luxe Aura|Timeless Elegance|98765 43210|Diamond Heritage|78500|72000|58900|10:30 AM/);
  }
});

test("saved business details remain visible", () => {
  assert.match(renderComponent("SettingsView", { business_name: "Client Jeweller", contact_phone: "+4412345" }), /Client Jeweller/);
  assert.match(renderComponent("KnowledgeView", { gold_rate_22k_per_10g: 81234, store_address: "Client address" }), /81234/);
  assert.match(renderComponent("KnowledgeView", { gold_rate_22k_per_10g: 0 }), /value=""/);
});
