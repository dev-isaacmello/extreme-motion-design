# Direção: como um estúdio decide antes de animar

Motion bom é design bom que se move com motivo. Esta referência cobre as decisões que vêm antes do código e os sinais que denunciam trabalho amador ou gerado.

## Ordem de produção

1. **Styleframes**: 3 a 5 quadros estáticos (abertura, um por ideia principal, fecho). Renderize com `stills.cjs --times` e olhe. Cada um tem de funcionar como pôster: hierarquia, uma cor de acento, respiro. Se o quadro parado é fraco, animar não salva.
2. **Animatic**: as cenas como blocos estáticos, já com a duração da partitura e o áudio. Rode `lint.py` aqui: é quando o ritmo ainda é barato de mudar.
3. **Animação**: movimento primário de cada cena, depois secundário, depois ambiente.
4. **Polimento**: curvas, holds, SFX nos pontos de impacto, grão. Só depois de o animatic passar.

## Estrutura de batidas

| Formato | Estrutura |
|---|---|
| Vertical curto (até 30 s) | gancho em 0 a 2 s, prova em 2 a 20 s, uma mudança visual relevante a cada 2 a 4 s, fecho com ação em 3 a 5 s; o último frame emenda no primeiro se a peça for loop |
| Explainer (30 a 90 s) | problema, virada, como funciona em até 3 passos, resultado, chamada |
| Produto ou lançamento | uma promessa, 3 recursos com um quadro herói cada, marca e chamada |
| Logo sting (2 a 5 s) | construção, resolução no impacto do áudio, hold, assinatura |

- **Gancho**: no frame 0 já existe algo em movimento e a promessa está legível em até 2 s. Nada de fade vindo do preto nem logo na abertura.
- **Contraste de ritmo**: alterne rápido e lento. Use pelo menos duas classes de duração na peça (por exemplo 8 e 24 frames) e deixe a cena mais lenta durar cerca de 3x a mais rápida.
- **Hold**: depois de cada chegada, 12 a 24 frames em que só o ambiente se mexe. É no hold que a pessoa lê.

## Funcionar sem som

Assuma que parte do público vê no celular com o som desligado. Regras:

- A mensagem inteira se entende mudo. Cada frase narrada que carrega informação tem uma palavra-chave ou número na tela.
- Texto com tempo de leitura (regra de 1,5 s mais 0,3 s por palavra do SKILL.md).
- Se o usuário escolheu sem voz, a tipografia é a narração: escreva o texto de tela como roteiro, uma ideia por cena.

## Som como estrutura

- Marque os pontos de impacto do áudio antes de animar: início de frase, batida forte (`beats.py`), clímax. O keyframe de chegada cai neles.
- SFX no frame do contato ou 1 frame antes; whoosh começa 0,25 s antes do corte.
- Um SFX por evento com significado. `lint.py` acusa dois eventos a menos de 0,12 s.
- Silêncio de 2 a 4 frames antes de um corte seco aumenta o impacto.

## Sinais de amador ou de gerado, com teste

| Sinal | Como detectar |
|---|---|
| Curva linear ou padrão em tudo | `interpolate(` sem `easing`; `lint.py` avisa curva criada fora dos tokens |
| Tudo entra com fade e sobe | `lint.py` compara usos de `opacity` com transform, máscara e traço |
| Tudo entra no mesmo frame | mais de 3 elementos com o mesmo frame inicial e sem cascata |
| Tudo termina no mesmo frame | nenhuma sobreposição de 1 a 3 frames entre os finais |
| Mesma duração em tudo | menos de 3 durações distintas nas cenas; `lint.py` avisa cenas de mesma duração |
| Movimento sem pausa | `qa.py --timeline`: cena com respiro abaixo de 0,25 s |
| Quadro morto | `qa.py`: trecho parado acima de 1,5 s (faltou ambiente) |
| Olho pula no corte | compare na folha de contato o foco do fim de A com o do início de B |
| Câmera e objeto no mesmo eixo | leia a cena: `<Camera x>` e `translateX` do filho na mesma janela |
| Movimento rápido sem blur nem smear | deslocamento acima de 3% da largura por frame sem `smear`, `<Echo>` ou motion blur |
| Oscilação de vários ciclos | `Easing.bounce` ou `Easing.elastic`: `lint.py` reprova |
| Número que treme | contador sem `tabular-nums` |
| Escala sempre do centro | `transformOrigin` nunca definido |
| Efeito em excesso | aberração acima de 3 px, grão acima de 10%, glow em mais de um elemento |
| Gradiente roxo e azul, vidro fosco, glow padrão | revisão do styleframe; não há medida confiável |

Os limiares desta tabela são heurística de prática, não norma. Os testes automáticos saem como aviso, e quem decide é a revisão da folha de contato.
