import subprocess

def versao_sistema(request):
    try:
        # Tenta pegar o hash curto do último commit git (ex: a1b2c3d)
        versao = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'], 
            stderr=subprocess.STDOUT
        ).decode('utf-8').strip()
    except Exception:
        # Se der erro (não tiver git instalado ou pasta .git), mostra padrão
        versao = 'Local/Dev'

    return {'versao_sistema': versao}