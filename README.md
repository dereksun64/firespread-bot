## Setup

The button is fireproof, following the TA clarification recorded in commit
03fabb5. Corrected evidence is in `results/fireproof/`; reproduce it with
`python3 -u collect_evidence.py` and `python3 summarize_evidence.py`.
Older artifacts directly in `results/` used the earlier burnable-button
model and are historical. `analysis.md` uses the corrected evidence and
current-rule diagnoses; LaTeX typesetting and PDF preparation remain.

Tested with Python 3.9.6. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
```

The dependency versions match the completed experiments. Review `analysis.md`
for the writeup draft; graphs, raw results, and experiment methods are in `results/`.

## TODO
- [x] regenerate evidence for fireproof-button rules, including 300 paired trials at q=0.3
- [x] revise analysis for the fireproof-button rules and new evidence
- [ ] typeset the revised writeup in LaTeX and inspect its compiled PDF
- [x] shared `bfs.py` helper used by all bots

- steps
    - [x] ship.py      (P) done: make a layout
    - [x] fire.py      (D) next: spread the fire one timestep 
    - [x] bots.py      (P) Bot 1
    - [x] simulate.py  (D) run bot moves and fire turns in the required order
    - [x] bots.py      (D, P) Bots 2, 3, and 4
    - [x] simulate.py  (D, P) repeated trials across flammability values
    - [x] save experiment results and graph success rates
    - [x] benchmark runtime and choose a practical grid size
    - [x] run a 60x60 exploratory sweep and inspect success-rate graphs
    - [x] replay contrasting outcomes and document failure examples
    - [x] draft assignment analysis in analysis.md
    - [x] diagnose representative Bot 4 failures with a hindsight escape search
    - [x] add 200 focused paired scenarios and assess uncertainty in bot differences
    - [x] final code review, dependency setup, and unified test command

Run one seeded comparison: `python3 simulate.py`

Run repeated comparisons: `python3 simulate.py --size 10 --trials 10 --q 0 0.1 0.3 0.5 1 --seed 4`

Each trial shares its layout, initial positions, and fire seed across bots and q values.
Save raw results and a graph:
`python3 simulate.py --size 10 --trials 100 --q 0 0.1 0.3 0.5 1 --seed 4 --csv results/trials.csv --plot results/success.png`

The graph counts timeouts as unsuccessful trials. Small runs are checks, not final experimental evidence.

Run all tests: `python3 -m unittest discover -s tests -v`

Run the existing fire check: `PYTHONPATH=. python3 tests/test_fire.py`

Runtime benchmark: `python3 benchmark.py`

On the development machine, 3 paired ships at q = 0, 0.1, 0.3, 0.6, 1
gave these mean complete-trial times in seconds (15 runs per bot per size):

| Grid size | Bot 1 | Bot 2 | Bot 3 | Bot 4 |
| --- | ---: | ---: | ---: | ---: |
| 20 | 0.0028 | 0.0032 | 0.0033 | 0.0130 |
| 40 | 0.0342 | 0.0424 | 0.0418 | 0.0957 |
| 60 | 0.0989 | 0.1111 | 0.1132 | 0.2180 |
| 80 | 0.2997 | 0.4150 | 0.4326 | 0.8803 |

No benchmark run timed out. D=80 is feasible for an additional sweep;
100 ships at 11 q values with all four bots is estimated at about 37 minutes.
D=60 is a faster exploratory option (about 10 minutes for the same sweep).
These are small-sample estimates, exclude ship generation/plotting, and vary
with seeds and q. The benchmark measures bot decisions plus fire simulation,
not just pathfinding. It does not establish accuracy of success rates.

Controlled path comparisons are in `tests/test_pathfinding.py`:

- On the 6x6 ship generated with seed 16, start (2,2), button (3,3),
  fire (1,5), q=0.3 and fire seed 16, Bot 1 burns on turn 2;
  Bots 2-4 replan and succeed on turn 10.
- On an open 5x5 grid with start (1,0), button (1,4), fire (0,2), q=0,
  Bots 1,2,4 take 4 turns; Bot 3's fire buffer forces a 6-turn detour.
- On the 6x6 ship generated with seed 0, start (2,3), button (5,1),
  fire (5,2), q=0.3, Bots 2-3 move to (3,3), while Bot 4 moves to (2,2).
  An independent scalar forecast and forward search confirm this minimizes
  the model's cumulative risk cost over Bot 4's 27-turn horizon.

These checks demonstrate distinct strategies and validate the risk model on
a controlled case; they do not prove Bot 4 maximizes actual survival probability.

The completed 60x60 sweep (100 ships per q, 4,400 runs) and its methodology
are in `results/README.md`, with raw CSV results and the success-rate graph.

The focused follow-up (300 total ships per q at 0.3, 0.4, 0.5) is documented
in `results/focused_analysis.md`, with paired uncertainty estimates.
