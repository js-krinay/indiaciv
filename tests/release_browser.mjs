import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { join } from "node:path";

const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = require(process.env.INDIACIV_PLAYWRIGHT || "playwright"));
} catch (error) {
  if (error.code !== "MODULE_NOT_FOUND") throw error;
  console.log("Playwright is unavailable");
  process.exit(77);
}

let browser;
try {
  browser = await chromium.launch({ channel: "chrome" });
} catch (error) {
  if (!/distribution .* is not found|executable doesn't exist/i.test(error.message)) throw error;
  console.log("Chrome is unavailable");
  process.exit(77);
}

try {
  for (const width of [1440, 390]) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    const errors = [];
    page.on("console", message => {
      if (message.type() === "error") errors.push(message.text());
    });
    page.on("pageerror", error => errors.push(error.message));
    page.on("requestfailed", request => errors.push(request.url() + " " + request.failure().errorText));
    page.on("response", response => {
      if (response.status() >= 400) errors.push(response.status() + " " + response.url());
    });
    let failure;
    try {
      await page.goto(process.argv[2]);
      await page.locator("#loading").waitFor({ state: "hidden" });
      await page.waitForFunction(() => window.__app?.extensions?.length === 3);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await page.locator("#btn-pedia").click();
      await page.locator("#pedia").waitFor({ state: "visible" });
      await page.waitForFunction(() => window.__app?.data.sources?.length > 0);
      await page.locator("#pedia [data-close]").click();
      if (process.env.INDIACIV_RELEASE_SCREENSHOTS) {
        await page.screenshot({ path: join(process.env.INDIACIV_RELEASE_SCREENSHOTS, "release-" + width + ".png") });
      }
    } catch (error) {
      failure = error;
    } finally {
      await page.close();
    }
    assert.deepEqual(errors, [], "Browser errors at " + width + " px");
    if (failure) throw failure;
    console.log(width + " px: loading hidden, extensions installed, no request or console errors");
  }
} finally {
  await browser.close();
}
