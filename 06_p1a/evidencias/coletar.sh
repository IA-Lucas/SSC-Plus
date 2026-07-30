#!/usr/bin/env bash
# SSC+ P1-A — coleta reproduzivel de evidencias de preflight (SOMENTE LEITURA).
# Nunca imprime valores de segredos: apenas nomes de variaveis, flags booleanas
# e claims de plano. Uso: bash 06_p1a/evidencias/coletar.sh [dir-saida]
#
# P1-A.1: (a) escritor unico — a coleta SEGURA o lock p1-ops (lease +
# fencing da P0) do inicio ao fim; se outra sessao o detem, aborta com
# codigo 3 ANTES de escrever ou invocar qualquer CLI; (b) redacao em
# linha — e-mail e caminho de usuario nunca persistem em nova coleta.
set -u
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"

# --- escritor unico (P1-A.1): adquire e segura o lock durante a coleta ---
python -c "
import sys, time
sys.path.insert(0, r'$RAIZ/06_p1a'); sys.path.insert(0, r'$RAIZ/05_p0')
from escritor import EscritorP1
e = EscritorP1(r'$RAIZ/locks', sessao='p1-ops')
e.adquirir()
print('escritor unico adquirido (p1-ops)', flush=True)
while True:
    time.sleep(5)
    e.renovar()
" &
_ESCRITOR_PID=$!
sleep 1
if ! kill -0 "$_ESCRITOR_PID" 2>/dev/null; then
  echo "escritor unico: outra sessao detem o lock; coleta abortada ANTES" \
       "de escrever ou invocar CLI" >&2
  exit 3
fi
trap 'kill "$_ESCRITOR_PID" 2>/dev/null' EXIT

SAIDA="${1:-$RAIZ/06_p1a/evidencias/coleta-$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$SAIDA"

etapa() { echo "== $1"; }

# Redacao em linha: e-mail (PII operacional) e usuario local da estacao.
USUARIO="$(basename "$HOME")"
redigir() {
  sed -E -e 's/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/<EMAIL-REDACTED>/g' \
         -e "s|${USUARIO}|<USUARIO>|g"
}

# --- 0. ambiente da coleta -------------------------------------------------
etapa "ambiente"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  uname -a
  python --version
  bash --version | head -1
} | tee "$SAIDA/00_ambiente.txt"

# --- 1. pre-condicoes git + testes ------------------------------------------
etapa "pre-condicoes"
{
  git -C "$RAIZ" log --oneline -4
  git -C "$RAIZ" status --porcelain
  if git -C "$RAIZ" merge-base --is-ancestor a96eda5 0da9d41; then
    echo "merge-base a96eda5..0da9d41: ANCESTOR_OK"
  else
    echo "merge-base a96eda5..0da9d41: ANCESTOR_FAIL"
  fi
} | tee "$SAIDA/01_git.txt"
python -m unittest discover -s "$RAIZ/05_p0/tests" 2>&1 | tail -3 \
  | tee "$SAIDA/02_testes_p0.txt"
python "$RAIZ/05_p0/cenarios/prova_central.py" 2>&1 | tail -2 \
  | tee "$SAIDA/03_prova_central.txt"

# --- 2. auditoria de ambiente (somente NOMES de variaveis) -------------------
etapa "ambiente-payg"
printenv | cut -d= -f1 | grep -iE '(^|_)(api[_ ]?key|auth[_ ]?token|access[_ ]?token|api[_ ]?secret|secret[_ ]?key)(_|$)|^(OPENAI|ANTHROPIC|GEMINI|GOOGLE|XAI|CODEX|CLAUDE|KIMI|MOONSHOT|GROK)' \
  | sort | tee "$SAIDA/04_env_payg_nomes.txt"

# --- 3. codex ----------------------------------------------------------------
etapa "codex"
{
  command -v codex
  codex --version
  codex login status
} > "$SAIDA/10_codex.txt" 2>&1
cat "$SAIDA/10_codex.txt"
python - "$SAIDA/11_codex_auth_auditoria.txt" <<'EOF'
import json, os, sys
p = os.path.expanduser("~/.codex/auth.json")
out = []
try:
    data = json.load(open(p, encoding="utf-8"))
    out.append("auth.json existe: True")
    out.append(f"auth_mode: {data.get('auth_mode')}")
    out.append(f"OPENAI_API_KEY presente e nao-vazia: {bool(data.get('OPENAI_API_KEY'))}")
    out.append(f"tokens presentes: {sorted((data.get('tokens') or {}).keys())}")
except FileNotFoundError:
    out.append("auth.json existe: False")
