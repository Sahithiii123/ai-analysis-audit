"""Generate summary reports from schema-validated case results."""

from __future__ import annotations

from reporting import build_reports


def main() -> int:
    for path in build_reports():
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())