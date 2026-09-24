type User = {
    id: number;
    name: string;
};

function UserCard(user: User): string {
    return user.name;
}

export {};