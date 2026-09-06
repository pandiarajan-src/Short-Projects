// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pom/LoginPage';
import { InventoryPage } from '../../pom/InventoryPage';
import { CartPage } from '../../pom/CartPage';

test.describe('Shopping Cart Management', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('standard_user', 'secret_sauce');
  });

  test('Add multiple items to the cart from the inventory page and verify badge count', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);

    // 1. Click 'Add to cart' for 'Sauce Labs Backpack'.
    await inventoryPage.addProductToCart('sauce-labs-backpack');
    await expect(inventoryPage.shoppingCartBadge).toHaveText('1');

    // 2. Click 'Add to cart' for 'Sauce Labs Bike Light'.
    await inventoryPage.addProductToCart('sauce-labs-bike-light');
    await expect(inventoryPage.shoppingCartBadge).toHaveText('2');

    // 3. Click 'Add to cart' for 'Sauce Labs Onesie'.
    await inventoryPage.addProductToCart('sauce-labs-onesie');
    await expect(inventoryPage.shoppingCartBadge).toHaveText('3');

    // 4. Verify that the buttons for all three added products now read 'Remove', while the remaining
    // three products (Bolt T-Shirt, Fleece Jacket, Test.allTheThings() T-Shirt) still read 'Add to cart'.
    await expect(inventoryPage.removeButton('sauce-labs-backpack')).toHaveText('Remove');
    await expect(inventoryPage.removeButton('sauce-labs-bike-light')).toHaveText('Remove');
    await expect(inventoryPage.removeButton('sauce-labs-onesie')).toHaveText('Remove');
    await expect(inventoryPage.addToCartButton('sauce-labs-bolt-t-shirt')).toHaveText('Add to cart');
    await expect(inventoryPage.addToCartButton('sauce-labs-fleece-jacket')).toHaveText('Add to cart');
    await expect(inventoryPage.addToCartButton('test.allthethings()-t-shirt-(red)')).toHaveText('Add to cart');

    // 5. Click [data-test="shopping-cart-link"] to navigate to the cart page.
    await inventoryPage.goToCart();
    await expect(cartPage.itemRows).toHaveCount(3);
    await expect(cartPage.rowByName('Sauce Labs Backpack')).toBeVisible();
    await expect(cartPage.rowByName('Sauce Labs Bike Light')).toBeVisible();
    await expect(cartPage.rowByName('Sauce Labs Onesie')).toBeVisible();
    await expect(cartPage.quantityByName('Sauce Labs Backpack')).toHaveText('1');
    await expect(cartPage.quantityByName('Sauce Labs Bike Light')).toHaveText('1');
    await expect(cartPage.quantityByName('Sauce Labs Onesie')).toHaveText('1');
    await expect(cartPage.priceByName('Sauce Labs Backpack')).toHaveText('$29.99');
    await expect(cartPage.priceByName('Sauce Labs Bike Light')).toHaveText('$9.99');
    await expect(cartPage.priceByName('Sauce Labs Onesie')).toHaveText('$7.99');
  });
});
