# Corrected fireproof-button evidence

This is the current evidence set. Earlier files directly under `results/`
used a burnable button and must not be used for current-rule performance
or failure claims. No bot parameters were changed during this collection.

## Experiment design and reproduction

- D=60; four bots; 5,000-turn cutoff; button cannot ignite.
- Full sweep: 100 paired ships at each q=0.0, 0.1, ..., 1.0 (4,400 runs).
- Follow-up: 200 new paired ships at q=0.3 (800 additional runs).
- Focused CSV combines the original 100 q=0.3 ships with the 200 new ships.
  It contains 1,200 rows, including 400 already in the sweep. There are
  5,200 distinct runs overall, not 5,600. No runs timed out.
- The sweep took 827.3 seconds; sweep plus follow-up and intermediate
  plotting took 999.9 seconds (about 17 minutes).

Run `python3 -u collect_evidence.py`, then `python3 summarize_evidence.py`
from the repository root. Collection rewrites this evidence set with the
same seeds. The first script uses ten batches with seeds 600-609 (ten ships
each) and follow-up seeds 700-709 (twenty ships each). Trial IDs 0-99 are
shared across q; the new q=0.3 IDs are 100-299. Initial positions, ship
seeds, fire seeds, rule labels, and cutoffs are stored in every raw CSV row.
Bots share the same grid, starting positions, and fire progression at
equal elapsed turns, but have separate state and RNG objects per run.

The q=0.3 follow-up was chosen from the earlier exploration under the old
rules and fixed before the new experiment completed. No strategy was tuned
to the new results. The raw results can be replayed using, for example:

```sh
python3 replay.py --csv results/fireproof/focused_q03.csv --trial 100 --q 0.3
```

## Full-range results

![All four bots on shared axes](sweep.png)

| q | Bot 1 | Bot 2 | Bot 3 | Bot 4 |
| --- | ---: | ---: | ---: | ---: |
| 0.0 | 100% | 100% | 100% | 100% |
| 0.1 | 96% | 99% | 99% | 99% |
| 0.2 | 91% | 96% | 97% | 99% |
| 0.3 | 89% | 94% | 95% | 96% |
| 0.4 | 82% | 86% | 86% | 88% |
| 0.5 | 79% | 81% | 81% | 82% |
| 0.6 | 76% | 77% | 77% | 78% |
| 0.7 | 69% | 69% | 69% | 71% |
| 0.8 | 66% | 66% | 66% | 68% |
| 0.9 | 62% | 63% | 63% | 64% |
| 1.0 | 56% | 56% | 56% | 57% |

Each entry is based on 100 trials. At q=0, all bots succeed. At high q,
the curves approach each other but are not exactly identical in this sample.
At q=0.2-0.4, Bot 4 has a higher observed success rate than all three
other bots; these coarse-sweep differences alone do not establish superiority.

## Focused paired comparison at q=0.3

| Bot | Successful ships | Success rate |
| --- | ---: | ---: |
| Bot 1 | 264/300 | 88.00% |
| Bot 2 | 275/300 | 91.67% |
| Bot 3 | 278/300 | 92.67% |
| Bot 4 | 282/300 | 94.00% |

In the following table, a win means Bot 4 succeeds while the other bot
fails; a loss means the reverse. Difference and intervals use percentage
points. All 300 pairs, including ties, enter the difference denominator.

| Bot 4 versus | Wins | Losses | Difference | Approximate bootstrap 95% interval | Exact p | Holm-adjusted p |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| Bot 1 | 19 | 1 | +6.00 | [3.33, 9.00] | 0.000040 | 0.000120 |
| Bot 2 | 8 | 1 | +2.33 | [0.67, 4.33] | 0.039063 | 0.078125 |
| Bot 3 | 4 | 0 | +1.33 | [0.33, 2.67] | 0.125000 | 0.125000 |

Methods are implemented in `summarize_evidence.py`. The pointwise intervals
use 20,000 paired percentile bootstrap samples, implemented by multinomial
resampling of observed -1, 0, +1 outcome differences. NumPy's generator seed
is 42, with comparisons processed in Bot 1, Bot 2, Bot 3 order. These
intervals are approximate and can be optimistic when discordant outcomes
are scarce or one-sided: the Bot 3 interval cannot resample a Bot 4 loss
that was never observed. Its exclusion of zero is not conclusive evidence.

The exact two-sided McNemar p value is twice the binomial(n, 0.5) lower-tail
probability at min(wins, losses), capped at 1, with n=wins+losses.
Holm correction covers the three preselected comparisons at q=0.3.
At a 0.05 familywise threshold, only the Bot 4 versus Bot 1 comparison
is supported. Evidence against Bot 2 is weaker after correction; against
Bot 3 it is insufficient. The estimated Bot 4 advantage over Bot 3 is
four additional successes among 300 scenarios, or 1.33 percentage points.

Decision: retain the current strategy and report its observed improvement
with uncertainty. Do not claim Bot 4 reliably beats all three alternatives.
More sampling could reduce uncertainty, but is not guaranteed to establish
that difference. The full-range sweep is exploratory; the q=0.3 paired
comparison is the planned follow-up. This completes evidence collection
for the current draft without an open-ended search for significance.

## Files

- `sweep.csv`, `sweep.png`, `sweep_summary.csv`: full-range experiment.
- `focused_q03.csv`, `focused_summary.csv`: focused paired experiment.
- `paired_q03.json`: machine-readable uncertainty and paired tests.

The revised writeup is `analysis.md`. Current-rule diagnostic replays are
`replay_50_q03.json`, `replay_249_q03.json`, and `replay_0_q03.json`.
The first two include independently verified hindsight escape paths;
the third has no escape and the oracle exhausts surviving reachable states
on turn 266. `horizon_diagnostics.csv` records eight separate runs varying
only slack (0, 5, 20, 40) on Trials 50 and 249. These selected-case
diagnostics are not included in the reported 5,200-run performance sample.
The older replays directly under `results/` remain historical.
