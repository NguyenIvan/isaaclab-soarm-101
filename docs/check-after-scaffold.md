---

**1. Structure check (10 seconds).** Eyeball the tree against your CLAUDE.md layout. Every directory you expect has an `__init__.py`. `pyproject.toml` exists at the root. `scripts/environments/list_envs.py` exists. No stray files in weird places.

**2. Install check.**

```bash
uv sync
```

Should complete without resolver errors. Then confirm IsaacSim is actually present in the conda env (not just the `uv` env):

```bash
conda activate v2.3.2
pip list | grep -iE "isaacsim|isaaclab|so.arm|gymnasium"
```

You want to see a stack of `isaacsim-*` packages, the `isaaclab*` packages, and your own package listed (usually with an editable path). If no `isaacsim-*` packages appear, the IsaacSim install never landed against this env — fix by rerunning the installer with the env activated:

```bash
conda activate v2.3.2
./isaaclab.sh -i
```

If your package isn't listed but `isaacsim-*` is, `pyproject.toml` isn't declaring your package as installable correctly *into the conda Python*. Install it directly: `./isaaclab.sh -p -m pip install -e .` from the project root.

**3. Import check (AppLauncher-gated).** Anything that imports `isaaclab.utils`, USD bindings, or articulation configs needs the runtime up first. Drop this in `test_appcontext.py` at the project root:

```python
from isaaclab.app import AppLauncher
simulation_app = AppLauncher(headless=True).app

# now safe — runtime is up
from pxr import Usd, UsdGeom  # noqa: F401
from isaaclab.utils import configclass  # noqa: F401

import so_arm101_block  # noqa: F401
from so_arm101_block.robots import so_arm101  # noqa: F401
from so_arm101_block.tasks.block import block_env_cfg  # noqa: F401
from so_arm101_block.agents import rsl_rl_ppo_cfg  # noqa: F401

print("appcontext ok")
simulation_app.close()
```

Run it:

```bash
./isaaclab.sh -p test_appcontext.py
```

You want `appcontext ok` at the end. If it dies on `from pxr import ...`, IsaacSim isn't installed against this Python — back to step 2. If it dies on the `isaaclab.utils` import, IsaacLab itself isn't installed. If it dies importing your package, the two-Python-env problem — also step 2.

This is the right place to test imports of any module that eventually pulls in `isaaclab.utils.mesh` or `pxr` — which will be most of your robot config and env code once those stubs become real. **Don't try to validate them with bare `-c` imports**; you'll get spurious "missing pxr" errors that aren't real.

**4. List-envs check.**

```bash
./isaaclab.sh -p scripts/environments/list_envs.py
```

`list_envs.py` launches the SimulationApp internally (it has to, in order to import task modules), so it's effectively running in the same context as step 3 — that's why it's the realistic end-to-end smoke test for the scaffold.

The acceptable outcomes: prints "no tasks", or prints only Isaac Lab built-ins, or prints an empty table. The unacceptable outcomes: an `ImportError` mentioning your package, or any traceback past the normal Kit startup chatter.

Grep for your package name:

```bash
./isaaclab.sh -p scripts/environments/list_envs.py 2>&1 | grep -i so_arm
```

At this stage should return nothing — you haven't registered anything yet. A match means Claude registered a task it shouldn't have.

**5. Lint check.**

```bash
uv run ruff check .
uv run ruff format --check .
```

**6. Git hygiene.** `git status` should show only files you expect. No `.venv/`, `__pycache__/`, `*.egg-info/`, or `test_appcontext.py` (add the test file to `.gitignore` if you're keeping it as a scratch tool, or delete it after step 3).

---

**The single most diagnostic check** is step 4, `list_envs.py`. It launches the app, imports your package, and exercises every import path that real task code will use, all in one command. If it runs cleanly, the scaffold is sound. Step 3 is the fallback when step 4 fails and you need to localize whether the problem is the runtime, the IsaacLab install, or your own package.

**The pitfall to avoid:** don't validate any `@configclass` that imports robot configs, articulation configs, USD paths, or anything from `isaaclab.utils` via a bare `./isaaclab.sh -p -c "from ..."`. You'll get an error that looks like a missing dependency but is really the AppLauncher gate. Always use the step-3 pattern (AppLauncher first, then import) — or just run `list_envs.py`, which does it for you.