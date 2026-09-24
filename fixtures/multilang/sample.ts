
class UserService {
    getUser(userId: number): string {
        return `User ${userId}`;
    }
}

function createUser(name: string): string {
    return name;
}
export {};