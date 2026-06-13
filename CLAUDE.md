# Claude Code Instructions for SO-ARM101 Stick-Block

## Project goal

Train the **SO-ARM101** low-cost arm in **NVIDIA Isaac Lab** to wield a stick and **block an incoming stick**. A stick is launched toward the arm; the policy must position and orient its own held stick to intercept and deflect the incoming one before it reaches a defended zone in front of the base. Built as an external Isaac Lab project and trained with **RSL-RL (PPO)** across thousands of parallel GPU environments.

## Repo layout (orient here first)

- `source/<ext_name>/` — the task extension package (where almost all edits happen)
  - `robots/` — `SO_ARM101_CFG` articulation config (USD path, actuators, joint limits)
  - `tasks/block/` — the blocking env: `*_env_cfg.py` (scene + MDP wiring) and `mdp/` (observations, rewards, terminations, events)
  - `agents/` — RL hyperparameters (e.g. `rsl_rl_ppo_cfg.py`)
  - `__init__.py` — `gym.register(...)` task IDs
- `scripts/` — train / play / list-envs entry points
- `logs/` — training runs for Tensorboard, pattern `logs/rsl_rl/<task>/<date-time>`
- Isaac Lab and Isaac Sim core live **outside** this repo — treat them as read-only dependencies.

## Tool strategy

- Use **Claude Code** for repo-wide work: reward-function reviews, refactoring env configs across the task package, and reasoning about how MDP terms interact.
- Use **Aider** for small edits touching only 1–3 files (a single reward term, one joint limit).
- Use **AgentMemory** for durable decisions and recurring gotchas (reward-shaping choices, sim params that broke training, sim-to-real notes).

## Token-saving rules

1. Do not read Isaac Lab / Isaac Sim core source. Stay inside the task extension package unless a dependency's behavior is genuinely unclear.
2. Prefer editing `@configclass` config classes over rewriting logic; change the smallest number of files.
3. Before large changes (new reward terms, observation/action-space changes, task restructure), write a short plan first.
4. Do **not** launch full training just to validate a change. Smoke-test instead: list envs, then run a zero/random agent or a few-iteration headless training run.
5. Keep explanations short unless asked for detail. RL configs are dense — point to the specific term, don't restate the whole env.

## Commands

Set up (external project via uv; assumes Isaac Lab + Isaac Sim already installed):

```bash
uv sync
```

List registered tasks:

```bash
./isaaclab.sh -p scripts/environments/list_envs.py
```

Smoke-test the env (no learning):

```bash
./isaaclab.sh -p scripts/environments/zero_agent.py   --task SO-ARM101-Block-Play-v0 --num_envs 16
./isaaclab.sh -p scripts/environments/random_agent.py --task SO-ARM101-Block-Play-v0 --num_envs 16
```

Train (headless, many parallel envs):

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
  --task SO-ARM101-Block-v0 --headless --num_envs 4096
```

Evaluate a checkpoint (with viewer, fewer envs):

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py \
  --task SO-ARM101-Block-Play-v0 --num_envs 32 \
  --load_run <run_folder> --checkpoint model.pt
```

Record a video of a trained policy (needs ffmpeg):

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py \
  --task SO-ARM101-Block-Play-v0 --headless --video --video_length 300
```

Watch training curves:

```bash
tensorboard --logdir logs/rsl_rl
```

Lint:

```bash
uv run ruff check .
```

Format:

```bash
uv run ruff format .
```

## Task-specific notes (the blocking problem)

- The held stick is **rigidly attached** to the SO-ARM101 end-effector (fixed joint / welded body), so the policy controls it indirectly through arm joints — this is not a grasp task.
- The incoming stick is a rigid body launched with a **randomized** initial pose and velocity toward the defended zone.
- Core reward: contact between held stick and incoming stick, plus deflection away from the defended zone. Shape with distance-to-intercept and orientation-alignment terms; penalize joint-limit violations, excessive effort, and self-collision.
- Termination: incoming stick deflected (closest approach stays outside the defended zone) = success; it reaches the zone = failure; otherwise time-out.
- Domain-randomize the incoming stick (launch position, speed, angle, mass) and arm dynamics so the policy generalizes and transfers toward real hardware.
- Keep deployed observations **observable on the real arm** (joint pos/vel, held-stick pose, estimated incoming-stick state). Avoid privileged sim-only signals in the final policy, or use teacher→student distillation if you need them during training.

## Coding conventions

- **Python 3.11** to match the Isaac Sim runtime in this environment.
- Define environments and assets with Isaac Lab `@configclass` config classes; prefer config over imperative setup.
- Keep three concerns separate: robot/asset config, task/MDP logic (observations, rewards, terminations, events), and RL agent hyperparameters.
- Put each MDP term in the `mdp/` modules as a small, named, documented function; keep reward terms independently toggleable.
- Register every task with `gym.register` and a clear ID; keep a `-Play-v0` variant for evaluation.
- Seed runs and pin sim/physics params for reproducibility; never hardcode absolute asset paths — resolve them from config.
- When you change the observation or action space, update the agent config and flag it — checkpoints won't load across shape changes.
- Add or update a smoke test (zero/random agent runs cleanly) with every behavior change.