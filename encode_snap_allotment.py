"""Stress test: encode SNAP allotment (7 USC 2017)."""

import asyncio
from pathlib import Path

from autorac.harness.orchestrator import Orchestrator

CITATION = "7 USC 2017"
OUTPUT = Path(__file__).parent / "statute" / "7" / "2017"
STATUTE_TEXT = Path("/tmp/7_usc_2017.txt").read_text()

orchestrator = Orchestrator(backend="cli")
run = asyncio.run(
    orchestrator.encode(
        CITATION,
        output_path=OUTPUT,
        statute_text=STATUTE_TEXT,
    )
)

print(orchestrator.print_report(run))
print(f"\nFiles created: {len(run.files_created)}")
for f in run.files_created:
    print(f"  {f}")
