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

  test('Validation error when Postal Code is missing', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);
    const checkoutStepOne = new CheckoutStepOnePage(page);

    // 1. Reach checkout-step-one.html with an item in the cart. Fill firstName with 'Pandi' and
    // lastName with 'Rajan', leaving Postal Code empty.
    await inventoryPage.addProductToCart('sauce-labs-backpack');
    await inventoryPage.goToCart();
    await cartPage.checkout();
    await checkoutStepOne.firstNameInput.fill('Pandi');
    await checkoutStepOne.lastNameInput.fill('Rajan');
    await expect(checkoutStepOne.firstNameInput).toHaveValue('Pandi');
    await expect(checkoutStepOne.lastNameInput).toHaveValue('Rajan');

    // 2. Click [data-test="continue"].
    await checkoutStepOne.continue();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-step-one.html');
    await expect(checkoutStepOne.errorBanner).toHaveText('Error: Postal Code is required');

    // 3. Now fill [data-test="postalCode"] with '560001' and click Continue again.
    await checkoutStepOne.postalCodeInput.fill('560001');
    await checkoutStepOne.continue();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-step-two.html');
    await expect(checkoutStepOne.errorBanner).toHaveCount(0);
  });
});
