// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pom/LoginPage';
import { InventoryPage } from '../../pom/InventoryPage';
import { CartPage } from '../../pom/CartPage';
import { CheckoutStepOnePage } from '../../pom/CheckoutStepOnePage';
import { CheckoutStepTwoPage } from '../../pom/CheckoutStepTwoPage';
import { CheckoutCompletePage } from '../../pom/CheckoutCompletePage';

test.describe('Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('standard_user', 'secret_sauce');
  });

  test("Checkout complete page 'Generate PDF order' control is present", async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);
    const checkoutStepOne = new CheckoutStepOnePage(page);
    const checkoutStepTwo = new CheckoutStepTwoPage(page);
    const checkoutComplete = new CheckoutCompletePage(page);

    // 1. Complete a full valid checkout (add item, fill info, continue, finish) to reach
    // checkout-complete.html.
    await inventoryPage.addProductToCart('sauce-labs-backpack');
    await inventoryPage.goToCart();
    await cartPage.checkout();
    await checkoutStepOne.fillInfo('Pandi', 'Rajan', '560001');
    await checkoutStepOne.continue();
    await checkoutStepTwo.finish();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-complete.html');

    await expect(checkoutComplete.completeHeader).toHaveText('Thank you for your order!');
    await expect(checkoutComplete.completeHeader).toBeVisible();
    await expect(checkoutComplete.backToProductsButton).toBeVisible();
    await expect(checkoutComplete.backToProductsButton).toBeEnabled();
    await expect(checkoutComplete.generatePdfOrderButton).toBeVisible();
    await expect(checkoutComplete.generatePdfOrderButton).toBeEnabled();
  });
});
