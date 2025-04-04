from rest_framework.throttling import UserRateThrottle


class TokenRateThrottle(UserRateThrottle):
    scope = 'token'
