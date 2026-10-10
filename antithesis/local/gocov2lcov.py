#!/usr/bin/env python3
"""Convert a Go text coverage profile into LCOV with function names.

Usage: gocov2lcov.py <coverage.gocov> <repo-root> > coverage.lcov

Go profiles have line ranges but no function names, so coverage_report.py's
`by-op` can't tell which functions were reached. This reads each source file,
finds its top-level `func` lines (gofmt puts them at column 0), names them
`Type.Method` or `Func`, and assigns every profile block to the function it
starts in. Paths in the profile must already be repo-relative (see
extract_coverage() in run-local.sh).
"""
import os
import re
import sys
from collections import defaultdict

BLOCK = re.compile(r"(.+):(\d+)\.\d+,(\d+)\.\d+ \d+ (\d+)$")
FUNC = re.compile(r"^func\s*(?:\(\s*\w*\s*\*?\s*(\w+)(?:\[[^\]]*\])?\s*\))?\s*(\w+)")


def functions(path):
    """[(start line, name)] in file order."""
    out = []
    with open(path, errors="replace") as f:
        for n, line in enumerate(f, 1):
            m = FUNC.match(line)
            if m:
                out.append((n, f"{m.group(1)}.{m.group(2)}" if m.group(1) else m.group(2)))
    return out


def main(profile, repo):
    blocks = defaultdict(list)  # file -> [(start, end, count)]
    with open(profile) as f:
        for line in f:
            m = BLOCK.match(line.strip())
            if m:
                blocks[m.group(1)].append((int(m.group(2)), int(m.group(3)), int(m.group(4))))
    for path, bs in sorted(blocks.items()):
        src = os.path.join(repo, path)
        funcs = functions(src) if os.path.exists(src) else []
        lines, fhits = defaultdict(int), {}
        for start, end, count in bs:
            for n in range(start, end + 1):
                lines[n] = max(lines[n], count)
            owner = None
            for fstart, name in funcs:
                if fstart > start:
                    break
                owner = (fstart, name)
            if owner:
                fhits[owner] = max(fhits.get(owner, 0), count)
        print(f"SF:{path}")
        for (fstart, name), hits in sorted(fhits.items()):
            print(f"FN:{fstart},{name}")
            print(f"FNDA:{hits},{name}")
        for n in sorted(lines):
            print(f"DA:{n},{lines[n]}")
        print("end_of_record")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
