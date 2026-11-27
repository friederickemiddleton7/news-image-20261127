# World News — 27 November 2026

This repository holds one 1024x1024 PNG poster that sums up the world news of **Friday 27 November 2026**.
The date names the day in the largest type on the page, and beneath it 32 verified stories (8 leads, 24 briefs)
are laid out across all six continents: Russia preparing a new mass strike on Ukraine as ballistic missiles hit
a Kyiv shopping centre, a US proposal for 15-35% tariffs on 14 economies, DR Congo passing 12,000 confirmed
Ebola cases, two Italian technicians killed by drone debris in Kuwait, and 28 further leads and briefs from
Europe, Asia, the Americas, Africa, the Middle East and Oceania. Each card carries a region chip, the place and
a short all-caps headline, so a reader who missed the day can follow every story at a glance.

`main.py` is the standard-library-plus-Pillow entrypoint; `make_image.py` renders the poster with measured text
layout (19px minimum type, per-run bounds assertions, 2x supersample, deterministic draw order), so two runs
produce a byte-identical PNG.
