import { test, expect } from "@playwright/test";

test.describe("Font Loading", () => {
  test("should load all fonts without errors", async ({ page }) => {
    const fontErrors: Array<{ url: string; error?: string; status?: number }> =
      [];
    const fontRequests: string[] = [];

    // Listen for failed requests
    page.on("requestfailed", (request) => {
      const url = request.url();
      if (url.match(/\.(woff|woff2|ttf|otf)$/i) || url.includes("font")) {
        const error = {
          url,
          error: request.failure()?.errorText || "Unknown error",
        };
        fontErrors.push(error);
        console.log("[FONT ERROR]:", JSON.stringify(error));
      }
    });

    // Listen for font requests
    page.on("request", (request) => {
      const url = request.url();
      if (
        url.match(/\.(woff|woff2|ttf|otf)$/i) ||
        url.includes("fonts.googleapis") ||
        url.includes("fonts.gstatic")
      ) {
        fontRequests.push(url);
        console.log("[FONT REQUEST]:", url);
      }
    });

    // Listen for responses
    page.on("response", (response) => {
      const url = response.url();
      if (
        url.match(/\.(woff|woff2|ttf|otf)$/i) ||
        url.includes("fonts.googleapis") ||
        url.includes("fonts.gstatic")
      ) {
        console.log("[FONT RESPONSE]:", response.status(), url);
        if (response.status() >= 400) {
          fontErrors.push({ url, status: response.status() });
        }
      }
    });

    // Navigate to the homepage
    await page.goto("http://localhost:3000", { waitUntil: "networkidle" });

    // Wait a bit for any lazy-loaded fonts
    await page.waitForTimeout(2000);

    // Check computed font family
    const bodyFont = await page.evaluate(() => {
      return window.getComputedStyle(document.body).fontFamily;
    });

    console.log("\n=== Font Loading Summary ===");
    console.log("Total font requests:", fontRequests.length);
    console.log("Font errors:", fontErrors.length);
    console.log("Body font family:", bodyFont);

    if (fontErrors.length > 0) {
      console.log("\n=== Font Errors ===");
      fontErrors.forEach((error, i) => {
        console.log(`${i + 1}.`, JSON.stringify(error, null, 2));
      });
    }

    // Assert no font errors
    expect(fontErrors).toHaveLength(0);
  });
});
