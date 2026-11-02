ROLES = ["CUSTOMER", "CONSULTANT", "ADMIN"]

ROLE_SCOPES = {
    "CUSTOMER": [
        "vehicle:create",
        "vehicle:read",
        "vehicle:update",
        "vehicle:delete",
        "inspection:read",
    ],
    "CONSULTANT": [
        "vehicle:read",
        "inspection:read",
        "inspection:update",
    ],
    "ADMIN": [
        "vehicle:create",
        "vehicle:read",
        "vehicle:update",
        "vehicle:delete",
        "inspection:read",
        "inspection:update",
        "user:read",
        "user:update",
        "user:create",
    ],
}
