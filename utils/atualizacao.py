"""
utils/atualizacao.py — Atualização automática via GitHub Releases
Baixa o EXE novo completo — funciona mesmo com PyInstaller!
"""
import os, sys, json, threading, urllib.request, shutil
from datetime import datetime

GITHUB_USUARIO = "edemilsonrussin12"
GITHUB_REPO    = "pdv-padaria-dalaine"

URL_VERSAO  = f"https://raw.githubusercontent.com/{GITHUB_USUARIO}/{GITHUB_REPO}/main/versao.json"
URL_RELEASE = f"https://github.com/{GITHUB_USUARIO}/{GITHUB_REPO}/releases/latest/download/PDV_Padaria_DaLaine.exe"

def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_versao_atual():
    try:
        path = os.path.join(get_base_dir(), "versao.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("versao", "0.0.0")
    except Exception:
        return "0.0.0"

def _ssl_open(url, timeout=10):
    """Abre URL com SSL — tenta padrão, fallback sem verificação"""
    import ssl
    req = urllib.request.Request(url, headers={"User-Agent": "PDV-PadariaLaine/2.0"})
    try:
        ctx = ssl.create_default_context()
        return urllib.request.urlopen(req, timeout=timeout, context=ctx)
    except Exception:
        ctx2 = ssl.create_default_context()
        ctx2.check_hostname = False
        ctx2.verify_mode = ssl.CERT_NONE
        return urllib.request.urlopen(req, timeout=timeout, context=ctx2)

def verificar_versao_online():
    try:
        with _ssl_open(URL_VERSAO, timeout=8) as r:
            dados = json.loads(r.read().decode())
        return dados.get("versao"), dados.get("notas",""), dados.get("obrigatorio", False)
    except Exception as e:
        print(f"[PDV] Erro verificar versão: {e}")
        return None, "", False

def baixar_e_instalar(versao_nova="", callback_progresso=None):
    """
    Baixa o EXE novo do GitHub Releases e substitui o atual.
    Funciona mesmo com PyInstaller --onedir!
    """
    try:
        base    = get_base_dir()
        exe_atual = os.path.join(base, "PDV_Padaria_DaLaine.exe")
        exe_novo  = os.path.join(base, "PDV_Padaria_DaLaine_novo.exe")
        exe_bak   = os.path.join(base, "PDV_Padaria_DaLaine_bak.exe")

        if callback_progresso:
            callback_progresso("⬇️ Baixando novo EXE...")

        # Baixa o EXE novo
        with _ssl_open(URL_RELEASE, timeout=120) as r:
            total = int(r.headers.get("Content-Length", 0))
            baixado = 0
            with open(exe_novo, "wb") as f:
                while True:
                    chunk = r.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    baixado += len(chunk)
                    if callback_progresso and total > 0:
                        pct = int(baixado / total * 100)
                        callback_progresso(f"⬇️ Baixando... {pct}%")

        if callback_progresso:
            callback_progresso("📦 Instalando...")

        # Cria bat para substituir o EXE após fechar
        bat_path = os.path.join(base, "_atualizar.bat")
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(f"""@echo off
timeout /t 2 /nobreak >nul
if exist "{exe_bak}" del /f /q "{exe_bak}"
move /y "{exe_atual}" "{exe_bak}" >nul
move /y "{exe_novo}" "{exe_atual}" >nul
del /f /q "{bat_path}"
start "" "{exe_atual}"
""")

        # Atualiza versao.json local
        if versao_nova:
            versao_path = os.path.join(base, "versao.json")
            dados_versao = {
                "versao": versao_nova,
                "data": datetime.now().strftime("%Y-%m-%d"),
                "notas": "Atualização automática",
                "obrigatorio": False
            }
            with open(versao_path, "w", encoding="utf-8") as f:
                json.dump(dados_versao, f, ensure_ascii=False, indent=4)

        return True, bat_path

    except Exception as e:
        # Limpa arquivo parcial se existir
        try:
            if os.path.exists(exe_novo):
                os.remove(exe_novo)
        except Exception:
            pass
        return False, str(e)

def aplicar_atualizacao(bat_path):
    """Executa o bat que substitui o EXE e reinicia"""
    import subprocess
    subprocess.Popen(
        ["cmd", "/c", bat_path],
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    sys.exit(0)

def verificar_atualizacao_async(callback=None):
    """Verifica atualização em background ao iniciar"""
    def _verificar():
        try:
            versao_nova, notas, obrigatorio = verificar_versao_online()
            versao_atual = get_versao_atual()

            print(f"[PDV] Versão local: {versao_atual} | GitHub: {versao_nova}")

            if not versao_nova or versao_nova == versao_atual:
                print("[PDV] Sistema atualizado. Nenhuma ação necessária.")
                return

            print(f"[PDV] Atualização {versao_nova} disponível!")
            if callback:
                callback(True, versao_nova, notas, obrigatorio)

        except Exception as e:
            print(f"[PDV] Verificação falhou: {e}")

    threading.Thread(target=_verificar, daemon=True).start()

def mostrar_dialogo_atualizacao(parent, versao, notas, obrigatorio=False):
    """Aviso de atualização disponível"""
    try:
        import customtkinter as ctk
        from tema import (COR_CARD, COR_ACENTO, COR_ACENTO2,
                         COR_SUCESSO, COR_SUCESSO2, COR_PERIGO, COR_PERIGO2,
                         COR_TEXTO, COR_TEXTO_SUB, FONTE_TITULO,
                         FONTE_LABEL, FONTE_SMALL, FONTE_BTN)

        win = ctk.CTkToplevel(parent)
        win.title("Atualização Disponível!")
        win.geometry("420x280")
        win.configure(fg_color=COR_CARD)
        win.grab_set()
        win.lift()
        win.focus_force()

        ctk.CTkLabel(win, text="🔄  Atualização Disponível!",
                     font=FONTE_TITULO, text_color=COR_ACENTO).pack(pady=(24,8))
        ctk.CTkLabel(win, text=f"Versão {versao} disponível!",
                     font=FONTE_LABEL, text_color=COR_TEXTO).pack()
        if notas:
            ctk.CTkLabel(win, text=notas,
                         font=FONTE_SMALL, text_color=COR_TEXTO_SUB,
                         wraplength=360).pack(pady=8)

        lbl_status = ctk.CTkLabel(win, text="",
                                   font=FONTE_SMALL, text_color=COR_ACENTO)
        lbl_status.pack(pady=4)

        def instalar():
            btn_instalar.configure(state="disabled", text="Instalando...")
            lbl_status.configure(text="⬇️ Baixando...")
            win.update()

            def _progress(msg):
                win.after(0, lambda: lbl_status.configure(text=msg))

            def _instalar():
                ok, resultado = baixar_e_instalar(versao, _progress)
                if ok:
                    win.after(0, lambda: [
                        lbl_status.configure(
                            text="✅ Instalado! Reiniciando...",
                            text_color=COR_SUCESSO),
                        win.after(1500, lambda: aplicar_atualizacao(resultado))
                    ])
                else:
                    win.after(0, lambda: [
                        lbl_status.configure(
                            text=f"❌ Erro: {resultado}",
                            text_color=COR_PERIGO),
                        btn_instalar.configure(state="normal", text="Tentar Novamente")
                    ])

            threading.Thread(target=_instalar, daemon=True).start()

        btn_instalar = ctk.CTkButton(
            win, text="⬇️  Instalar Agora e Reiniciar",
            font=FONTE_BTN, height=44,
            fg_color=COR_SUCESSO, hover_color=COR_SUCESSO2,
            text_color="white",
            command=instalar)
        btn_instalar.pack(pady=8, padx=40, fill="x")

        ctk.CTkButton(win, text="Mais tarde",
                      font=FONTE_SMALL, height=32,
                      fg_color="transparent",
                      hover_color=COR_CARD,
                      text_color=COR_TEXTO_SUB,
                      command=win.destroy).pack()

    except Exception as e:
        print(f"[PDV] Dialogo erro: {e}")
