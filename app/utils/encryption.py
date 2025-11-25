import bcrypt


def hash_password(password):
    # 生成盐
    salt = bcrypt.gensalt()
    # 使用生成的盐对密码进行哈希
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def check_password(hashed_password: str, user_password: str) -> bool:
    # 将用户输入的密码和存储的哈希密码进行比对
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password.encode('utf-8'))
