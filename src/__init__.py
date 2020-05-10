from pathlib import Path
loader_path = Path(__file__).parent.resolve().joinpath("data/loader.bin")
with open(loader_path, "rb") as f:
    loader = f.read()
