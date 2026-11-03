ROLES = ["CUSTOMER", "CONSULTANT", "ADMIN"]

ROLE_SCOPES = {
    "CUSTOMER": [
        "vehicle:create",
        "vehicle:read_own",
        "vehicle:update_own",
        "vehicle:delete_own",
        "inspection:read",
    ],
    "CONSULTANT": [
        "vehicle:read",
        "inspection:read",
        "inspection:update",
        "inspection:claim",
    ],
    "ADMIN": [
        "vehicle:create",
        "vehicle:read",
        "vehicle:update",
        "vehicle:delete",
        "inspection:read",
        "inspection:update",
        "inspection:claim",
        "user:read",
        "user:update",
        "user:create",
    ],
}
