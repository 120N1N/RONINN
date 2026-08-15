#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

GROUPS = {
    "web": [f"a{i:02d}" for i in range(1, 11)],
    "api": [f"api{i:02d}" for i in range(1, 11)],
    "both": [f"a{i:02d}" for i in range(1, 11)] + [f"api{i:02d}" for i in range(1, 11)],
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate OWASP A01-A10/API1-API10 test cards for an endpoint.")
    parser.add_argument("profile", choices=sorted(GROUPS), help="Coverage profile to generate")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Engagement root")
    parser.add_argument("--asset-id", default="")
    parser.add_argument("--endpoint-id", default="")
    parser.add_argument("--method", default="")
    parser.add_argument("--path", default="")
    parser.add_argument("--target", default="")
    parser.add_argument("--loop-id", default="")
    parser.add_argument("--priority", default="1")
    parser.add_argument("--actor", default="ai")
    parser.add_argument("--angle-profile", choices=["core", "deep", "creative", "full"], default="full")
    parser.add_argument("--skip-angle-plan", action="store_true", help="Do not create endpoint_angle_planned/creative events.")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    common = [
        "--root",
        str(root),
        "--asset-id",
        args.asset_id,
        "--endpoint-id",
        args.endpoint_id,
        "--method",
        args.method,
        "--path",
        args.path,
        "--target",
        args.target,
        "--priority",
        args.priority,
        "--actor",
        args.actor,
        "--no-build",
    ]
    if args.loop_id:
        common.extend(["--loop-id", args.loop_id])

    created = 0
    for key in GROUPS[args.profile]:
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/pentest_card.py"),
                key,
                "--title",
                f"{key.upper()} coverage test for {args.endpoint_id or args.path or args.target or 'target'}",
                *common,
            ],
            check=True,
        )
        created += 1

    if not args.skip_angle_plan:
        angle_cmd = [
            sys.executable,
            str(ROOT / "scripts/angle_plan.py"),
            args.angle_profile,
            "--root",
            str(root),
            "--asset-id",
            args.asset_id,
            "--endpoint-id",
            args.endpoint_id,
            "--method",
            args.method,
            "--path",
            args.path,
            "--target",
            args.target,
            "--actor",
            args.actor,
            "--source",
            f"bbf owasp-plan {args.profile}",
            "--no-build",
        ]
        if args.loop_id:
            angle_cmd.extend(["--loop-id", args.loop_id])
        subprocess.run(angle_cmd, check=True)

    subprocess.run([sys.executable, str(ROOT / "scripts/build_graph.py"), "--root", str(root)], check=True)
    print(f"created {created} {args.profile} OWASP coverage cards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
