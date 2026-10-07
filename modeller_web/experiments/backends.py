from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class EmailBackend(ModelBackend):
    """
    Autenticação utilizando o e-mail do usuário no lugar do username.
    Também permite fallback para username caso já exista.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get('email') or username
        if not email or not password:
            return None
        try:
            # Tenta encontrar o usuário pelo e-mail (case-insensitive)
            user = User.objects.filter(email__iexact=email.strip()).first()
            if not user:
                # Fallback para o campo username
                user = User.objects.filter(username__iexact=email.strip()).first()
            if user and user.check_password(password):
                return user
        except Exception:
            return None
        return None
