"""
utils/backup.py — Backup automático com criptografia
Backup local diário criptografado por chave do hardware
"""
import os, sys, shutil, hashlib, base64
from datetime import datetime

def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _chave_hardware():
    """Chave única baseada no hardware do PC"""
    try:
        import subprocess
        uuid = subprocess.check_output(
            "wmic csproduct get uuid", shell=True,
            stderr=subprocess.DEVNULL).decode()
        uuid = [x.strip() for x in uuid.split("\n")
                if x.strip() and x.strip() != "UUID"]
        seed = uuid[0] if uuid else "padaria_laine"
    except Exception:
        import platform
        seed = platform.node()
    return hashlib.sha256(f"PDV_BACKUP_{seed}".encode()).digest()[:32]

def _criptografar(dados: bytes) -> bytes:
    """Criptografia XOR com chave do hardware"""
    chave = _chave_hardware()
    return bytes([dados[i] ^ chave[i % len(chave)]
                  for i in range(len(dados))])

def fazer_backup():
    """
    Faz backup criptografado do banco.
    Arquivo .bak.enc — só abre no mesmo PC ou com a chave.
    """
    base    = get_base_dir()
    db_path = os.path.join(base, "banco", "padaria.db")

    if not os.path.exists(db_path):
        return False, "Banco não encontrado."

    pasta_bk = os.path.join(base, "backups")
    os.makedirs(pasta_bk, exist_ok=True)

    agora   = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(pasta_bk, f"padaria_{agora}.bak.enc")

    try:
        # Ler banco
        with open(db_path, "rb") as f:
            dados = f.read()

        # Criptografar
        dados_enc = _criptografar(dados)

        # Salvar com cabeçalho de identificação
        cabecalho = b"PDV_PADARIA_BACKUP_V2\n"
        with open(destino, "wb") as f:
            f.write(cabecalho + dados_enc)

        # Manter apenas últimos 30 backups
        backups = sorted([
            os.path.join(pasta_bk, f)
            for f in os.listdir(pasta_bk)
            if f.endswith(".bak.enc")
        ])
        while len(backups) > 30:
            os.remove(backups.pop(0))

        return True, f"Backup: {os.path.basename(destino)}"

    except Exception as e:
        return False, str(e)

def restaurar_backup(arquivo_enc):
    """
    Restaura backup criptografado.
    Só funciona no mesmo PC que fez o backup!
    """
    try:
        base    = get_base_dir()
        db_path = os.path.join(base, "banco", "padaria.db")

        with open(arquivo_enc, "rb") as f:
            conteudo = f.read()

        # Remover cabeçalho
        cabecalho = b"PDV_PADARIA_BACKUP_V2\n"
        if not conteudo.startswith(cabecalho):
            return False, "Arquivo inválido ou corrompido."

        dados_enc = conteudo[len(cabecalho):]

        # Descriptografar
        dados = _criptografar(dados_enc)  # XOR é simétrico

        # Fazer backup do banco atual antes de restaurar
        if os.path.exists(db_path):
            shutil.copy2(db_path, db_path + ".antes_restauracao")

        with open(db_path, "wb") as f:
            f.write(dados)

        return True, "Backup restaurado com sucesso!"

    except Exception as e:
        return False, str(e)

def listar_backups():
    """Lista backups disponíveis"""
    base     = get_base_dir()
    pasta_bk = os.path.join(base, "backups")
    if not os.path.exists(pasta_bk):
        return []
    return sorted([
        f for f in os.listdir(pasta_bk)
        if f.endswith(".bak.enc")
    ], reverse=True)

def fazer_backup_async(callback=None):
    """Backup em background sem travar o sistema"""
    import threading
    def _fazer():
        ok, msg = fazer_backup()
        if callback:
            callback(ok, msg)
    threading.Thread(target=_fazer, daemon=True).start()
