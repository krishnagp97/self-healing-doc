
class UserService {
    String getUser(int userId) {
        return "User " + userId;
    }

    boolean deleteUser(int userId) {
        return true;
    }
}

class UserController {
    void createUser(String name) {
        System.out.println(name);
    }
}