import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  const response = await page.goto("/");

  expect(response?.ok()).toBe(true);
  await expect(
    page.getByRole("heading", {
      level: 1,
      name: "React performance review runtime",
    }),
  ).toBeVisible();
});

test("keeps the newest search result when an older request resolves later", async ({ page }) => {
  const query = page.getByRole("textbox", { name: "Search query" });
  const result = page.getByRole("status", { name: "Search result" });

  await query.fill("old");
  await page.getByRole("button", { name: "Start search" }).click();
  await query.fill("new");
  await page.getByRole("button", { name: "Start search" }).click();

  await page.getByRole("button", { name: "Resolve new" }).click();
  await expect(result).toHaveText("Result for new");
  await page.getByRole("button", { name: "Resolve old" }).click();
  await expect(result).toHaveText("Result for new");
});

test("transfers DOM focus when keyboard navigation crosses the virtual window", async ({ page }) => {
  const listbox = page.getByRole("listbox", { name: "Virtual results" });
  const fifthItem = page.getByRole("option", { name: "Item 5" });

  await expect(listbox).toBeVisible();
  await fifthItem.focus();
  await fifthItem.press("ArrowDown");

  const sixthItem = page.getByRole("option", { name: "Item 6" });
  await expect(sixthItem).toBeFocused();
  await expect(sixthItem).toHaveAttribute("aria-posinset", "6");
  await expect(sixthItem).toHaveAttribute("aria-setsize", "100");
  await expect(page.getByRole("option", { name: "Item 1" })).toHaveCount(0);
});

test("records a Profiler commit while preserving filtering and analytics sync", async ({ page }) => {
  const profilerEvidence = page.getByRole("status", { name: "Profiler evidence" });
  const analyticsEvidence = page.getByRole("status", { name: "Analytics evidence" });

  await expect(profilerEvidence).toHaveAttribute("data-commit-count", "1");
  await expect(analyticsEvidence).toHaveAttribute("data-sync-count", "1");
  await page.getByRole("textbox", { name: "Filter measured results" }).fill("alp");

  await expect(page.getByRole("list", { name: "Filtered results" })).toHaveText("AlphaAlpine");
  await expect(page.getByText("Beta", { exact: true })).toHaveCount(0);
  await expect(profilerEvidence).toHaveAttribute("data-commit-count", "2");
  await expect(profilerEvidence).toContainText("actualDuration=");
  await expect(analyticsEvidence).toHaveAttribute("data-sync-count", "2");
});
