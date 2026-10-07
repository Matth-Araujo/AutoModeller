def site_language(request):
    """
    Context processor para fornecer o idioma atual (padrão: inglês).
    Permite alternar entre English ('en') e Português ('pt').
    """
    lang = request.session.get('site_lang') or request.COOKIES.get('site_lang', 'en')
    if lang not in ('en', 'pt'):
        lang = 'en'
    return {
        'site_lang': lang,
        'is_pt': lang == 'pt',
        'is_en': lang == 'en',
    }
