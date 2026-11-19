from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class EmailBackend(ModelBackend):
    """
    Autenticação utilizando o e-mail do usuário no lugar do username.
    Também permite fallback para username caso já exista.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get('email') or username
        if not email or not password:
            return None
        identifier = email.strip()
        if not identifier:
            return None
        try:
            candidates = User.objects.filter(
                Q(email__iexact=identifier) | Q(username__iexact=identifier)
            ).distinct()
            for user in candidates:
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
        except Exception:
            return None
        return None
