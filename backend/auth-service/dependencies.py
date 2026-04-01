from backend.auth_service.models.user import UserResponse

def get_current_user():
    # Minimal stub for dependency
    return UserResponse(id=1, email="stub@example.com", is_active=True)
