# XRay Mouth

Versao **0.2.0** — layout Green Smile aprovado em 03/10/2026.

Gerador local de montagem radiografica Green Smile para series periapicais.

O projeto recebe pastas de pacientes com 14 radiografias numeradas, monta um quadro clinico
por paciente com medidas controladas pixel a pixel e gera PDF, previa PNG, HTML e relatorio
textual. Todo o processamento acontece localmente; nenhuma imagem e enviada para servicos
externos.

> Ferramenta experimental e nao diagnostica. Nao substitui avaliacao odontologica profissional.

## Resultado visual

- Quadro horizontal de 1672 x 941 pixels sobre fundo preto, conforme a referencia.
- Quatro radiografias horizontais em cada lateral, com aproximadamente 240 x 177 pixels.
- Tres radiografias verticais na regiao superior central e tres na inferior central,
  com aproximadamente 186 x 241 pixels e cantos arredondados.
- Cabecalho grafico Green Smile extraido da referencia, sem a identificacao do paciente.
- Identificacao com rotulos brancos e valores laranja. O nome vem da pasta do paciente;
  a data e a da geracao. O profissional padrao e Victor Greenhalgh e pode ser definido
  pela variavel de ambiente `XRAY_MOUTH_DOCTOR`.
- PDF com o mesmo layout exibido na previa.
- Nenhum dado de paciente da imagem de referencia foi incorporado ao repositorio.

## Uso facil no Windows

O exemplo anonimizado e autorizado em `xray/Caso_Anonimo/` continua disponivel
para testar. A geracao processa cada pasta de paciente separadamente.

1. Baixe ou clone o repositorio.
2. Dentro de `xray`, crie uma subpasta com o nome de cada paciente.
3. Coloque as 14 imagens do paciente nessa subpasta e nomeie-as com prefixos de `01_` ate `14_`.
4. Execute `executar_relatorio.bat`.

```text
xray/
├── Francisco Bispo De Souza/
│   ├── 01_radiografia.jpg
│   ├── ...
│   └── 14_radiografia.jpg
└── Maria Silva/
    ├── 01_radiografia.jpg
    ├── ...
    └── 14_radiografia.jpg
```

O BAT:

- detecta e recria uma `.venv` copiada de outro computador;
- procura Python 3.11 ou superior;
- tenta instalar Python 3.12 pelo `winget` quando necessario;
- instala as dependencias na `.venv` local;
- instala o Chromium usado pelo Playwright;
- gera o relatorio e abre o PDF.

A primeira execucao precisa de acesso a internet. Nao copie a pasta `.venv` entre computadores.

O layout aprovado e unico: o BAT e o comando instalado usam o mesmo gerador.
Tambem e possivel executar na pasta do projeto:

```powershell
.venv\Scripts\xray-mouth.exe report .
```

Para gerar sem abrir janelas, acrescente `--no-open`. Consulte [o contrato do layout](docs/LAYOUT.md)
para as coordenadas exatas, a ordem dos arquivos e os criterios de verificacao.

## Posicoes das 14 imagens

A montagem usa os seguintes grupos:

- lateral esquerda: `01`, `02`, `08`, `09`;
- centro superior: `03`, `04`, `05`;
- centro inferior: `10`, `11`, `12`;
- lateral direita: `06`, `07`, `13`, `14`.

A atribuicao continua sendo feita exclusivamente pelo prefixo do nome do arquivo. O programa
nao tenta identificar dentes ou regioes anatomicas a partir dos pixels.

Use a ordem anatomica de nomes descrita em [xray/README.md](xray/README.md).

## Saida

Cada execucao cria uma pasta datada por paciente em `relatorio`, usando o nome da subpasta,
contendo:

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
.venv\Scripts\python.exe -m build
```

O projeto tambem preserva os utilitarios existentes de inspecao de datasets e desidentificacao
DICOM. Consulte `src/xray_mouth` para esses modulos.

## Privacidade

- Nao inclua radiografias reais no Git.
- Nao inclua dados identificaveis de pacientes no repositorio.
- Os arquivos de entrada nunca sao modificados.
- O processamento do relatorio ocorre no computador local.

Licenca MIT. Consulte [LICENSE](LICENSE).
