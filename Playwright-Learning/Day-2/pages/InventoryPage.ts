// InventoryPage.ts for SauceDemo application
import { Page, Locator } from '@playwright/test';

export class InventoryPage {
    private readonly page: Page;
    readonly inventoryItems: Locator;
    readonly cartBadge: Locator;

    constructor(page: Page) {
        this.page = page;
        this.inventoryItems = page.locator('.inventory_item');
        this.cartBadge = page.locator('.shopping_cart_badge');
    }

    async addItemToCart(itemName: string): Promise<void> {
        const itemLocator = this.page.locator('.inventory_item').filter({ hasText: itemName }).getByRole('button', { name: 'Add to cart' });
        await itemLocator.click();
    }
    async isInventoryDisplayed(): Promise<boolean> {
        return await this.inventoryItems.isVisible();
    }
}