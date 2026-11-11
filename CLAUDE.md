# Canal de curiosidades — manual de produção

Canal do Pedro ("Zaka"). Shorts animados de **histórias reais** (história/ciência), em **português do Brasil**, para público **brasileiro**, postados no TikTok (Creator Rewards) e YouTube Shorts. Tudo para o Pedro (mensagens, roteiro, legendas) em português.

## Formato (obrigatório)
- 1080x1920, 30 fps, **65–85 s** (TikTok só monetiza vídeo com mais de 1 minuto). Renderizar no tamanho final, nunca cortar/upscale do vídeo final.
- Uma história verdadeira por vídeo. Linha 1 = gancho; virada por volta dos 60% ("Mas aí vem a reviravolta…"); última linha fecha o gancho (loop).
- Corte novo a cada ideia do roteiro (~2–3 s). Câmera só com push-in/dolly com motivo.
- Legenda na tela: 1–2 palavras por vez, Poppins Bold branca com contorno, palavras-chave em amarelo (adicionar as do episódio com `gfx.KEYWORDS |= {...}` em minúsculas, com acento), **centralizada** (y=1370). Nunca cobrir rosto de personagem: a cabeça (centro em `pés - 505*s`, raio `165*s`) tem que terminar acima de y≈1290.
- Datas/nomes principais centralizados no topo (`date_stamp`, `banner`), em português (ex.: "14 DE ABRIL DE 1912").

## Estilo visual (aprovado pelo Pedro no EP01 v2)
**2D + 3D nos mesmos objetos:**
- Cenários e objetos (navios, prédios, objetos-chave da história) = **3D no Blender** (Cycles CPU), céu transparente, renderizados como "placas" (stills) + **contorno de nanquim tremido** gerado por `kit/ink.py` a partir de passes de normal e ID.
- Céu, raios de luz, partículas, chuva, explosões = 2D em skia (`kit/gfx.py`).
- Personagens = **2D próprios** (`kit/toon2.py`): cabeça branca redonda, traço tremido de caneta, corpo cápsula, braços/pernas de palito, expressões exageradas (grin, shock, joy, worried, determined, sad), luz de 3D na cabeça.
- **Nunca** copiar personagens, cenários ou roteiros de outros canais (ex.: Ricks Clips). Mesma linguagem visual, criações originais.
- Proibido: título centralizado em gradiente, tudo com fade-in, whoosh em todo corte, número/afirmação na tela que não esteja em sources.md.

## Setup (sessão nova)
```bash
bash setup.sh            # skia, kokoro (voz), bpy/Blender 5 em .venv-bl, modelos de voz em models/
```

## Pipeline de um episódio (pasta de trabalho fora do repo, ex. /home/claude/work/epNN)
1. **Tema**: sortear em `themes.md` (RESTANTES; itens marcados PRIORIDADE vêm primeiro). Pesquisar na web e confirmar fatos com 2+ fontes.
2. **Roteiro**: `episodes/epNN/script.md` em tabela `| # | Narração (PT-BR) | Nota |` (ver `episodes/ep01/script_pt.md`), **190–220 palavras**, português falado, natural e brasileiro (nada de tradução literal), frases curtas. Números podem ficar em dígitos (a voz lê). `sources.md` com fonte para cada afirmação.
3. **Narração** (voz fixa do canal: Kokoro `pm_alex`, velocidade 1.05, pt-br):
   `python3 -I kit/narrate.py models episodes/epNN/script.md <work> pm_alex 1.05` → `narration.wav` + `timings.json`. Conferir duração 65–85 s; ajustar o roteiro se precisar.
4. **Plano de cenas**: uma cena por ideia, reaproveitar 3–6 cenários. Definir placas 3D (cenário fixo) e camadas 3D (objetos que se movem, renderizados com o mar/chão como holdout e animados em 2D).
5. **Placas 3D**: criar `episodes/epNN/plates.py` a partir de `kit/bl_scenes.py` (helpers: `mat`, `win_mat`, `box`, `cyl`, `sea`, `mood`, `camera`, `holdout`, `render`; criar assets novos do tema). Prévia rápida com `BL_PCT=22 BL_SAMPLES=8` + `kit/prevsheet.py`, olhar a folha, corrigir enquadramentos; render final:
   `bash kit/render_all.sh <work> episodes/epNN/plates.py placa1 placa2 ...` (~40 s por placa a 75%).
6. **Composição**: `episodes/epNN/render.py` a partir de `episodes/ep01/render_pt.py` (funções de cena por shot, `add(início, fim, cena)` amarrado às palavras faladas via `ws(linha, "palavra")` — palavras em português). Prévia: `kit/stills_v2.py` (adaptar import) → folha de stills; corrigir os 3 piores problemas; repetir.
7. **Som**: adaptar `episodes/ep01/sfx_pt.py` (drone + impactos nas palavras de ação + chime final), mixar: `amix` + `loudnorm=I=-14:TP=-1.5`.
8. **Render final** em 2 processos paralelos (metade dos frames cada), concat, mux áudio AAC 192k, `-movflags +faststart`.
9. **Revisão obrigatória antes de entregar**: contact sheet 1 fps; `ffprobe` (1080x1920, 30/1, duração 60+ s); conferir cada fato da tela contra sources.md; legenda nunca em cima de rosto; ouvir se a pronúncia de nomes estrangeiros ficou aceitável (se não, escrever foneticamente no roteiro).
10. **Entrega ao Pedro** (SendUserFile + mensagem curta em português):
    - o .mp4;
    - **a capa pronta (PNG 1080x1920), SEMPRE**: `python3 -I kit/cover.py episodes/epNN/render.py <work>/timings.json <work>/plates <segundo> "LINHA 1|LINHA 2" episodes/epNN/cover.png "PALAVRAS,AMARELAS"` — frame forte (personagem + objeto principal) + título curto em português de 3–6 palavras que gere curiosidade (ver `episodes/ep01/cover_pt.png`); conferir antes de enviar;
    - **melhor horário para postar** (ver abaixo) com o porquê em 1 linha;
    - legenda do post em português (1 linha com pergunta para gerar comentário) + 3–5 hashtags (#curiosidades #historia #vocesabia + 1–2 do tema);
    - o roteiro;
    - lembrete: ativar o rótulo "conteúdo gerado por IA" (voz sintética) ao postar;
    - se restarem ≤4 temas em themes.md, avisar para mandar mais.
11. **Salvar no repo**: commitar `episodes/epNN/` (script.md, sources.md, timings.json, plates.py, render.py, sfx.py, cover.png, contact sheet PNG — **sem** vídeos/áudios/placas) + `themes.md` atualizado, push na `main`.

## Horários de postagem (público Brasil, horário de Brasília)
- **Segunda a sexta: 12h e 20h** (almoço e início da noite, os maiores picos de uso no Brasil).
- **Sábado e domingo: 11h e 19h.**
- Entregar o vídeo antes do horário.
- Conta: nome **Sério Isso?** (@serioisso.historia), bio em português, foto de perfil = personagem do canal (episodes/ep01/profile.png).

## Regras
- Só fatos verificáveis; na dúvida, tirar do roteiro.
- Nunca postar nada na conta do Pedro; ele mesmo posta.
- Nunca usar voz clonada de pessoa real; voz fixa do canal = `pm_alex`.
