## Exploratory 60x60 sweep

`exploratory_60.csv` contains 4,400 trial outcomes; `exploratory_60.png`
plots the success rates. Each bot ran on 100 ships at each q in
0.0, 0.1, ..., 1.0. No runs timed out (5,000-turn cutoff).

The sweep used ten batches: `run_experiments(60, [i / 10 for i in range(11)],
10, seed=400 + batch)` for batch 0 through 9. Trial IDs were offset by
`batch * 10` before concatenating the rows. Ships, positions, and fire seeds
were paired across bots and q within each trial. All seeds and positions
needed to replay a trial are stored in the CSV. Runtime was 820.6 seconds,
excluding final plotting.

At q=0.3, success rates for Bots 1-4 were 85%, 86%, 88%, and 89%.
At q=0.5, they were 69%, 71%, 73%, and 73%.
At q=0.9 and q=1.0, all bots had identical success rates (52% and 48%).
The curves show small differences, not identical behavior. With only 100
ships per point, this exploratory sample does not establish a statistically
reliable ranking. More paired trials around q=0.3-0.5 would help evaluate
the observed differences.

## Replayed failure examples

Run `python3 replay.py --trial 9 --q 0.5` or
`python3 replay.py --trial 4 --q 0.3`. Add `--output path.json` to save
every move and the fire immediately before and after that move's spread.
Replays verify the saved outcome and step count and check legal moves.
The two saved JSON histories contain all four bots' runs and the grid.

Trial 9, q=0.5 (`replay_9_q05.json`):

- Bot 1 burns on turn 8; Bot 2 succeeds in 36 turns; Bots 3-4 in 34.
- At turn 8, Bots 1 and 2 are at (40,30), with identical fire states.
  Bot 1 moves to (39,30); Bot 2 moves back to (41,30). Bot 1's
  destination is not yet burning but ignites in that turn's spread.
- Bot 3 diverges from Bot 2 earlier, on turn 7, using (41,31) instead
  of (40,30). Bot 4 first diverges from Bot 3 on turn 4.
- This is evidence that alternative decisions saved the other bots in
  the same realized fire scenario. It is not evidence that Bot 1 could
  know the next random ignition with certainty.

Trial 4, q=0.3 (`replay_4_q03.json`):

- Bot 1 burns on turn 44; Bots 2-3 burn on turn 59; Bot 4 succeeds in 55.
- Bot 1 enters existing fire at (22,48), still following its original
  plan. Just before its final move, a 20-move route avoiding current fire
  exists from its position, so that move was avoidable.
- Bots 2-3 take the same path. On turn 59, the button is already burning,
  so neither can find a safe route; they stay at (24,56), which ignites.
  A safe neighboring cell exists, but cannot restore access to the button.
- Bot 4 diverges from Bot 3 on turn 3, choosing (42,27) instead of
  (41,26). It reaches the button on turn 55, before the fire blocks success.
  This illustrates the value of an earlier risk-aware decision; it does
  not establish that every individual Bot 4 move was optimal.

The fire generator depends only on the grid, q, seed, and elapsed turns,
so paired runs share identical fire states at equal times until success
or termination. Bot movement does not influence fire spread.

## Bot 4 failure diagnosis

Saved histories: `replay_6_q01.json`, `replay_22_q01.json`,
`replay_58_q03.json`, and `replay_47_q04.json`.
Use `python3 replay.py --trial 47 --q 0.4 --hindsight` to reproduce
the oracle diagnosis. The oracle searches time layers with exact future
fire, includes staying, and checks arrival before the next spread.

- Trial 6, q=0.1: shortest initial route 54 moves, button burns on update
  25; no hindsight escape. Bot 4 burns on turn 133.
- Trial 22, q=0.1: shortest initial route 47 moves, button burns on update
  1; no hindsight escape. Bot 4 burns on turn 374.
- Trial 58, q=0.3: shortest initial route 61 moves, button burns on update
  71; no hindsight escape because routes are blocked by the evolving fire.
  Bot 4 burns on turn 93.
- Trial 47, q=0.4: all bots fail, but a 91-move hindsight escape exists.
  Bot 4 burns on turn 29. Its first divergence from the recovered oracle
  path is on turn 17. The JSON includes the independently verified escape.

These claims concern the saved fire sequences, not the probability of
success under other fire draws. The oracle has information unavailable to
the bots; its result does not establish that a particular online decision
was irrational. Its general cutoff is 5,000 turns; the no-escape cases
above terminate because the button burns or all reachable states disappear,
not because this cutoff expires.
