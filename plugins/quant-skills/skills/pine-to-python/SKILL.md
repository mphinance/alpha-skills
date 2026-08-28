---
name: pinescript-to-python-translator
description: "Translate TradingView PineScript strategies into vectorized Python strategies suitable for Optuna optimization and walk-forward analysis."
---

# 🌲 PineScript to Python Translator

This skill is designed to take raw TradingView PineScript files (`.pine`) and rigorously deconstruct them into Python-native components so they can be optimized using vectorization and tools like Optuna.

## When to use this skill
Use this skill when you want to migrate a backtest from the TradingView ecosystem into a headless Python environment. This is critical for running multi-fold Walk-Forward Analysis (WFA) and Monte Carlo simulations that TradingView cannot handle.

## Workflow

1. **Deconstruction & Classification (The IR Build)**
   - Parse the `.pine` script to identify `input()`, `input.int()`, `input.float()`, and `input.bool()`.
   - Classify parameters into three buckets:
     - **Signal**: Parameters that dictate entries (e.g., `length`, `crossover_threshold`).
     - **Risk**: Parameters that dictate exits (e.g., `stop_ticks`, `trail_offset`).
     - **Display**: Parameters used only for plotting/UI (discard these).

2. **Boundary Extraction**
   - For every Signal and Risk parameter, extract the `minval`, `maxval`, and `step` if provided.
   - Format these into Optuna trial suggestions (e.g., `trial.suggest_int('length', 10, 50)`).

3. **Logic Translation**
   - Translate PineScript technical analysis functions (`ta.sma`, `ta.ema`, `ta.rsi`) into their `pandas-ta` or `numpy` equivalents.
   - Vectorize the entry and exit conditions. Do not use standard `for` loops over rows unless path-dependency strictly requires it. Use `np.where` and `.shift()` wherever possible.

4. **Hardening & Auditing**
   - **Repaint Risk**: Scan the translation for anything relying on the *current* unclosed bar data. Force the use of `.shift(1)` for signal generation.
   - **Division by Zero**: Wrap all denominators in a `np.maximum(denominator, 1e-8)` guard to prevent NaN explosions during optimization.

## Output Format

The output should be a single Python file containing:
1. An `extract_features(df, params)` function that builds all the indicators based on a parameter dictionary.
2. A `generate_signals(df)` function that creates a `signal` column (1 for Long, -1 for Short, 0 for Flat).
3. A `get_optuna_space(trial)` function that returns the hyperparameter search space dictionary.
