// Playwright MCP function. Run only with the disposable QA server on 8002/3013.
async (page) => {
  const context = await page.context().browser().newContext();
  const qa = await context.newPage();
  const checks = [], errors = [];
  qa.on("pageerror", err => errors.push(err.message));
  const click = name => qa.getByRole("button", { name, exact: true }).click();
  const check = (ok, label) => { if (!ok) throw new Error(label); checks.push(label); };
  try {
    await qa.goto("http://127.0.0.1:3013");
    await qa.getByLabel("Workspace email").fill("buttons-client@example.com");
    await qa.getByLabel("Password").fill("Buttons-qa-only-2026!");
    await click("Sign in");
    await qa.getByRole("button", { name: "Meta Integration", exact: true }).waitFor();
    for (const width of [375, 768, 1440]) {
      await qa.setViewportSize({ width, height: 1000 });
      for (const name of ["Overview", "Live Inbox", "Catalogue", "Reels & Post Linking", "AI Playground", "Knowledge & FAQs", "Meta Integration", "Settings & Logs"]) {
        await click(name);
        if (name === "Live Inbox") await qa.getByRole("button", { name: "Take Over Thread", exact: true }).waitFor();
        else await qa.locator("main h1, main h2").first().waitFor();
        const size = await qa.evaluate(() => ({ width: innerWidth, scroll: document.documentElement.scrollWidth }));
        check(size.scroll <= size.width, `${name} at ${width}px: no page overflow`);
        await qa.screenshot({ path: `.playwright-mcp/workflow-${name.split(" ")[0].toLowerCase()}-${width}.png`, fullPage: true });
      }
    }
    await click("Catalogue");
    await qa.route("**/api/v1/products?**", route => route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"Synthetic catalogue outage"}' }));
    await click("Go");
    await qa.getByRole("alert").filter({ hasText: "Synthetic catalogue outage" }).waitFor();
    await qa.unroute("**/api/v1/products?**");
    await click("Retry catalogue");
    await qa.getByRole("alert").filter({ hasText: "Synthetic catalogue outage" }).waitFor({ state: "hidden" });
    checks.push("catalogue network failure is visible and Retry recovers");
    await click("AI Playground");
    await qa.route("**/api/v1/ai/test", route => route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"Synthetic AI outage"}' }));
    await click("Simulate AI Execution");
    await qa.getByRole("alert").filter({ hasText: "Synthetic AI outage" }).waitFor();
    await qa.unroute("**/api/v1/ai/test");
    await click("Simulate AI Execution");
    await qa.getByText("Synthesized Instagram DM Response", { exact: true }).waitFor();
    checks.push("AI failure is visible and retry recovers without stale results");
    await qa.route("https://images.unsplash.com/**", route => route.fulfill({ contentType: "image/png", body: Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j9WQAAAAASUVORK5CYII=", "base64") }));
    await click("EN Customer Photo Match");
    await qa.getByText("Synthesized Instagram DM Response", { exact: true }).waitFor();
    await qa.getByRole("button", { name: "Simulate AI Execution", exact: true }).waitFor();
    checks.push("photo scenario renders with synthetic image/provider; not live vision acceptance");
    check(errors.length === 0, "no uncaught browser errors in responsive and recovery checks");
    return { count: checks.length, checks, errors };
  } finally { await context.close(); }
}
