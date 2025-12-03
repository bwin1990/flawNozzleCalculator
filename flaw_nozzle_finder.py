import argparse
import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception:
    tk = None


@dataclass
class LabelData:
    label: str
    points: List[Tuple[float, float]]
    nozzle_indices: List[int]
    out_of_range: List[Tuple[float, float]]
    angle_deg: float
    step: float
    start: float
    end: float
    details: List[Tuple[float, float, int, bool]]


def _get_field(row: Dict[str, str], names: Sequence[str]) -> str:
    for name in names:
        if name in row and row[name] != "":
            return row[name]
    return ""


def load_points(path: Path) -> Dict[str, List[Tuple[float, float]]]:
    groups: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for idx, row in enumerate(reader, start=1):
            label_raw = _get_field(row, ["Label", "label", "LABEL"]).strip()
            if not label_raw:
                continue

            x_raw = _get_field(row, ["X", "X,", "x", "x,"]).strip()
            y_raw = _get_field(row, ["Y", "Y,", "y", "y,"]).strip()
            try:
                x = float(x_raw)
                y = float(y_raw)
            except ValueError:
                raise ValueError(f"Row {idx}: cannot parse coordinates ({x_raw}, {y_raw})")

            groups[label_raw].append((x, y))
    return groups


def rotate_to_vertical(points: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
    if len(points) < 2:
        return []

    pts = sorted(points, key=lambda p: p[0])
    x1, y1 = pts[0]
    x2, y2 = pts[-1]
    dx = x2 - x1
    dy = y2 - y1
    # Use atan2(dy, dx) to capture small tilt around the X axis (avoid 90° swap)
    angle = math.atan2(dy, dx)

    cos_a = math.cos(-angle)
    sin_a = math.sin(-angle)
    rotated = []
    for x, y in pts:
        rx = x * cos_a - y * sin_a
        ry = x * sin_a + y * cos_a
        rotated.append((rx, ry))
    return angle, rotated


def find_nozzles(
    xs: Sequence[float], nozzle_count: int, tolerance: float
) -> Tuple[List[int], List[Tuple[float, float]], float, float, float, List[Tuple[float, float, int, bool]]]:
    if len(xs) < 2 or nozzle_count < 2:
        return [], [], 0.0, 0.0, 0.0, []

    sorted_x = sorted(xs)
    start = sorted_x[0]
    end = sorted_x[-1]
    mid = sorted_x[1:-1]
    if nozzle_count == 1:
        return [], [], start, end, 0.0, []

    step = (end - start) / (nozzle_count - 1)
    indices: List[int] = []
    out_of_range: List[Tuple[float, float]] = []
    details: List[Tuple[float, float, int, bool]] = []
    for x in mid:
        pos = (x - start) / step + 1
        rounded = round(pos)
        in_tol = abs(rounded - pos) < tolerance
        if in_tol:
            indices.append(int(rounded))
        else:
            out_of_range.append((x, pos))
        details.append((x, pos, int(rounded), in_tol))
    return indices, out_of_range, start, end, step, details


def process_labels(
    groups: Dict[str, List[Tuple[float, float]]],
    nozzle_count: int,
    tolerance: float,
) -> List[LabelData]:
    results: List[LabelData] = []
    for label in sorted(groups):
        pts = groups[label]
        angle, rotated = rotate_to_vertical(pts) if len(pts) >= 2 else (0.0, [])
        xs = [p[0] for p in rotated]
        indices, outliers, start, end, step, details = find_nozzles(xs, nozzle_count, tolerance)
        results.append(
            LabelData(
                label=label,
                points=pts,
                nozzle_indices=indices,
                out_of_range=outliers,
                angle_deg=math.degrees(angle),
                step=step,
                start=start,
                end=end,
                details=details,
            )
        )
    return results


def write_output(output_path: Path, indices: Iterable[int]) -> None:
    with output_path.open("w", encoding="utf-8") as fh:
        for idx in indices:
            fh.write(f"{idx}\n")


def print_debug(label_data: Sequence[LabelData], combined: List[int]) -> None:
    total_labels = len(label_data)
    total_points = sum(len(ld.points) for ld in label_data)
    print(f"Loaded {total_points} points across {total_labels} labels.")
    for ld in label_data:
        out_cnt = len(ld.out_of_range)
        out_msg = f", {out_cnt} out-of-range" if out_cnt else ""
        print(f"- {ld.label}: {len(ld.points)} points, indices={ld.nozzle_indices}{out_msg}")
    print(f"Combined nozzle list ({len(combined)} unique): {combined}")


def choose_file_via_gui() -> Path:
    if tk is None:
        raise RuntimeError("Tkinter not available; please provide CSV path via CLI.")
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="选择 CSV 文件",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    if not file_path:
        raise RuntimeError("未选择文件，操作已取消。")
    return Path(file_path)


def wait_for_enter(prompt: str) -> None:
    try:
        input(prompt)
    except EOFError:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate flaw nozzle indices from CSV data.")
    parser.add_argument("csv_path", nargs="?", type=Path, help="Input CSV file with Label, X, Y columns. If omitted, a file dialog will open.")
    parser.add_argument(
        "-m",
        "--machine",
        help="Machine identifier suffix (e.g., 04) appended to the output filename. If omitted, you will be prompted.",
    )
    parser.add_argument("--nozzles", type=int, default=636, help="Total nozzle count (default: 636).")
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.25,
        help="Tolerance in nozzle steps for matching (default: 0.25).",
    )
    args = parser.parse_args()

    if args.csv_path is None:
        csv_path = choose_file_via_gui()
    else:
        csv_path = args.csv_path

    print(f"Selected file: {csv_path}")
    wait_for_enter("Press Enter to load the file (Ctrl+C to abort)...")

    groups = load_points(csv_path)
    if not groups:
        print("No data loaded. Exiting.")
        return

    print("Labels found and point counts:")
    for label in sorted(groups):
        print(f"  {label}: {len(groups[label])} points")
    wait_for_enter("Press Enter to compute rotations and nozzle indices...")

    label_data = process_labels(groups, args.nozzles, args.tolerance)

    combined = sorted({idx for ld in label_data for idx in ld.nozzle_indices})
    print_debug(label_data, combined)

    wait_for_enter("Press Enter to proceed to export (or Ctrl+C to abort)...")

    machine = args.machine
    if not machine:
        machine = input("Enter machine identifier (e.g., 04): ").strip()
        if not machine:
            print("No machine identifier provided. Exiting without export.")
            return

    date_str = datetime.now().strftime("%Y%m%d")
    output_name = f"flaw_nozzle_{date_str}_680k_{machine}.txt"
    output_path = csv_path.parent / output_name
    write_output(output_path, combined)
    print(f"Output written to: {output_path}")

    if any(ld.out_of_range for ld in label_data):
        print("Warning: some points were out of range. See details above.")


if __name__ == "__main__":
    main()
