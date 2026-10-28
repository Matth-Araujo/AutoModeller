import sys
import time
from django.core.cache import cache
from django.http import HttpResponse


def get_client_ip(request):
    """Obtém o IP real do cliente de forma segura."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


class SecurityHeadersAndRateLimitMiddleware:
    """
    Middleware de segurança para proteção contra os principais ataques web (OWASP Top 10):
    1. Headers de Segurança HTTP (CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy).
    2. Proteção contra Força Bruta em autenticação (/login, /register) e DoS em criação/execução de experimentos.
    """

    # Limites por janela de 60 segundos por IP
    RATE_LIMITS = {
        'admin_post': (5, 60),       # Máx 5 tentativas de login no painel /admin por minuto por IP
        'auth_post': (15, 60),       # Máx 15 tentativas de login/cadastro por minuto por IP
        'experiment_post': (20, 60), # Máx 20 disparos de modelagem por minuto por IP
        'general_req': (240, 60),    # Máx 240 requisições gerais por minuto por IP
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verifica rate limiting (exceto durante execução da suíte de testes unitários)
        is_testing = 'test' in sys.argv
        if not is_testing or getattr(request, '_enforce_rate_limit_in_test', False):
            blocked_response = self._check_rate_limit(request)
            if blocked_response is not None:
                return self._apply_security_headers(blocked_response)

        response = self.get_response(request)
        return self._apply_security_headers(response)

    def _check_rate_limit(self, request):
        ip = get_client_ip(request)
        path = request.path.lower()
        method = request.method.upper()

        bucket = 'general_req'
        if method == 'POST':
            if '/admin' in path:
                bucket = 'admin_post'
            elif any(p in path for p in ('/login', '/register', '/password')):
                bucket = 'auth_post'
            elif any(p in path for p in ('/experiments/new', '/retry', '/select-template')):
                bucket = 'experiment_post'

        max_requests, window_seconds = self.RATE_LIMITS[bucket]
        now_window = int(time.time() // window_seconds)
        cache_key = f"rl:{bucket}:{ip}:{now_window}"

        current_count = cache.get(cache_key, 0)
        if current_count >= max_requests:
            return HttpResponse(
                "429 Too Many Requests - Limite de requisições excedido por segurança. Tente novamente em instantes.",
                status=429,
                content_type="text/plain; charset=utf-8",
            )
        cache.set(cache_key, current_count + 1, timeout=window_seconds + 5)
        return None

    def _apply_security_headers(self, response):
        # Previne MIME-sniffing
        response.setdefault('X-Content-Type-Options', 'nosniff')
        # Previne Clickjacking
        response.setdefault('X-Frame-Options', 'DENY')
        # Controla envio de Referer para proteger UUIDs de experimentos
        response.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        # Restringe APIs sensíveis do navegador
        response.setdefault(
            'Permissions-Policy',
            'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=()'
        )
        # Isolamento de contexto Cross-Origin
        response.setdefault('Cross-Origin-Opener-Policy', 'same-origin')

        # Content Security Policy (CSP) compatível com Bootstrap CDN, Google Fonts, 3Dmol.js (WebGL/Workers) e RCSB PDB
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: https://cdn.jsdelivr.net https://3dmol.org",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "font-src 'self' data: https://cdn.jsdelivr.net https://fonts.gstatic.com",
            "img-src 'self' data: blob: https:",
            "connect-src 'self' https://files.rcsb.org https://*.rcsb.org https://3dmol.org https://cdn.jsdelivr.net",
            "worker-src 'self' blob:",
            "frame-ancestors 'none'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.setdefault('Content-Security-Policy', '; '.join(csp_directives))
        return response
