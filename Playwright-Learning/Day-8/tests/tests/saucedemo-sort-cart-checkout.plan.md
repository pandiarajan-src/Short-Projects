# SauceDemo - Sorting, Cart, and Checkout Test Plan

## Application Overview


This test plan covers the SauceDemo (https://www.saucedemo.com/) inventory sorting feature, shopping cart management, and the end-to-end checkout flow. All scenarios assume a fresh browser context and use the seed login flow (username `standard_user`, password `secret_sauce`) defined in `tests/seed.spec.ts` as the entry point, landing the user on `https://www.saucedemo.com/inventory.html` before each test begins.

Key selectors discovered during exploration:
- Sort dropdown: `[data-test="product-sort-container"]` with option values `az` ("Name (A to Z)"), `za` ("Name (Z to A)"), `lohi` ("Price (low to high)"), `hilo` ("Price (high to low)")
- Inventory item container: `[data-test="inventory-item"]`; name: `[data-test="inventory-item-name"]`; price: `[data-test="inventory-item-price"]`
- Add to cart buttons: `[data-test="add-to-cart-<product-slug>"]` (e.g. `add-to-cart-sauce-labs-backpack`); after adding, the button becomes `[data-test="remove-<product-slug>"]` with text "Remove"
- Cart badge: `[data-test="shopping-cart-badge"]` (absent from DOM entirely when cart is empty)
- Cart link: `[data-test="shopping-cart-link"]`
- Cart page (`/cart.html`): item rows show quantity, name, price, and a `Remove` button; `[data-test="continue-shopping"]` and `[data-test="checkout"]` buttons at the bottom. Checkout button is present even when the cart is empty.
- Checkout step one (`/checkout-step-one.html`): fields `[data-test="firstName"]`, `[data-test="lastName"]`, `[data-test="postalCode"]`; buttons `[data-test="cancel"]` and `[data-test="continue"]`. On validation failure, an error banner appears: `[data-test="error"]` with text such as "Error: First Name is required", "Error: Last Name is required", "Error: Postal Code is required" (validated in that order — first empty field wins), plus a dismiss button `[data-test="error-button"]`.
- Checkout step two / overview (`/checkout-step-two.html`): read-only list of cart items (no remove buttons), Payment Information ("SauceCard #31337"), Shipping Information ("Free Pony Express Delivery!"), Item total, Tax, and Total lines, plus `[data-test="cancel"]` and `[data-test="finish"]` buttons.
- Checkout complete (`/checkout-complete.html`): heading "Thank you for your order!", confirmation text, `[data-test="back-to-products"]` ("Back Home") button. After completing an order the cart is emptied (badge disappears).

Products and prices observed on the inventory page (default "Name (A to Z)" order):
1. Sauce Labs Backpack — $29.99
2. Sauce Labs Bike Light — $9.99
3. Sauce Labs Bolt T-Shirt — $15.99
4. Sauce Labs Fleece Jacket — $49.99
5. Sauce Labs Onesie — $7.99
6. Test.allTheThings() T-Shirt (Red) — $15.99

Verified "Price (low to high)" order: Onesie ($7.99), Bike Light ($9.99), Bolt T-Shirt ($15.99), Test.allTheThings() T-Shirt ($15.99), Backpack ($29.99), Fleece Jacket ($49.99).
Verified "Price (high to low)" order: Fleece Jacket ($49.99), Backpack ($29.99), Bolt T-Shirt ($15.99), Test.allTheThings() T-Shirt ($15.99), Bike Light ($9.99), Onesie ($7.99).
Note: when two items share the same price ($15.99), the relative order between them appears stable/tied — assertions should tolerate either ordering between the two $15.99 items, or assert on the full price sequence being non-decreasing/non-increasing rather than a strict item-by-item name match for tied prices.


## Test Scenarios

### 1. Product Sorting (Price-based)

**Seed:** `tests/seed.spec.ts`

#### 1.1. Default sort is Name (A to Z) on page load

**File:** `tests/sorting/default-sort.spec.ts`

**Steps:**
  1. After logging in via the seed flow, land on the inventory page.
    - expect: URL is https://www.saucedemo.com/inventory.html
    - expect: The sort dropdown [data-test="product-sort-container"] shows the selected option "Name (A to Z)" (value 'az')
  2. Read all product names in the inventory item list, in DOM order.
    - expect: Names are alphabetically sorted A to Z: Sauce Labs Backpack, Sauce Labs Bike Light, Sauce Labs Bolt T-Shirt, Sauce Labs Fleece Jacket, Sauce Labs Onesie, Test.allTheThings() T-Shirt (Red)

#### 1.2. Sort products by Price (low to high)

**File:** `tests/sorting/price-low-to-high.spec.ts`

**Steps:**
  1. Select the option "Price (low to high)" (value 'lohi') from [data-test="product-sort-container"].
    - expect: The dropdown's selected/displayed value updates to "Price (low to high)"
  2. Extract the text of every [data-test="inventory-item-price"] element in DOM order and parse to numbers.
    - expect: The resulting array of prices is sorted in strictly non-decreasing numeric order: 7.99, 9.99, 15.99, 15.99, 29.99, 49.99
  3. Extract the text of every [data-test="inventory-item-name"] element in DOM order.
    - expect: First item is 'Sauce Labs Onesie' ($7.99)
    - expect: Second item is 'Sauce Labs Bike Light' ($9.99)
    - expect: Third and fourth items are 'Sauce Labs Bolt T-Shirt' and 'Test.allTheThings() T-Shirt (Red)' (both $15.99, in either relative order)
    - expect: Fifth item is 'Sauce Labs Backpack' ($29.99)
    - expect: Sixth (last) item is 'Sauce Labs Fleece Jacket' ($49.99)

#### 1.3. Sort products by Price (high to low)

**File:** `tests/sorting/price-high-to-low.spec.ts`

**Steps:**
  1. Select the option "Price (high to low)" (value 'hilo') from [data-test="product-sort-container"].
    - expect: The dropdown's selected/displayed value updates to "Price (high to low)"
  2. Extract the text of every [data-test="inventory-item-price"] element in DOM order and parse to numbers.
    - expect: The resulting array of prices is sorted in strictly non-increasing numeric order: 49.99, 29.99, 15.99, 15.99, 9.99, 7.99
  3. Extract the text of every [data-test="inventory-item-name"] element in DOM order.
    - expect: First item is 'Sauce Labs Fleece Jacket' ($49.99)
    - expect: Second item is 'Sauce Labs Backpack' ($29.99)
    - expect: Third and fourth items are 'Sauce Labs Bolt T-Shirt' and 'Test.allTheThings() T-Shirt (Red)' (both $15.99, in either relative order)
    - expect: Fifth item is 'Sauce Labs Bike Light' ($9.99)
    - expect: Sixth (last) item is 'Sauce Labs Onesie' ($7.99)

#### 1.4. Toggle between price sorts and back to name sort updates order each time

**File:** `tests/sorting/toggle-sort-orders.spec.ts`

**Steps:**
  1. Select "Price (low to high)" from the sort dropdown.
    - expect: Prices are ascending, first item price is $7.99 (Onesie)
  2. Select "Price (high to low)" from the sort dropdown without reloading the page.
    - expect: Prices are descending, first item price is $49.99 (Fleece Jacket)
    - expect: Product count on the page remains 6 items throughout
  3. Select "Name (Z to A)" from the sort dropdown.
    - expect: Product names are sorted Z to A, first name is 'Test.allTheThings() T-Shirt (Red)', last name is 'Sauce Labs Backpack'
  4. Select "Name (A to Z)" from the sort dropdown again.
    - expect: Product names return to the original A-Z order matching the initial page-load order

#### 1.5. Sort selection persists product prices/details (no data corruption) after sorting

**File:** `tests/sorting/sort-preserves-item-data.spec.ts`

**Steps:**
  1. Record the price shown for 'Sauce Labs Backpack' while sorted Name (A to Z).
    - expect: Price recorded is $29.99
  2. Sort by "Price (high to low)", then locate the 'Sauce Labs Backpack' item card by its name text.
    - expect: The price displayed next to 'Sauce Labs Backpack' is still $29.99 (unchanged by sorting)
  3. Click 'Add to cart' on the 'Sauce Labs Backpack' item while in Price (high to low) order, then re-sort to "Price (low to high)".
    - expect: The 'Sauce Labs Backpack' item's button now reads 'Remove' regardless of its new sorted position
    - expect: The cart badge [data-test="shopping-cart-badge"] shows '1'

### 2. Shopping Cart Management

**Seed:** `tests/seed.spec.ts`

#### 2.1. Cart badge is absent when cart is empty on initial load

**File:** `tests/cart/empty-cart-badge.spec.ts`

**Steps:**
  1. On the inventory page immediately after login, check for the cart badge element.
    - expect: [data-test="shopping-cart-badge"] does not exist in the DOM (cart is empty, no badge shown)

#### 2.2. Add a single item to the cart updates badge and button state

**File:** `tests/cart/add-single-item.spec.ts`

**Steps:**
  1. Click [data-test="add-to-cart-sauce-labs-backpack"] on the inventory page.
    - expect: The button's text changes to 'Remove' and its data-test becomes 'remove-sauce-labs-backpack'
    - expect: [data-test="shopping-cart-badge"] appears and shows '1'
  2. Click [data-test="shopping-cart-link"] to open the cart page.
    - expect: URL is https://www.saucedemo.com/cart.html
    - expect: Exactly one cart item row is shown for 'Sauce Labs Backpack' with quantity '1' and price '$29.99'

#### 2.3. Add multiple items to the cart from the inventory page and verify badge count

**File:** `tests/cart/add-multiple-items.spec.ts`

**Steps:**
  1. Click 'Add to cart' for 'Sauce Labs Backpack' ([data-test="add-to-cart-sauce-labs-backpack"]).
    - expect: Cart badge shows '1'
  2. Click 'Add to cart' for 'Sauce Labs Bike Light' ([data-test="add-to-cart-sauce-labs-bike-light"]).
    - expect: Cart badge shows '2'
  3. Click 'Add to cart' for 'Sauce Labs Onesie' ([data-test="add-to-cart-sauce-labs-onesie"]).
    - expect: Cart badge shows '3'
  4. Verify that the buttons for all three added products now read 'Remove', while the remaining three products (Bolt T-Shirt, Fleece Jacket, Test.allTheThings() T-Shirt) still read 'Add to cart'.
    - expect: Only the 3 selected items show 'Remove'; the other 3 show 'Add to cart'
  5. Click [data-test="shopping-cart-link"] to navigate to the cart page.
    - expect: Cart page shows exactly 3 line items: Sauce Labs Backpack ($29.99, qty 1), Sauce Labs Bike Light ($9.99, qty 1), Sauce Labs Onesie ($7.99, qty 1)
    - expect: Each row's quantity is '1' and the item names/prices match what was added on the inventory page

#### 2.4. Add all six items to the cart in one session

**File:** `tests/cart/add-all-items.spec.ts`

**Steps:**
  1. Click every 'Add to cart' button on the inventory page for all 6 products.
    - expect: Cart badge shows '6'
    - expect: All 6 product buttons now read 'Remove'
  2. Navigate to the cart page.
    - expect: Cart page lists all 6 products with correct names and prices matching the inventory page
    - expect: Total of quantities across rows equals 6

#### 2.5. Remove an item from the inventory page after adding it

**File:** `tests/cart/remove-item-from-inventory.spec.ts`

**Steps:**
  1. Add 'Sauce Labs Backpack' and 'Sauce Labs Bike Light' to the cart from the inventory page.
    - expect: Cart badge shows '2'
  2. Click [data-test="remove-sauce-labs-backpack"] (the same button, now showing 'Remove') on the inventory page.
    - expect: Cart badge updates to show '1'
    - expect: The Backpack button reverts to 'Add to cart' with data-test 'add-to-cart-sauce-labs-backpack'
  3. Open the cart page.
    - expect: Only 'Sauce Labs Bike Light' is listed in the cart; 'Sauce Labs Backpack' is absent

#### 2.6. Remove an item from the cart page

**File:** `tests/cart/remove-item-from-cart-page.spec.ts`

**Steps:**
  1. Add 'Sauce Labs Backpack', 'Sauce Labs Bike Light', and 'Sauce Labs Onesie' to the cart, then navigate to the cart page.
    - expect: Cart page shows 3 items and badge shows '3'
  2. Click the 'Remove' button on the 'Sauce Labs Bike Light' row (e.g. [data-test="remove-sauce-labs-bike-light"]).
    - expect: The 'Sauce Labs Bike Light' row disappears from the cart list
    - expect: Cart badge updates to '2'
    - expect: The other two items (Backpack, Onesie) remain listed with unchanged quantities and prices

#### 2.7. Remove all items from the cart results in empty cart and no badge

**File:** `tests/cart/remove-all-items.spec.ts`

**Steps:**
  1. Add 3 items to the cart, then navigate to the cart page and click 'Remove' on all 3 line items one by one.
    - expect: After each removal, the badge count decrements by 1
    - expect: After removing the final item, [data-test="shopping-cart-badge"] is no longer present in the DOM
    - expect: The cart page shows zero item rows
  2. Click [data-test="continue-shopping"] to return to the inventory page.
    - expect: URL is https://www.saucedemo.com/inventory.html
    - expect: All 6 product buttons read 'Add to cart' (none show 'Remove')

#### 2.8. Cart contents persist across navigation to inventory and back

**File:** `tests/cart/cart-persists-navigation.spec.ts`

**Steps:**
  1. Add 'Sauce Labs Fleece Jacket' to the cart, navigate to the cart page, then click [data-test="continue-shopping"] to go back to inventory.
    - expect: Cart badge still shows '1' after returning to inventory
    - expect: 'Sauce Labs Fleece Jacket' button still reads 'Remove'
  2. Navigate to the cart page again via [data-test="shopping-cart-link"].
    - expect: 'Sauce Labs Fleece Jacket' is still listed in the cart with quantity 1 and price $49.99

#### 2.9. Cart item click navigates to product detail page

**File:** `tests/cart/cart-item-detail-navigation.spec.ts`

**Steps:**
  1. Add 'Sauce Labs Backpack' to the cart and open the cart page.
    - expect: 'Sauce Labs Backpack' row is visible
  2. Click the product name link 'Sauce Labs Backpack' within the cart row.
    - expect: Navigates to the product's inventory-item detail page showing the same product name, description, and price ($29.99)

### 3. Checkout Flow

**Seed:** `tests/seed.spec.ts`

#### 3.1. Complete checkout successfully with valid information (happy path)

**File:** `tests/checkout/complete-checkout-happy-path.spec.ts`

**Steps:**
  1. Add 'Sauce Labs Backpack' and 'Sauce Labs Onesie' to the cart from the inventory page, then click [data-test="shopping-cart-link"].
    - expect: Cart page shows both items with badge '2'
  2. Click [data-test="checkout"].
    - expect: Navigates to https://www.saucedemo.com/checkout-step-one.html
    - expect: Page heading reads 'Checkout: Your Information'
  3. Fill [data-test="firstName"] with 'Pandi', [data-test="lastName"] with 'Rajan', and [data-test="postalCode"] with '560001'.
    - expect: Fields contain the entered values
  4. Click [data-test="continue"].
    - expect: Navigates to https://www.saucedemo.com/checkout-step-two.html
    - expect: Page heading reads 'Checkout: Overview'
    - expect: Both cart items (Backpack $29.99, Onesie $7.99) are listed with quantity 1 and no Remove buttons present
    - expect: Payment Information shows 'SauceCard #31337'
    - expect: Shipping Information shows 'Free Pony Express Delivery!'
    - expect: Item total reads 'Item total: $37.98'
    - expect: Tax line is present and non-zero (e.g. 'Tax: $3.04')
    - expect: Total reads 'Total: $41.02' (item total + tax)
  5. Click [data-test="finish"].
    - expect: Navigates to https://www.saucedemo.com/checkout-complete.html
    - expect: Heading 'Thank you for your order!' is visible
    - expect: Confirmation text 'Your order has been dispatched, and will arrive just as fast as the pony can get there!' is visible
    - expect: The pony express image is visible
  6. Click [data-test="back-to-products"] ('Back Home').
    - expect: Navigates back to https://www.saucedemo.com/inventory.html
    - expect: The cart badge is no longer present (cart has been emptied)
    - expect: All product buttons read 'Add to cart'

#### 3.2. Checkout with a single item (minimum happy path)

**File:** `tests/checkout/checkout-single-item.spec.ts`

**Steps:**
  1. Add only 'Sauce Labs Bike Light' to the cart, open the cart, and click Checkout.
    - expect: Checkout step one page loads
  2. Fill in valid First Name, Last Name, and Postal Code, then click Continue.
    - expect: Overview page shows exactly 1 item, 'Sauce Labs Bike Light' at $9.99, with correct item total ($9.99), tax, and total
  3. Click Finish.
    - expect: Order completes and confirmation page is shown

#### 3.3. Validation error when First Name is missing

**File:** `tests/checkout/validation-missing-first-name.spec.ts`

**Steps:**
  1. Add an item to the cart, navigate to cart page, click Checkout to reach checkout-step-one.html.
    - expect: Form fields are empty
  2. Leave all fields empty and click [data-test="continue"] directly.
    - expect: Page remains on checkout-step-one.html (no navigation occurs)
    - expect: An error banner [data-test="error"] appears with text 'Error: First Name is required'
  3. Click the error dismiss button [data-test="error-button"].
    - expect: The error banner is dismissed/hidden

#### 3.4. Validation error when Last Name is missing

**File:** `tests/checkout/validation-missing-last-name.spec.ts`

**Steps:**
  1. Reach checkout-step-one.html with an item in the cart. Fill only [data-test="firstName"] with 'Pandi', leaving Last Name and Postal Code empty.
    - expect: First Name field contains 'Pandi'
  2. Click [data-test="continue"].
    - expect: Page remains on checkout-step-one.html
    - expect: Error banner shows 'Error: Last Name is required'

#### 3.5. Validation error when Postal Code is missing

**File:** `tests/checkout/validation-missing-postal-code.spec.ts`

**Steps:**
  1. Reach checkout-step-one.html with an item in the cart. Fill [data-test="firstName"] with 'Pandi' and [data-test="lastName"] with 'Rajan', leaving Postal Code empty.
    - expect: First and Last Name fields are filled
  2. Click [data-test="continue"].
    - expect: Page remains on checkout-step-one.html
    - expect: Error banner shows 'Error: Postal Code is required'
  3. Now fill [data-test="postalCode"] with '560001' and click Continue again.
    - expect: Navigation succeeds to checkout-step-two.html
    - expect: The error banner is no longer present

#### 3.6. Checkout step one validates fields in order (only first missing field's error shown)

**File:** `tests/checkout/validation-field-order.spec.ts`

**Steps:**
  1. With an item in the cart on checkout-step-one.html, leave all three fields empty and click Continue.
    - expect: Only the First Name error is shown, not Last Name or Postal Code errors simultaneously
  2. Fill First Name only and click Continue again.
    - expect: Error switches to 'Error: Last Name is required'
  3. Fill Last Name as well (First Name still filled) and click Continue again.
    - expect: Error switches to 'Error: Postal Code is required'

#### 3.7. Cancel on checkout step one returns to cart page

**File:** `tests/checkout/cancel-step-one.spec.ts`

**Steps:**
  1. Add an item to the cart and proceed to checkout-step-one.html.
    - expect: Checkout info form is visible
  2. Optionally fill in some field values, then click [data-test="cancel"].
    - expect: Navigates back to https://www.saucedemo.com/cart.html
    - expect: The previously added item is still present in the cart (cancel does not clear the cart)

#### 3.8. Cancel on checkout overview (step two) returns to cart page

**File:** `tests/checkout/cancel-step-two.spec.ts`

**Steps:**
  1. Add an item to the cart, complete checkout-step-one.html with valid data, and reach checkout-step-two.html (Overview).
    - expect: Overview page shows the item and totals
  2. Click [data-test="cancel"].
    - expect: Navigates back to https://www.saucedemo.com/cart.html
    - expect: The cart still contains the original item(s) (order was not placed)

#### 3.9. Checkout overview totals are correct for multiple items

**File:** `tests/checkout/overview-totals-calculation.spec.ts`

**Steps:**
  1. Add 'Sauce Labs Backpack' ($29.99), 'Sauce Labs Bike Light' ($9.99), and 'Sauce Labs Fleece Jacket' ($49.99) to the cart, then proceed through checkout-step-one.html with valid info to reach the Overview page.
    - expect: Overview lists all 3 items with correct individual prices
  2. Read the 'Item total' line.
    - expect: Item total equals $89.97 (29.99 + 9.99 + 49.99)
  3. Read the 'Tax' and 'Total' lines.
    - expect: Total equals Item total + Tax exactly (verify via arithmetic on the parsed values)

#### 3.10. Attempting checkout with an empty cart still allows reaching the info form

**File:** `tests/checkout/checkout-empty-cart.spec.ts`

**Steps:**
  1. Without adding any items, navigate directly to the cart page via [data-test="shopping-cart-link"].
    - expect: Cart page shows zero items and no badge
  2. Click [data-test="checkout"] on the empty cart.
    - expect: Navigates to checkout-step-one.html despite the cart being empty (document actual behavior — no blocking validation occurs at this step)
  3. Fill in valid First Name, Last Name, and Postal Code and click Continue.
    - expect: Navigates to checkout-step-two.html
    - expect: Overview shows zero item rows
    - expect: Item total reads $0.00 (or equivalent) and Total reflects tax-only or $0.00 depending on app behavior — record actual displayed values as the assertion baseline

#### 3.11. Whitespace-only input is treated as missing for required fields

**File:** `tests/checkout/validation-whitespace-input.spec.ts`

**Steps:**
  1. On checkout-step-one.html, fill First Name with a single space ' ', fill Last Name and Postal Code with valid values, and click Continue.
    - expect: Document actual behavior: either the app accepts the whitespace as a valid (non-empty) value and proceeds to the Overview page, or it rejects it and shows 'Error: First Name is required'. Assert whichever the live app actually does.

#### 3.12. Checkout complete page 'Generate PDF order' control is present

**File:** `tests/checkout/order-complete-page-controls.spec.ts`

**Steps:**
  1. Complete a full valid checkout (add item, fill info, continue, finish) to reach checkout-complete.html.
    - expect: Confirmation heading 'Thank you for your order!' is visible
    - expect: 'Back Home' button ([data-test="back-to-products"]) is visible and enabled
    - expect: 'Generate PDF order' button is visible and enabled
