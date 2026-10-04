# Layout Green Smile aprovado

Este e o layout aprovado em 03/10/2026. Todas as entradas de geracao devem produzir
a mesma montagem. `src/xray_mouth/report.py` e a unica implementacao; o BAT,
`gerar_relatorio.py` e `xray-mouth report` usam esse modulo.

## Quadro e imagens

O quadro mede **1672 x 941 pixels**, com fundo preto. O cabecalho tem 138 pixels de altura.
As coordenadas abaixo sao medidas a partir do canto superior esquerdo, em pixels.

| Arquivo | x | y | Largura | Altura |
| --- | ---: | ---: | ---: | ---: |
| 01 | 174 | 145 | 240 | 176 |
| 02 | 174 | 337 | 240 | 178 |
| 03 | 498 | 262 | 186 | 241 |
| 04 | 735 | 262 | 186 | 241 |
| 05 | 975 | 262 | 185 | 241 |
| 06 | 1192 | 145 | 242 | 176 |
| 07 | 1192 | 337 | 242 | 178 |
| 08 | 174 | 532 | 240 | 178 |
| 09 | 174 | 725 | 240 | 175 |
| 10 | 498 | 591 | 186 | 241 |
| 11 | 735 | 591 | 186 | 241 |
| 12 | 975 | 591 | 185 | 241 |
| 13 | 1192 | 532 | 242 | 178 |
| 14 | 1192 | 725 | 242 | 175 |

Os cantos tem raio de 42 pixels. As imagens usam `object-fit: cover`, centralizacao
e escala de cinza, como no resultado aprovado. A exibicao pode recortar as bordas
para preencher cada quadro; os arquivos originais permanecem intactos.

## Cabecalho

`assets/green_smile_reference_header.png` e a arte aprovada, sem os dados do paciente
da referencia. Ela integra o pacote instalado. A antiga logo isolada nao e usada
na montagem atual.

A identificacao comeca em x=580, y=23. Fonte Arial/Helvetica, 24 pixels, peso 700,
entrelinha de 29 pixels; rotulos brancos e valores `#ff6200`.
As linhas sao `Paciente`, `Data` e `Dr`. O paciente vem da pasta e a data da geracao
no fuso UTC-3. O profissional padrao e Victor Greenhalgh, configuravel por
`XRAY_MOUTH_DOCTOR`.

## Saida e verificacao

O PNG mede 1672 x 941. O PDF tem uma pagina de 1254 x 705,75 pontos, equivalente
ao quadro a 96 dpi, sem margens. O HTML inclui as imagens e a arte em data URIs.

Os testes fixam todas as coordenadas e a integridade da arte, verificam a renderizacao
com imagens sinteticas, os cantos pretos, as cores de cada posicao e o tamanho do PDF.
Nenhuma radiografia real e necessaria para executar os testes ou a CI.

```powershell
.venv\Scripts\python.exe -m playwright install chromium
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m build
```

O conteudo das radiografias e da identificacao varia por paciente. O layout permanece
o mesmo. A reproducao pixel a pixel exige as mesmas entradas e fontes. O Playwright
esta fixado na versao 1.63.0, usada para produzir o resultado aprovado, mantendo a
versao correspondente do Chromium nas novas instalacoes.
