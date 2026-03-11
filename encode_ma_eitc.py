"""Stress test: encode MA EITC (Mass. General Laws c. 62, § 6(h))."""

import asyncio
from pathlib import Path

from autorac.harness.orchestrator import Orchestrator

CITATION = "Mass. General Laws c. 62 § 6(h)"
OUTPUT = Path(__file__).parent / "statute" / "ma" / "62" / "6" / "h"
STATUTE_TEXT = Path("/tmp/ma_62_6_h.txt").read_text()

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
