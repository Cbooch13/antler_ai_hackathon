import { test, expect } from '@playwright/test';

test('six-step walk', async ({ page }) => {
  // Landing page
  await page.goto('/');
  await expect(page.locator('h1').first()).toBeVisible();

  // Navigate to intake
  await page.click('text=Start a feasibility run');
  await expect(page).toHaveURL(/\/workspace\/intake/);

  // Step 1: Intake — validate spec, then find lots
  await expect(page.locator('h1').filter({ hasText: 'Project intake' })).toBeVisible();
  await page.click('button:has-text("Validate spec")');
  // Wait for validated badge to appear (status changes from Pending → Validated)
  await expect(page.locator('.badge:has-text("Validated"), span:has-text("Validated")')).toBeVisible({ timeout: 5000 });
  // Find prototype lots advances to step 2 and navigates to /workspace/lots
  await page.click('button:has-text("Find prototype lots")');
  await expect(page).toHaveURL(/\/workspace\/lots/, { timeout: 5000 });

  // Step 2: Lots — select a lot
  await expect(page.locator('[data-lot]').first()).toBeVisible();
  await page.locator('[data-lot]').first().locator('button:has-text("View context")').click();
  await expect(page).toHaveURL(/\/workspace\/lot-context/);

  // Step 3: Lot context — run feasibility
  await expect(page.locator('button:has-text("Run feasibility check")')).toBeVisible();
  await page.click('button:has-text("Run feasibility check")');
  await expect(page).toHaveURL(/\/workspace\/compliance/, { timeout: 5000 });

  // Step 4: Compliance — generate schematic plan
  await expect(page.locator('text=Compliance metrics')).toBeVisible();
  await page.click('button:has-text("Generate schematic plan")');
  await expect(page).toHaveURL(/\/workspace\/schematic/, { timeout: 5000 });

  // Step 5: Schematic — advance to packet
  await expect(page.locator('button:has-text("Assemble review packet")')).toBeVisible();
  await page.click('button:has-text("Assemble review packet")');
  await expect(page).toHaveURL(/\/workspace\/packet/);

  // Step 6: Review packet
  await expect(page.locator('button:has-text("Share with reviewer")')).toBeVisible();
});

test('mobile toggle shows ios frame', async ({ page }) => {
  await page.goto('/workspace/intake');
  await page.click('button[role="tab"]:has-text("Mobile")');
  await expect(page.locator('.mobile-overlay')).toBeVisible({ timeout: 3000 });
  await expect(page.locator('.mobile-shell')).toBeVisible({ timeout: 3000 });
});

test('locked step shows locked state', async ({ page }) => {
  // Navigate directly to compliance without completing prior steps
  await page.goto('/workspace/compliance');
  // App shows LockedState with title "Compliance is locked"
  await expect(page.locator('text=is locked')).toBeVisible({ timeout: 3000 });
});
