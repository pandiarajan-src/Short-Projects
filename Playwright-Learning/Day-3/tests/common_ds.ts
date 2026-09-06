// Array of specific types of users to test login functionality
export const user_names: string[] = ['standard_user', 'locked_out_user', 'problem_user', 'performance_glitch_user'];

// union type - "this can be one of these exact values"
type UserType = 'standard_user' | 'locked_out_user' | 'problem_user' | 'performance_glitch_user';

//Enum - Status
enum Status {
    Success,
    Failure,
}

//Optional property (the '?') like a nullable type, but more explicit
interface Product {
    name: string;
    price?: number; // optional property
    discount?: number; // optional property
}

export const users: { username: string; expectSuccess: boolean }[] = [
    { username: 'standard_user', expectSuccess: true },
    { username: 'locked_out_user', expectSuccess: false },
    { username: 'problem_user', expectSuccess: true },
    { username: 'performance_glitch_user', expectSuccess: true },
];
