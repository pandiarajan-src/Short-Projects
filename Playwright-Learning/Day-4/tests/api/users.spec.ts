import {test, expect} from '@playwright/test';

interface User {
    id: number;
    name: string;
    job: string;
}

test.describe('User API Tests', () => {
    test('create a user via API and verify it', async ({request}) => {
        const newUser: Omit<User, 'id'> = {
            name: 'John Doe',
            job: 'Software Developer',
        };

        const response = await request.post('https://jsonplaceholder.typicode.com/users', {
            data: newUser,
        });

        expect(response.status()).toBe(201);

        const responseBody: User = await response.json();
        expect(responseBody.name).toBe(newUser.name);
        expect(responseBody.job).toBe(newUser.job);
        expect(responseBody.id).toBeDefined();
    });

    // test('authenticate user flow', async ({request}) => {

    //     // 1. Get a token from the API
    //     const authResponse = await request.post('https://restfull-booker.herokuapp.com/auth', {
    //         data: {
    //             username: 'admin',
    //             password: 'password123'
    //         }
    //     });
    //     const {token}: {token: string} = await authResponse.json();
    //     expect(token).toBeDefined();
        
    //     // 2. Use the token to access a protected resource
    //     const protectedResponse = await request.get('https://restfull-booker.herokuapp.com/booking/1', {
    //         headers: {
    //             'Authorization': `Bearer ${token}`
    //         }
    //     });
    //     expect(protectedResponse.status()).toBe(200);

    //     const bookingData = await protectedResponse.json();
    //     expect(bookingData).toHaveProperty('firstname');
    //     expect(bookingData).toHaveProperty('lastname');

    //     // 3. Use it on a protected call
    //     const deleteResponse = await request.delete('https://restfull-booker.herokuapp.com/booking/1', {
    //         headers: {
    //             'Authorization': `Bearer ${token}`
    //         }
    //     });
    //     expect(deleteResponse.status()).toBe(201); // Assuming 201 is the expected status for a successful delete
    // });

});

