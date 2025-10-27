from typing import Dict, List, Set
from app.api.models.user import UserRole


class PermissionManager:

    # Define all available permissions
    PERMISSIONS = {
        # Asset permissions
        "asset:read": "View assets",
        "asset:create": "Create assets",
        "asset:update": "Update assets",
        "asset:delete": "Delete assets",

        # Task permissions
        "task:read": "View tasks",
        "task:create": "Create tasks",
        "task:update": "Update tasks",
        "task:delete": "Delete tasks",
        "task:execute": "Execute tasks",

        # Vulnerability permissions
        "vulnerability:read": "View vulnerabilities",
        "vulnerability:create": "Create vulnerabilities",
        "vulnerability:update": "Update vulnerabilities",
        "vulnerability:delete": "Delete vulnerabilities",
        "vulnerability:verify": "Verify vulnerabilities",

        # Report permissions
        "report:read": "View reports",
        "report:create": "Create reports",
        "report:update": "Update reports",
        "report:delete": "Delete reports",
        "report:generate": "Generate reports",

        # User permissions
        "user:read": "View users",
        "user:create": "Create users",
        "user:update": "Update users",
        "user:delete": "Delete users",

        # System permissions
        "system:settings": "Manage system settings",
        "system:logs": "View system logs",
        "system:audit": "View audit logs",
    }

    # Role-based permission mapping
    ROLE_PERMISSIONS: Dict[UserRole, List[str]] = {
        UserRole.ADMIN: [
            # Full access to everything
            *PERMISSIONS.keys()
        ],

        UserRole.SECURITY_ANALYST: [
            # Asset management
            "asset:read", "asset:create", "asset:update",

            # Task management
            "task:read", "task:create", "task:update", "task:execute",

            # Vulnerability management
            "vulnerability:read", "vulnerability:create",
            "vulnerability:update", "vulnerability:verify",

            # Report management
            "report:read", "report:create", "report:generate",

            # Limited user access
            "user:read",
        ],

        UserRole.OPERATOR: [
            # Read access to most resources
            "asset:read", "asset:create", "asset:update",

            # Task execution
            "task:read", "task:create", "task:execute",

            # Limited vulnerability access
            "vulnerability:read", "vulnerability:update",

            # Report viewing
            "report:read",
        ],

        UserRole.VIEWER: [
            # Read-only access
            "asset:read",
            "task:read",
            "vulnerability:read",
            "report:read",
        ]
    }

    @classmethod
    def get_role_permissions(cls, role: UserRole) -> List[str]:
        """Get permissions for a specific role"""
        return cls.ROLE_PERMISSIONS.get(role, [])

    @classmethod
    def get_user_permissions(cls, role: UserRole, custom_permissions: List[str] = None) -> Set[str]:
        """Get all permissions for a user (role + custom)"""
        role_permissions = set(cls.get_role_permissions(role))

        if custom_permissions:
            # Add custom permissions but only if they're valid
            valid_custom = set(custom_permissions) & set(cls.PERMISSIONS.keys())
            role_permissions.update(valid_custom)

        return role_permissions

    @classmethod
    def has_permission(cls, user_role: UserRole, user_permissions: List[str],
                      required_permission: str) -> bool:
        """Check if user has a specific permission"""
        all_permissions = cls.get_user_permissions(user_role, user_permissions)
        return required_permission in all_permissions

    @classmethod
    def validate_permissions(cls, permissions: List[str]) -> List[str]:
        """Validate and return only valid permissions"""
        return [p for p in permissions if p in cls.PERMISSIONS]


# Permission dependency injection
permission_manager = PermissionManager()