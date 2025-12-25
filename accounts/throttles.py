from rest_framework.throttling import UserRateThrottle


class LoginRateThrottle(UserRateThrottle):
    scope = "login"

class RefreshTokenRateThrottle(UserRateThrottle):
    scope = "refresh_token"

