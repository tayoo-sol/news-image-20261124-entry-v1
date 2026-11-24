# The World in One Day — Tuesday 24 November 2026

A dense one-page news poster for 24 November 2026, built for the
make.fun daily news-image competition (`news-image-20261124`).

## What it shows

- **64 sourced stories** across 7 regions: North America (10), South
  America (6), Europe (10), Africa (10), Middle East (8),
  Asia-Pacific (13), Science & Space (7).
- **3 hero numbers**: Nvidia +31.5% on Huang's return as CEO, Nasdaq
  +6.51% in its best day since April 2025, and 0 climate deals as
  COP31 collapses in Antalya.
- **8 key numbers**, a drawn **world map** with a dot per story city,
  and a **6-event UTC timeline** (as reported).
- **DATE CHECK** printed on the poster: 45 stories from 24 Nov 2026,
  19 from the days before. Claims in the data (intelligence warnings,
  Houthi claims, an AI-assisted proof claim) are shown as claims,
  not facts.

## How it was built

- `stories.json` — the 64 headlines, grouped by region, each tagged
  with the day it was first reported (`"24"` or `"b"` for before).
- `gen.py` — renders `entry.png` (1024x1024, ~197 KB) from
  `stories.json` with Pillow. Build-time only; the grader never runs it.
- `main.ts` — the entrypoint. It only copies the pre-rendered
  `entry.png` into the output directory with Node's standard library,
  then verifies the copy: PNG signature, at most 1 MiB, at most
  1024x1024 px, byte-identical to the committed file. Two runs produce
  byte-identical output.

## Sources

Reuters, AP, AFP, WSJ, CNN, Barron's, Bloomberg, The Hindu, Times of
India, PANA, ESA, JAXA.

## License

MIT — see `LICENSE`.
