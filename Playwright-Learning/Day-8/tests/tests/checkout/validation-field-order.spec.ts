// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pom/LoginPage';
import { InventoryPage } from '../../pom/InventoryPage';
import { CartPage } from '../../pom/CartPage';
import { CheckoutStepOnePage } from '../../pom/CheckoutStepOnePage';

test.describe('Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('standard_user', 'secret_sauce');
  });

  test("Checkout step one validates fields in order (only first missing field's error shown)", async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);
    const checkoutStepOne = new CheckoutStepOnePage(page);

    await inventoryPage.addProductToCart('sauce-labs-backpack');
    await inventoryPage.goToCart();
    await cartPage.checkout();

    // 1. With an item in the cart on checkout-step-one.html, leave all three fields empty and click Continue.
    await checkoutStepOne.continue();
    await expect(checkoutStepOne.errorBanner).toHaveText('Error: First Name is required');

    // 2. Fill First Name only and click Continue again.
    await checkoutStepOne.firstNameInput.fill('Pandi');
    await checkoutStepOne.continue();
    await expect(checkoutStepOne.errorBanner).toHaveText('Error: Last Name is required');

    // 3. Fill Last Name as well (First Name still filled) and click Continue again.
    await checkoutStepOne.lastNameInput.fill('Rajan');
    await checkoutStepOne.continue();
    await expect(checkoutStepOne.errorBanner).toHaveText('Error: Postal Code is required');
  });
});
