// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pom/LoginPage';
import { InventoryPage } from '../../pom/InventoryPage';
import { CartPage } from '../../pom/CartPage';

const CART_SLUGS = ['sauce-labs-backpack', 'sauce-labs-bike-light', 'sauce-labs-onesie'];
const ALL_SLUGS = [
  'sauce-labs-backpack',
  'sauce-labs-bike-light',
  'sauce-labs-bolt-t-shirt',
  'sauce-labs-fleece-jacket',
  'sauce-labs-onesie',
  'test.allthethings()-t-shirt-(red)',
];

test.describe('Shopping Cart Management', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('standard_user', 'secret_sauce');
  });

  test('Remove all items from the cart results in empty cart and no badge', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);

    // 1. Add 3 items to the cart, then navigate to the cart page and click 'Remove' on all 3
    // line items one by one.
    for (const slug of CART_SLUGS) {
      await inventoryPage.addProductToCart(slug);
    }
    await inventoryPage.goToCart();
    await expect(cartPage.shoppingCartBadge).toHaveText('3');

    await cartPage.removeItem(CART_SLUGS[0]);
    await expect(cartPage.shoppingCartBadge).toHaveText('2');

    await cartPage.removeItem(CART_SLUGS[1]);
    await expect(cartPage.shoppingCartBadge).toHaveText('1');

    await cartPage.removeItem(CART_SLUGS[2]);
    await expect(cartPage.shoppingCartBadge).toHaveCount(0);
    await expect(cartPage.itemRows).toHaveCount(0);

    // 2. Click [data-test="continue-shopping"] to return to the inventory page.
    await cartPage.continueShopping();
    await expect(page).toHaveURL('https://www.saucedemo.com/inventory.html');
    for (const slug of ALL_SLUGS) {
      await expect(inventoryPage.addToCartButton(slug)).toHaveText('Add to cart');
    }
  });
});
