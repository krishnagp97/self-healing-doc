
package main

type UserService struct{}

func (u UserService) GetUser(userID int) string {
    return "user"
}

func (u UserService) DeleteUser(userID int) bool {
    return true
}

func CreateUser(name string) string {
    return name
}