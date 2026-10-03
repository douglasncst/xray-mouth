# XRay Mouth

Gerador local de montagem radiografica Green Smile para series periapicais.

O projeto recebe 16 radiografias numeradas, monta o quadro clinico com medidas controladas
pixel a pixel e gera PDF, previa PNG, HTML e relatorio textual. Todo o processamento acontece
localmente; nenhuma imagem e enviada para servicos externos.

> Ferramenta experimental e nao diagnostica. Nao substitui avaliacao odontologica profissional.

## Resultado visual

- Quadro fixo de 1672 x 958 pixels.
- Oito molduras laterais de 280 x 180 pixels.
- Oito molduras centrais de 185 x 270 pixels.
- Logo Green Smile com proporcao preservada.
- Cabecalho com paciente, exame e data.
- PDF com o mesmo layout exibido na previa.

## Uso facil no Windows

1. Baixe ou clone o repositorio.
2. Coloque as 16 imagens na pasta `xray`.
3. Nomeie os arquivos com prefixos de `01_` ate `16_`.
4. Execute `executar_relatorio.bat`.

O BAT:

- detecta e recria uma `.venv` copiada de outro computador;
- procura Python 3.11 ou superior;
- tenta instalar Python 3.12 pelo `winget` quando necessario;
- instala as dependencias na `.venv` local;
- instala o Chromium usado pelo Playwright;
- gera o relatorio e abre o PDF.

A primeira execucao precisa de acesso a internet. Nao copie a pasta `.venv` entre computadores.

## Saida

Cada execucao cria uma pasta datada em `relatorio` contendo:

- `periapical_series.pdf`
- `periapical_series_preview.png`
- `montagem.html`
- `report.txt`

## Desenvolvimento

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m playwright install chromium
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
```

O projeto tambem preserva os utilitarios existentes de inspecao de datasets e desidentificacao
DICOM. Consulte `src/xray_mouth` para esses modulos.

## Privacidade

- Nao inclua radiografias reais no Git.
- Nao inclua dados identificaveis de pacientes no repositorio.
- Os arquivos de entrada nunca sao modificados.
- O processamento do relatorio ocorre no computador local.

Licenca MIT. Consulte [LICENSE](LICENSE).
