class UserService {
    getUser(userId, includeEmail = false) {
        return userId;
    }
    deleteUser(userId) {
        return true;
    }
}
function createUser(name, active = true) {
    return { name, active };
}
