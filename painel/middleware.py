class SemCache:
    """Nao deixa o navegador guardar as paginas do app em cache.

    Sem isso, depois de "Sair da conta" o botao voltar ainda mostra a pagina
    autenticada (parece que o logout nao funcionou). Estaticos ficam de fora.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        resposta = self.get_response(request)
        if not (request.path.startswith('/static/') or request.path.startswith('/media/')):
            resposta['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            resposta['Pragma'] = 'no-cache'
        return resposta
