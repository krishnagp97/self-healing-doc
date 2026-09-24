
struct UserService;

impl UserService {
    fn get_user(user_id: i32) -> String {
        format!("User {}", user_id)
    }

    fn delete_user(user_id: i32) -> bool {
        true
    }
}

fn create_user(name: &str) -> String {
    name.to_string()
}