# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""List registered Isaac Lab environments."""

import argparse

from isaaclab.app import AppLauncher

# launch app
parser = argparse.ArgumentParser(description="List registered Isaac Lab environments.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
app_launcher = AppLauncher(args_cli)
app = app_launcher.app

# import task package so registration hooks run
import so_arm101_block  # noqa: F401

from isaaclab_tasks.utils import parse_env_cfg


def main():
    from gymnasium import registry

    env_ids = sorted(env_id for env_id in registry if "Block" in env_id or "SO-ARM101" in env_id)
    print("Registered environments:")
    for env_id in env_ids:
        print(env_id)

    app.close()


if __name__ == "__main__":
    main()
