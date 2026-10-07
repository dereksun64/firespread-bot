## TODO
- [x] shared `bfs.py` helper used by all bots

- steps
    - [x] ship.py      (P) done: make a layout
    - [x] fire.py      (D) next: spread the fire one timestep 
    - [x] bots.py      (P) Bot 1
    - [x] simulate.py  (D) run bot moves and fire turns in the required order
    - [x] bots.py      (D, P) Bots 2, 3, and 4
    - [ ] simulate.py  (D, P) repeated trials and graph data

Run one seeded comparison: `python3 simulate.py`

Run simulator tests: `python3 -m unittest discover -s tests -v`

Run the existing fire check: `PYTHONPATH=. python3 tests/test_fire.py`
