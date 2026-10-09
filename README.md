# Sequencia de Notas com Playwright

Esta pasta e uma versao independente do robô usando Playwright para Python.
O projeto antigo usa Selenium/undetected-chromedriver e possui conflitos de
merge e caminhos absolutos; ele nao foi alterado.

## Preparacao

1. Crie o ambiente Python a partir de `pyproject.toml` ou `requirements.txt`.
2. Instale o navegador:

   ```powershell
   python -m pip install -r requirements.txt
   python -m playwright install chromium
   ```

3. Copie `.env.exemplo` para `.env` e `params.example.json` para `params.json`.
   Preencha as credenciais sem versionar esses arquivos.
4. Configure as credenciais Oracle e `ANTI_CAPTCHA_TOKEN` no `.env`.

## Docker

A imagem usa `/app` como diretório de trabalho e inicia o robô
automaticamente. O `.env` e o `params.json` não são incluídos na imagem.
Coloque os dois arquivos em uma mesma pasta no host e monte essa pasta em
`/config`:

```powershell
cd C:\scripts_python\SequenciadeNotas\sequenciaNotasPW
docker build -f dockerfile -t hiannyurt/pw_sequencia_notas:latest .
docker run --rm  -v "C:\scripts_python\SequenciadeNotas\sequenciaNotasPW\.env:/config/.env:ro" -v "C:\scripts_python\SequenciadeNotas\sequenciaNotasPW\imparqsefaz:/app/imparqsefaz/:rw"  -v "C:\scripts_python\SequenciadeNotas\SequenciaNotas\parametros_contabilista\params.json:/config/params.json:ro" -v "C:\scripts_python\SequenciadeNotas\sequenciaNotasPW\data\log:/app/data/log:rw" hiannyurt/pw_sequencia_notas:latest
 
```

A pasta `config` deve conter `.env` e `params.json`. O diretório padrão do
container é `/app`. Os arquivos de configuração são lidos de `/config`, e os
diretórios `data/download`, `data/csv`, `data/captcha` e `data/log` ficam
dentro do container e são apagados quando ele é removido.

## Execucao

```powershell
cd C:\scripts_python\SequenciadeNotas\sequenciaNotasPW
python -m sequencanotas_pw.main
```

Também é possível executar diretamente:

```powershell
python C:\scripts_python\SequenciadeNotas\sequenciaNotasPW\sequencanotas_pw\main.py
```

Para acompanhar o navegador, defina `SEQUENCIA_NOTAS_HEADLESS=false`.
Os arquivos sao gravados em `data/download`, convertidos para
`data/csv` e, quando configurado, copiados para
`SEQUENCIA_NOTAS_PRODUCAO`.

O fluxo usa uma única sessão/contexto Playwright, abre uma página isolada por
CNPJ e fecha a página ao terminar. Isso elimina a troca manual de abas e reduz
esperas fixas do Selenium. O captcha continua dependendo do Anti-Captcha,
quando o portal o apresenta.
