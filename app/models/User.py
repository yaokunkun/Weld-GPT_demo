from dataclasses import dataclass


@dataclass
class User:
    UserID: int = 0
    UserName: str = "nan"
    Password: str = "nan"
    PhoneNumber: str = "nan"
    UserRole: str = "nan"