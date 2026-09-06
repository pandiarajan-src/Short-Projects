import {test, expect} from '@playwright/test';

test('should add a new todo', async ({ page }) => {
    // 1. Navigate to the TodoMVC app
    await page.goto('https://demo.playwright.dev/todomvc');

    // 2. Locate the input box and type a new todo item
    const newTodoInput = page.getByPlaceholder('What needs to be done?');
    await newTodoInput.fill('Learn Playwright Testing');
    await newTodoInput.press('Enter');

    // 3. Assert that the new todo item is added to the list
    const todoList = page.getByTestId('todo-title');
    await expect(todoList).toHaveText('Learn Playwright Testing');
});

test('should mark a todo as completed', async ({ page }) => {
    // 1. Navigate to the TodoMVC app
    await page.goto('https://demo.playwright.dev/todomvc');

    // 2. Add a new todo item
    const newTodoInput = page.getByPlaceholder('What needs to be done?');
    await newTodoInput.fill('Learn Playwright Testing');
    await newTodoInput.press('Enter');

    // 3. Mark the todo item as completed
    const todoCheckbox = page.getByRole('checkbox', { name: 'Toggle Todo' });
    await todoCheckbox.check();

    // 4. Assert that the todo item is marked as completed
    const todoItem = page.getByTestId('todo-item');
    await expect(todoItem).toHaveClass(/completed/);
});

test('should add three todos and filter them', async ({ page }) => {
    // 1. Navigate to the TodoMVC app
    await page.goto('https://demo.playwright.dev/todomvc');

    // 2. Add three new todo items
    const newTodoInput = page.getByPlaceholder('What needs to be done?');
    await newTodoInput.fill('Learn Playwright Testing');
    await newTodoInput.press('Enter');
    await newTodoInput.fill('Write Tests');
    await newTodoInput.press('Enter');
    await newTodoInput.fill('Run Tests');
    await newTodoInput.press('Enter');

    // 3. Mark the second todo item as completed
    const secondTodoCheckbox = page.getByRole('checkbox', { name: 'Toggle Todo' }).nth(1);
    await secondTodoCheckbox.check();

    // 4. Filter to show only active todos
    const activeFilter = page.getByRole('link', { name: 'Active' });
    await activeFilter.click();

    // 5. Assert that only the active todos are displayed
    const todoItems = page.getByTestId('todo-item');
    await expect(todoItems).toHaveCount(2);
    await expect(todoItems.nth(0)).toHaveText('Learn Playwright Testing');
    await expect(todoItems.nth(1)).toHaveText('Run Tests');

    // 6. Filter to show only completed todos
    const completedFilter = page.getByRole('link', { name: 'Completed' });
    await completedFilter.click();

    // 7. Assert that only the completed todo is displayed
    const completedTodoItems = page.getByTestId('todo-item');
    await expect(completedTodoItems).toHaveCount(1);
    await expect(completedTodoItems.nth(0)).toHaveText('Write Tests');
});
