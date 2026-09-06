import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Shared behavior for pages that render the SauceDemo product list item
 * component (`[data-test="inventory-item"]`). The Inventory page, the
 * Cart page, and the Checkout Overview page all reuse this same markup,
 * so the underlying locators live here once instead of being duplicated
 * across each page object.
 */
export class ItemListPage extends BasePage {
  readonly itemRows: Locator;
  readonly itemNames: Locator;
  readonly itemPrices: Locator;

  constructor(page: Page) {
    super(page);
    this.itemRows = page.locator('[data-test="inventory-item"]');
    this.itemNames = page.locator('[data-test="inventory-item-name"]');
    this.itemPrices = page.locator('[data-test="inventory-item-price"]');
  }

  rowByName(name: string): Locator {
    return this.itemRows.filter({
      has: this.page.locator('[data-test="inventory-item-name"]', { hasText: name }),
    });
  }

  priceByName(name: string): Locator {
    return this.rowByName(name).locator('[data-test="inventory-item-price"]');
  }

  async getItemCount(): Promise<number> {
    return this.itemRows.count();
  }

  async getProductNames(): Promise<string[]> {
    return this.itemNames.allTextContents();
  }

  async getProductPrices(): Promise<number[]> {
    const texts = await this.itemPrices.allTextContents();
    return texts.map((text) => parseFloat(text.replace('$', '')));
  }
}
