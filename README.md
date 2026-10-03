# XRay Mouth

Gerador local de montagem radiografica Green Smile para series periapicais.

O projeto recebe 14 radiografias numeradas, monta o quadro clinico com medidas controladas
pixel a pixel e gera PDF, previa PNG, HTML e relatorio textual. Todo o processamento acontece
localmente; nenhuma imagem e enviada para servicos externos.

> Ferramenta experimental e nao diagnostica. Nao substitui avaliacao odontologica profissional.

## Resultado visual

- Quadro fixo de 1600 x 1278 pixels sobre fundo preto.
- Quatro radiografias horizontais em cada lateral, com 252 x 190 pixels.
- Tres radiografias verticais na regiao superior central e tres na inferior central,
  com 190 x 253 pixels.
- Distribuicao inspirada no novo modelo clinico de referencia enviado para o projeto.
- Logo Green Smile no topo esquerdo e identificacao do exame em branco sobre o fundo preto.
- PDF com o mesmo layout exibido na previa.
- Nenhum dado de paciente da imagem de referencia foi incorporado ao repositorio.

## Uso facil no Windows

1. Baixe ou clone o repositorio.
2. Coloque as 14 imagens na pasta `xray`.
3. Nomeie os arquivos com prefixos de `01_` ate `14_`.
4. Execute `executar_relatorio.bat`.

O BAT:

- detecta e recria uma `.venv` copiada de outro computador;
- procura Python 3.11 ou superior;
- tenta instalar Python 3.12 pelo `winget` quando necessario;
- instala as dependencias na `.venv` local;
- instala o Chromium usado pelo Playwright;
- gera o relatorio e abre o PDF.

A primeira execucao precisa de acesso a internet. Nao copie a pasta `.venv` entre computadores.

## Posicoes das 14 imagens

A montagem usa os seguintes grupos:

- lateral esquerda: `01`, `06`, `07`, `10`;
- centro superior: `02`, `03`, `04`;
- centro inferior: `11`, `12`, `13`;
- lateral direita: `05`, `08`, `09`, `14`.

A atribuicao continua sendo feita exclusivamente pelo prefixo do nome do arquivo. O programa
nao tenta identificar dentes ou regioes anatomicas a partir dos pixels.

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
