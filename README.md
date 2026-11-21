# VELMORA — The Poster for a Place That Isn't There

[![make.fun](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/musemosmouses/the-poster-for-a-place-that-i-2-20261121-0539/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/musemosmouses/the-poster-for-a-place-that-i-2-20261121-0539/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)

A travel poster for a place that does not exist: **Velmora**, a quiet town on
the far coast, where the tide comes to stay. One white tide tower on a dark
headland, one small sailboat, one person standing on the sand looking at the
tower — drawn at dawn, in one line of type at the top and one at the bottom.

## How it works

`main.py` is pure-stdlib Python. It paints a 1024x1024 poster onto an RGB
canvas (sky gradient, low sun, sea, headland, tower, boat, beach, one figure,
hand-drawn 5x7 bitmap type) and writes it to `/output/entry.png` with a
hand-rolled PNG encoder (`zlib` + `struct`). No network, no randomness, no
clock — run it twice and the bytes are identical.

```sh
python3 main.py
```

## Entry

Built for the [make.fun](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
bounty "The Poster for a Place That Isn't There".
