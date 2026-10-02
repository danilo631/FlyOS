# FlyKWin patches

These are optional source-level changes against KDE KWin. They are **not** installed by the default ISO because KWin is security- and graphics-critical and should normally follow Ubuntu/KDE updates.

`0002-flyos-deeper-blur.patch` extends KWin's stock blur strength table with one additional downsample step. It is intended for a future `flyos-kwin` package or a developer fork, not for blind patching of a running system.

The default Fly OS experience uses stock KWin blur. The optional `flyos-kwin-glass` package provides more aggressive force-blur and rounded-corner features without replacing the whole compositor.