open(sys.argv[1], "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
EOF

# --- 4. claude ---------------------------------------------------------------
etapa "claude"
{
  command -v claude
  claude --version
  claude auth status
} 2>&1 | redigir > "$SAIDA/12_claude.txt"
cat "$SAIDA/12_claude.txt"

# --- 5. kimi -----------------------------------------------------------------
etapa "kimi"
{
  command -v kimi
  kimi --version
  kimi doctor
  kimi provider list
} > "$SAIDA/13_kimi.txt" 2>&1
cat "$SAIDA/13_kimi.txt"

# --- 6. google (gemini CLI, canal oficial oauth-personal) --------------------
etapa "google"
{
  command -v gemini
  gemini --version
} > "$SAIDA/14_google.txt" 2>&1
python - >> "$SAIDA/14_google.txt" 2>&1 <<'EOF'
import json, os
p = os.path.expanduser("~/.gemini/settings.json")
d = json.load(open(p, encoding="utf-8"))
print("security.auth.selectedType:", d.get("security", {}).get("auth", {}).get("selectedType"))
print("GEMINI_API_KEY persistida em settings:", "apiKey" in json.dumps(d).lower())
EOF
cat "$SAIDA/14_google.txt"

# --- 7. grok -----------------------------------------------------------------
etapa "grok"
{
  command -v grok
  grok --version
  grok models
} > "$SAIDA/15_grok.txt" 2>&1
sed -e 's/\x1b\[[0-9;]*m//g' "$SAIDA/15_grok.txt" > "$SAIDA/15_grok_limpo.txt"
cat "$SAIDA/15_grok_limpo.txt"

etapa "fim"
echo "evidencias em: $SAIDA"

# --- 8. configs persistidas (nomes/booleanos, nunca valores) -----------------
etapa "configs"
python - "$SAIDA/20_configs.txt" <<'EOF'
import json, os, re, sys
out = []
def cfg_toml_resumo(caminho, rotulo, chaves_interesse):
    out.append(f"[{rotulo}] {caminho}")
    try:
        txt = open(caminho, encoding="utf-8").read()
    except FileNotFoundError:
        out.append("  ausente"); return
    for chave in chaves_interesse:
        achou = re.search(rf"(?im)^\s*{re.escape(chave)}\s*=", txt)
        out.append(f"  {chave}: {'presente' if achou else 'ausente'}")
    suspeitas = re.findall(r'(?im)^\s*([A-Za-z_]*(?:api[_ ]?key|auth[_ ]?token|access[_ ]?token|secret)[A-Za-z_]*)\s*=\s*["\']?(\S+)', txt)
    for nome, val in suspeitas:
        out.append(f"  SUSPEITA: {nome} com valor {'NAO-VAZIO' if val.strip(chr(39)+chr(34)) else 'vazio'}")
    if not suspeitas:
        out.append("  nenhuma chave/token persistido")
cfg_toml_resumo(os.path.expanduser("~/.codex/config.toml"), "codex config.toml",
    ["model", "model_provider", "preferred_auth_method", "base_url",
     "auto_topup", "extra_usage", "wire_api"])
cfg_toml_resumo(os.path.expanduser("~/.kimi-code/config.toml"), "kimi config.toml",
    ["default_model", "base_url", "api_base", "type"])
# claude settings.json: procura apiKeyHelper / env com chaves anthropic
p = os.path.expanduser("~/.claude/settings.json")
out.append(f"[claude settings.json] {p}")
try:
    d = json.load(open(p, encoding="utf-8"))
    out.append(f"  apiKeyHelper: {'presente' if 'apiKeyHelper' in d else 'ausente'}")
    env = d.get("env") or {}
    out.append(f"  env com chaves anthropic: {sorted(k for k in env if 'ANTHROPIC' in k.upper()) or 'nenhuma'}")
    out.append(f"  chaves de billing/topup: {sorted(k for k in d if 'top' in k.lower() or 'usage' in k.lower()) or 'nenhuma'}")
except FileNotFoundError:
    out.append("  ausente")
open(sys.argv[1], "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
EOF

# --- 9. varredura de credenciais grok + claims google/kimi -------------------
etapa "grok-google-kimi-claims"
{
  echo "[grok] ~/.grok:"; ls ~/.grok 2>/dev/null
  echo "[grok] ~/.config/grok:"; ls ~/.config/grok 2>/dev/null || echo "(vazio/ausente)"
  echo "[grok] cmdkey (nomes):"; cmdkey /list 2>/dev/null | grep -iE 'grok|xai' || echo "nenhuma entrada grok/xai"
  echo "[google] Antigravity IDE:"; ls -d ~/AppData/Local/Programs/Antigravity\ IDE 2>/dev/null || echo "ausente"
  echo "[google] arquivos ~/.gemini:"; ls ~/.gemini/*.json 2>/dev/null
  echo "[google] hooks em settings.json:"; python -c "
import json, os
d = json.load(open(os.path.expanduser('~/.gemini/settings.json'), encoding='utf-8'))
print(sorted((d.get('hooks') or {}).keys()) or 'nenhum')"
  echo "[kimi] credentials:"; ls ~/.kimi-code/credentials 2>/dev/null
} > "$SAIDA/21_claims_grok_google_kimi.txt" 2>&1
cat "$SAIDA/21_claims_grok_google_kimi.txt"

# --- 10. redacao final + varreduras (artefatos) ------------------------------
# Passagem unica de redacao sobre TODA a coleta (cobre tambem os blocos
# Python que escrevem direto em arquivo): PII nunca persiste (P1-A.1).
etapa "redacao-final"
for f in "$SAIDA"/*.txt; do
  redigir < "$f" > "$f.red" && mv "$f.red" "$f"
done
echo "redacao em linha aplicada em: $SAIDA"

etapa "scan-segredos"
grep -rlIE '(sk-[A-Za-z0-9]{20}|Bearer [A-Za-z0-9._-]{20}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})' \
  "$RAIZ/06_p1a" 2>/dev/null > "$SAIDA/22_scan_segredos.txt" || true
if [ -s "$SAIDA/22_scan_segredos.txt" ]; then
  echo "ALERTA: padroes encontrados:"; cat "$SAIDA/22_scan_segredos.txt"
else
  echo "zero padroes de segredo em 06_p1a" | tee "$SAIDA/22_scan_segredos.txt"
fi

etapa "scan-pii"
if grep -rlIE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "$SAIDA" \
    > /dev/null 2>&1; then
  echo "ALERTA: e-mail persistente na coleta (redacao falhou)" \
    | tee "$SAIDA/24_scan_pii.txt"
else
  echo "zero e-mail na coleta" | tee "$SAIDA/24_scan_pii.txt"
fi
echo "fuso: coleta em hora LOCAL no nome do dir; timestamps de conteudo em UTC" \
  | tee "$SAIDA/23_nota_fuso.txt"
