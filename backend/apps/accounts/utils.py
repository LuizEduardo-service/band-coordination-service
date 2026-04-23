from .models import UserProfile


def get_user_instruments(user) -> list:
    try:
        return list(user.profile.instruments or [])
    except UserProfile.DoesNotExist:
        return []
