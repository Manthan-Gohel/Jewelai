import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import ts from "typescript";

const source = readFileSync(new URL("../lib/api.ts", import.meta.url), "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 },
});
const { api, ApiError } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`);

test("JSON requests use same-origin sessions without browser token storage", async (t) => {
  t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(url, "/api/v1/auth/login");
    assert.equal(options.credentials, "same-origin");
    assert.equal(options.headers["X-JewelAI-Request"], "1");
    assert.equal(options.headers["Content-Type"], "application/json");
    assert.equal(options.headers.Authorization, undefined);
    assert.deepEqual(JSON.parse(options.body), { email: "owner@example.com", password: "example-pass" });
    return Response.json({ user: { id: "owner" } });
  });
  assert.deepEqual(await api.login("owner@example.com", "example-pass"), { user: { id: "owner" } });
});

test("CSV uploads preserve multipart headers and shared session-expiration handling", async (t) => {
  const browser = new EventTarget();
  globalThis.window = browser;
  t.after(() => { delete globalThis.window; });
  let expired = false;
  browser.addEventListener("jewelai:session-expired", () => { expired = true; });
  t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(options.headers["Content-Type"], undefined);
    assert.ok(options.body instanceof FormData);
    assert.equal(options.headers["X-JewelAI-Request"], "1");
    return Response.json({ detail: "Please sign in again." }, { status: 401 });
  });
  await assert.rejects(api.previewCsv(new File(["sku,name"], "products.csv")), (error) => {
    assert.ok(error instanceof ApiError);
    assert.equal(error.message, "Please sign in again.");
    return true;
  });
  assert.equal(expired, true);
});

test("network failures become actionable errors", async (t) => {
  t.mock.method(globalThis, "fetch", async () => { throw new TypeError("fetch failed"); });
  await assert.rejects(api.getMe(), (error) => error instanceof ApiError && error.status === 0 && /connection/i.test(error.message));
});

test("validation errors are readable and no-content responses are supported", async (t) => {
  t.mock.method(globalThis, "fetch", async () => Response.json({ detail: [{ msg: "Enter a valid email." }] }, { status: 422 }));
  await assert.rejects(api.login("bad", "password"), /Enter a valid email/);
  globalThis.fetch = async () => new Response(null, { status: 204 });
  assert.equal(await api.deleteProduct("product-id"), undefined);
});
