from enum import StrEnum, auto

# 最佳实践：使用 auto() 自动生成值，或者显式定义
class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

# 比较时可以直接当做字符串处理
def check_role(role: UserRole):
    if role == "admin": # StrEnum 允许这样做，但推荐用 UserRole.ADMIN
        pass