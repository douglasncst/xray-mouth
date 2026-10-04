# Pasta de entrada

`Caso_Anonimo/` e o exemplo anonimizado e autorizado que ja integra o repositorio.
Novas pastas de pacientes sao locais e ignoradas pelo Git por padrao.

Crie aqui uma subpasta para cada paciente. O nome da pasta sera usado como nome do paciente
no relatorio. Dentro de cada subpasta, coloque 14 radiografias com nomes iniciados por `01_`
ate `14_`.

Exemplo:

```text
xray/
└── Francisco Bispo De Souza/
    ├── 01_radiografia.jpg
    ├── 02_radiografia.jpg
    ├── ...
    └── 14_radiografia.jpg
```

Radiografias reais e dados de pacientes nao devem ser enviados ao GitHub.

## Ordem obrigatoria

| Prefixo | Regiao | Posicao na montagem |
| --- | --- | --- |
| 01 | Superior direita, molares | Esquerda, primeira |
| 02 | Superior direita, pre-molares | Esquerda, segunda |
| 03 | Superior direita, canino | Centro superior, esquerda |
| 04 | Superior, incisivos | Centro superior, meio |
| 05 | Superior esquerda, canino | Centro superior, direita |
| 06 | Superior esquerda, pre-molares | Direita, primeira |
| 07 | Superior esquerda, molares | Direita, segunda |
| 08 | Inferior direita, molares | Esquerda, terceira |
| 09 | Inferior direita, pre-molares | Esquerda, quarta |
| 10 | Inferior direita, canino | Centro inferior, esquerda |
| 11 | Inferior, incisivos | Centro inferior, meio |
| 12 | Inferior esquerda, canino | Centro inferior, direita |
| 13 | Inferior esquerda, pre-molares | Direita, terceira |
| 14 | Inferior esquerda, molares | Direita, quarta |

O programa nao gira imagens automaticamente. Confira a orientacao antes de gerar.
