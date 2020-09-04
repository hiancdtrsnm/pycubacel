#! /bin/env python

from micubacel_manager import MiCubacelConfig
from pathlib import Path
import typer

def consult(config_path: Path):
    micubacel = MiCubacelConfig(config_path)
    return micubacel.compute_delta_and_update()

if __name__ == "__main__":
    typer.run(consult)
    #consult(Path('./config.json'))
