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

  test('Validation error when First Name is missing', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);
    const checkoutStepOne = new CheckoutStepOnePage(page);

    // 1. Add an item to the cart, navigate to cart page, click Checkout to reach checkout-step-one.html.
    await inventoryPage.addProductToCart('sauce-labs-backpack');
    await inventoryPage.goToCart();
    await cartPage.checkout();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-step-one.html');
    await expect(checkoutStepOne.firstNameInput).toHaveValue('');
    await expect(checkoutStepOne.lastNameInput).toHaveValue('');
    await expect(checkoutStepOne.postalCodeInput).toHaveValue('');

    // 2. Leave all fields empty and click [data-test="continue"] directly.
    await checkoutStepOne.continue();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-step-one.html');
    await expect(checkoutStepOne.errorBanner).toBeVisible();
    await expect(checkoutStepOne.errorBanner).toHaveText('Error: First Name is required');

    // 3. Click the error dismiss button [data-test="error-button"].
    await checkoutStepOne.dismissError();
    await expect(checkoutStepOne.errorBanner).toHaveCount(0);
  });
});
