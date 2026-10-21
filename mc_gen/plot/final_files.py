"""File of a tune for the final comparisons."""

# tune25: final production (228300 events); the other tunes use the scan files DY_tuneNN.root
FINAL_FILES = {"tune25": "../data/DY-Config-25-Oct12-2026.root"}


def tune_file(name):
    """File of a tune for the final comparisons: the large production if there is one, else the scan file."""
    return FINAL_FILES.get(name, f"../data/DY_{name}.root")
