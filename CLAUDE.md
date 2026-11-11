# Canal de curiosidades — manual de produção

Canal do Pedro ("Zaka"). Shorts animados de **histórias reais** (história/ciência), em **inglês**, para público dos **EUA**, postados no TikTok (Creator Rewards) e YouTube Shorts.
O Pedro não é fluente em inglês: tudo que for para ele ler vai em **português**, e o roteiro sempre com tradução linha a linha.

## Formato (obrigatório)
- 1080x1920, 30 fps, **65–85 s** (TikTok só monetiza vídeo com mais de 1 minuto). Renderizar no tamanho final, nunca cortar/upscale do vídeo final.
- Uma história verdadeira por vídeo. Linha 1 = gancho; virada por volta dos 60%; última linha fecha o gancho (loop).
- Corte novo a cada ideia do roteiro (~2–3 s). Câmera só com push-in/dolly com motivo.
- Legenda: 1–2 palavras por vez, Poppins Bold branca com contorno, palavras-chave em amarelo, **centralizada** (y=1370). Nunca cobrir rosto de personagem: a cabeça (centro em `pés - 505*s`, raio `165*s`) tem que terminar acima de y≈1290.
- Datas/nomes principais centralizados no topo (`date_stamp`, `banner`).

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
1. **Tema**: sortear em `themes.md` (RESTANTES). Pesquisar na web e confirmar fatos com 2+ fontes.
2. **Roteiro**: `episodes/epNN/script.md` no formato de tabela `| # | EN | PT |` (ver EP01), **200–230 palavras**, frases curtas faladas. `sources.md` com fonte para cada afirmação.
3. **Narração** (voz fixa do canal: Kokoro `am_michael`, velocidade 0.98):
   `python3 -I kit/narrate.py models episodes/epNN/script.md <work> am_michael 0.98` → `narration.wav` + `timings.json` (tempo por linha/palavra). Conferir duração 65–85 s; se curto, alongar o roteiro.
4. **Plano de cenas**: uma cena por ideia, reaproveitar 3–6 cenários. Definir quais placas 3D (cenário fixo) e quais camadas 3D (objetos que se movem, renderizados com o mar/chão como holdout e animados em 2D).
5. **Placas 3D**: criar `episodes/epNN/plates.py` a partir de `kit/bl_scenes.py` (reaproveitar helpers: `mat`, `win_mat`, `box`, `cyl`, `sea`, `mood`, `camera`, `holdout`, `render`; criar assets novos do tema). Prévia rápida de todas as placas com `BL_PCT=22 BL_SAMPLES=8` + `kit/prevsheet.py`, olhar a folha, corrigir enquadramentos; depois render final:
   `bash kit/render_all.sh <work> episodes/epNN/plates.py placa1 placa2 ...` (~40 s por placa a 75%).
6. **Composição**: `episodes/epNN/render.py` a partir de `kit/render_ep01_v2.py` (funções de cena por shot, `add(início, fim, cena)` amarrado aos tempos das palavras via `ws(linha, palavra)`). Prévia: `kit/stills_v2.py` (adaptar import) → folha de stills; corrigir os 3 piores problemas; repetir.
7. **Som**: adaptar `kit/sfx_ep01.py` (drone ambiente + impactos nos frames de ação + chime final), mixar com a narração: `amix` + `loudnorm=I=-14:TP=-1.5`.
8. **Render final** em 2 processos paralelos (metade dos frames cada), concat, mux áudio AAC 192k, `-movflags +faststart`.
9. **Revisão obrigatória antes de entregar**: contact sheet 1 fps; `ffprobe` (1080x1920, 30/1, duração 60+ s); conferir cada fato da tela contra sources.md; legenda nunca em cima de rosto.
10. **Entrega ao Pedro** (SendUserFile + mensagem em português, curta):
    - o .mp4;
    - legenda do post em inglês (1 linha com pergunta para gerar comentário) + 3–5 hashtags (#history #historyfacts #didyouknow + 1–2 do tema);
    - sugestão de capa (frame + texto curto em inglês);
    - o roteiro com tradução PT;
    - lembrete: ativar o rótulo "conteúdo gerado por IA" (voz sintética) ao postar;
    - se restarem ≤4 temas em themes.md, avisar para mandar mais.
11. **Salvar no repo**: commitar `episodes/epNN/` (script.md, sources.md, timings.json, plates.py, render.py, contact sheet PNG — **sem** vídeos/áudios/placas, são grandes) + `themes.md` atualizado, push na `main`.

## Horários de postagem (público EUA, horário de Brasília)
- **9h** e **22h** (7h e 20h em Nova York, de novembro a março). Quando os EUA entrarem no horário de verão (março), passa para **8h e 21h**.
- Entregar o vídeo antes do horário de postagem.

## Regras
- Só fatos verificáveis; na dúvida, tirar do roteiro.
- Nunca postar nada na conta do Pedro; ele mesmo posta.
- Nunca usar voz clonada de pessoa real; voz fixa do canal = `am_michael`.
