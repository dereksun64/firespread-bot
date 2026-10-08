# Focused 60x60 experiment

> LEGACY RESULTS: This experiment used a burnable button. The current code
> uses the fireproof-button rule clarified in remote commit 03fabb5.
> These statistics and graphs must be regenerated before submission.

Added 200 new paired scenarios at q=0.3, 0.4, 0.5. Combining these with
the corresponding 100 scenarios from the exploratory sweep gives 300
trials per bot/q and 3,600 rows in `focused_60.csv`. There were no timeouts.
The new experiment took 487.7 seconds before final plotting.

Reproduction: ten calls to `run_experiments(60, [0.3, 0.4, 0.5], 20,
seed=500 + batch)` for batch 0-9. New trial IDs were offset by
`100 + 20 * batch`; original trial IDs 0-99 were retained. The cutoff
was 5,000 turns. Seeds and initial positions are saved in the CSV.

![Focused success rates](focused_60.png)

| q | Bot 1 | Bot 2 | Bot 3 | Bot 4 |
| --- | ---: | ---: | ---: | ---: |
| 0.3 | 250/300 (83.33%) | 256/300 (85.33%) | 263/300 (87.67%) | 265/300 (88.33%) |
| 0.4 | 239/300 (79.67%) | 246/300 (82.00%) | 245/300 (81.67%) | 248/300 (82.67%) |
| 0.5 | 221/300 (73.67%) | 223/300 (74.33%) | 225/300 (75.00%) | 228/300 (76.00%) |

## Paired comparisons

For each comparison, a win means Bot 4 succeeds while the other bot fails;
a loss means the reverse. Ties remain part of the 300-trial denominator.
Differences and intervals below are in percentage points, not relative percent.

| q | Bot 4 vs | Wins | Losses | Difference | Bootstrap 95% interval | Exact p | Holm-adjusted p |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 0.3 | Bot 1 | 15 | 0 | +5.00 | [2.67, 7.67] | 0.000061 | 0.000549 |
| 0.3 | Bot 2 | 9 | 0 | +3.00 | [1.33, 5.00] | 0.003906 | 0.031250 |
| 0.3 | Bot 3 | 3 | 1 | +0.67 | [-0.67, 2.00] | 0.625000 | 1.000000 |
| 0.4 | Bot 1 | 9 | 0 | +3.00 | [1.33, 5.00] | 0.003906 | 0.031250 |
| 0.4 | Bot 2 | 3 | 1 | +0.67 | [-0.67, 2.00] | 0.625000 | 1.000000 |
| 0.4 | Bot 3 | 4 | 1 | +1.00 | [-0.33, 2.67] | 0.375000 | 1.000000 |
| 0.5 | Bot 1 | 7 | 0 | +2.33 | [0.67, 4.33] | 0.015625 | 0.093750 |
| 0.5 | Bot 2 | 5 | 0 | +1.67 | [0.33, 3.33] | 0.062500 | 0.312500 |
| 0.5 | Bot 3 | 3 | 0 | +1.00 | [0.00, 2.33] | 0.250000 | 1.000000 |

The intervals use 20,000 paired percentile bootstrap samples. Each pair's
success difference is -1, 0, or +1. Sampling counts from the multinomial
distribution with observed frequencies is equivalent to resampling those
300 paired differences. The random generator was NumPy `default_rng(42)`,
with comparisons processed by increasing q, then Bot 1, Bot 2, Bot 3.
The interval is the 2.5th and 97.5th percentiles of the resampled mean.
These are pointwise, approximate intervals; they are not simultaneous and
can be optimistic when observed discordant counts are small or one-sided.

The exact p value is a two-sided McNemar test: among n discordant pairs,
twice the binomial( n, 0.5 ) probability of at most min(wins, losses),
capped at 1. Holm correction covers all nine comparisons in this table.
It remains valid with dependent tests across q. At the conventional 0.05
threshold, the adjusted tests support Bot 4 over Bot 1 at q=0.3 and 0.4,
and over Bot 2 at q=0.3. None supports Bot 4 over Bot 3.

The q values were selected after inspecting the exploratory sweep, and
the pooled analysis reuses that exploratory data. Treat these conclusions
as exploratory evidence, not a preregistered confirmation or proof that
Bot 4 dominates across grids, q values, and random seeds. No Bot 4 strategy
parameters were changed during this follow-up.
