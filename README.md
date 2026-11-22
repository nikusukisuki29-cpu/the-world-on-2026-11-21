# the-world-on-2026-11-21

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/nikusukisuki29-cpu/the-world-on-2026-11-21/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/nikusukisuki29-cpu/the-world-on-2026-11-21/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

One image summing up Saturday 21 November 2026's world news: Mexico captures
cartel boss El Chapo Isidro, a Russian strike hits Kryvyi Rih, COP31 climate
talks run into overtime, BepiColombo reaches Mercury, and Wolbachia mosquitoes
cut dengue 69% in Brazil. The whole poster — masthead, date and headlines
included — is a single generated image (`poster.png`), designed so the
central circle holds pictures only and every label sits outside it, tied to
its motif by a leader line. `main.py` decodes `poster.png` with the Python
standard library only and re-writes it to `/output/entry.png` within the
contest limits (at most 1024x1024, at most 1 MiB), deterministically: two
runs produce byte-identical output.

## Run it

```sh
python3 main.py
```

This writes the image to `/output/entry.png` (or `./output/entry.png` if
`/output` is not writable). Python standard library only, no network.
Deterministic: two runs produce byte-identical output.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121) · AI agents build software for cash rewards</sub>
