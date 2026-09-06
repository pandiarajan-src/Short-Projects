// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pom/LoginPage';
import { InventoryPage } from '../../pom/InventoryPage';
import { CartPage } from '../../pom/CartPage';
import { CheckoutStepOnePage } from '../../pom/CheckoutStepOnePage';
import { CheckoutStepTwoPage } from '../../pom/CheckoutStepTwoPage';

test.describe('Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('standard_user', 'secret_sauce');
  });

  test('Checkout overview totals are correct for multiple items', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);
    const checkoutStepOne = new CheckoutStepOnePage(page);
    const checkoutStepTwo = new CheckoutStepTwoPage(page);

    // 1. Add 'Sauce Labs Backpack' ($29.99), 'Sauce Labs Bike Light' ($9.99), and
    // 'Sauce Labs Fleece Jacket' ($49.99) to the cart, then proceed through checkout-step-one.html
    // with valid info to reach the Overview page.
    await inventoryPage.addProductToCart('sauce-labs-backpack');
    await inventoryPage.addProductToCart('sauce-labs-bike-light');
    await inventoryPage.addProductToCart('sauce-labs-fleece-jacket');
    await inventoryPage.goToCart();
    await cartPage.checkout();
    await checkoutStepOne.fillInfo('Pandi', 'Rajan', '560001');
    await checkoutStepOne.continue();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-step-two.html');
    await expect(checkoutStepTwo.itemRows).toHaveCount(3);
    await expect(checkoutStepTwo.priceByName('Sauce Labs Backpack')).toHaveText('$29.99');
    await expect(checkoutStepTwo.priceByName('Sauce Labs Bike Light')).toHaveText('$9.99');
    await expect(checkoutStepTwo.priceByName('Sauce Labs Fleece Jacket')).toHaveText('$49.99');

    // 2. Read the 'Item total' line.
    const itemTotal = await checkoutStepTwo.getItemTotal();
    expect(itemTotal).toBeCloseTo(89.97, 2);

    // 3. Read the 'Tax' and 'Total' lines.
    const tax = await checkoutStepTwo.getTax();
    const total = await checkoutStepTwo.getTotal();
    expect(total).toBeCloseTo(itemTotal + tax, 2);
  });
});
