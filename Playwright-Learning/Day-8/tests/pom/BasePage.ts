import { Page, Locator } from '@playwright/test';

/**
 * Shared header behavior available on every authenticated SauceDemo page
 * (inventory, cart, checkout step one/two, checkout complete): the
 * shopping cart link and its item-count badge.
 */
export class BasePage {
  readonly page: Page;
  readonly shoppingCartLink: Locator;
  readonly shoppingCartBadge: Locator;

  constructor(page: Page) {
    this.page = page;
    this.shoppingCartLink = page.locator('[data-test="shopping-cart-link"]');
    this.shoppingCartBadge = page.locator('[data-test="shopping-cart-badge"]');
  }

  async goToCart(): Promise<void> {
    await this.shoppingCartLink.click();
  }
}
