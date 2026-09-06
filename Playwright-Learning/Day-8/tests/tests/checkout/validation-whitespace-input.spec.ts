// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts
//
// Verified live application behavior: a single-space First Name is treated as a
// non-empty value by the app's client-side validation, so submitting it along
// with valid Last Name and Postal Code values successfully proceeds to the
// Overview page rather than showing the "First Name is required" error.

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pom/LoginPage';
import { CheckoutStepOnePage } from '../../pom/CheckoutStepOnePage';

test.describe('Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('standard_user', 'secret_sauce');
    await page.goto('https://www.saucedemo.com/checkout-step-one.html');
  });

  test('Whitespace-only input is treated as missing for required fields', async ({ page }) => {
    const checkoutStepOne = new CheckoutStepOnePage(page);

    // 1. On checkout-step-one.html, fill First Name with a single space ' ', fill Last Name and
    // Postal Code with valid values, and click Continue.
    await checkoutStepOne.fillInfo(' ', 'Rajan', '560001');
    await checkoutStepOne.continue();

    // The live application accepts the whitespace-only value and proceeds to the Overview page.
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-step-two.html');
    await expect(checkoutStepOne.errorBanner).toHaveCount(0);
  });
});
