#!/usr/bin/env python3
"""
Generate a land/water bitmap for Beyond the Sea.

Uses Natural Earth low-res land polygons (bundled with geopandas) to create
a 1800x3600 (0.1 degree) grid. Output is a bitpacked, RLE-compressed,
base64-encoded JavaScript constant ready to embed in index.html.

Usage:
    python3 generate_bitmap.py > bitmap_data.js
"""

import geopandas as gpd
import numpy as np
from shapely.geometry import Point
from shapely.prepared import prep
from shapely.ops import unary_union
import base64
import sys
import time


def generate_grid(rows=720, cols=1440, res=0.25):
    """Generate land/water grid using Natural Earth data."""
    print(f"Loading Natural Earth land polygons...", file=sys.stderr)
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    shp_path = os.path.join(script_dir, 'ne_50m_land', 'ne_50m_land.shp')
    world = gpd.read_file(shp_path)
    land_geoms = world[world.geometry.notnull()].geometry.tolist()

    print(f"Merging {len(land_geoms)} polygons...", file=sys.stderr)
    merged = unary_union(land_geoms)
    prepared = prep(merged)

    print(f"Rasterizing {rows}x{cols} grid at {res}° resolution...", file=sys.stderr)
    grid = np.zeros((rows, cols), dtype=np.uint8)

    t0 = time.time()
    total = rows * cols
    checked = 0

    # Test a 3x3 sub-grid within each cell. If ANY sub-point is land,
    # mark the cell as land. This avoids missing coastal cells where the
    # cell center falls just offshore (e.g., SF peninsula).
    offsets = [0.17, 0.5, 0.83]  # sub-grid positions within cell (0-1)

    for row in range(rows):
        for col in range(cols):
            is_land = False
            for yo in offsets:
                if is_land:
                    break
                lat = 90.0 - (row + yo) * res
                for xo in offsets:
                    lng = -180.0 + (col + xo) * res
                    if prepared.contains(Point(lng, lat)):
                        is_land = True
                        break
            if is_land:
                grid[row, col] = 1

        checked += cols
        if (row + 1) % 180 == 0:
            elapsed = time.time() - t0
            pct = checked / total * 100
            rate = checked / elapsed if elapsed > 0 else 0
            print(f"  {pct:.0f}% ({row+1}/{rows} rows, {rate:.0f} pts/s)", file=sys.stderr)

    elapsed = time.time() - t0
    land_cells = np.sum(grid)
    print(f"Done in {elapsed:.1f}s. Land cells: {land_cells} / {total} ({land_cells/total*100:.1f}%)", file=sys.stderr)

    return grid


def validate_grid(grid, res=0.25):
    """Validate known land/water points."""
    def check(lat, lng, expected_name, expected_land):
        row = int((90 - lat) / res)
        col = int((lng + 180) / res)
        row = max(0, min(grid.shape[0] - 1, row))
        col = max(0, min(grid.shape[1] - 1, col))
        actual = bool(grid[row, col])
        status = "OK" if actual == expected_land else "FAIL"
        print(f"  {status}: {expected_name} ({lat}, {lng}) = {'land' if actual else 'water'} (expected {'land' if expected_land else 'water'})", file=sys.stderr)
        return actual == expected_land

    print("Validating known points:", file=sys.stderr)
    all_ok = True
    all_ok &= check(37.77, -122.42, "San Francisco", True)
    all_ok &= check(20.0, -160.0, "Mid-Pacific", False)
    all_ok &= check(35.68, 139.69, "Tokyo", True)
    all_ok &= check(19.7, -155.5, "Hawaii Big Island", True)
    all_ok &= check(51.5, -0.12, "London", True)
    all_ok &= check(0.0, -30.0, "Mid-Atlantic", False)
    all_ok &= check(-33.87, 151.21, "Sydney", True)
    all_ok &= check(21.31, -157.86, "Honolulu", True)
    all_ok &= check(0.0, 0.0, "Gulf of Guinea", False)

    if all_ok:
        print("All validation checks passed!", file=sys.stderr)
    else:
        print("WARNING: Some validation checks failed!", file=sys.stderr)

    return all_ok


def bitpack(grid):
    """Pack boolean grid into bytes (8 cells per byte, MSB-first)."""
    flat = grid.flatten()
    # Pad to multiple of 8
    padded_len = (len(flat) + 7) // 8 * 8
    padded = np.zeros(padded_len, dtype=np.uint8)
    padded[:len(flat)] = flat

    # Pack 8 bits per byte
    packed = np.zeros(padded_len // 8, dtype=np.uint8)
    for bit in range(8):
        packed |= padded[bit::8] << (7 - bit)

    return packed


def rle_encode(data):
    """RLE encode: byte pairs [value, count], max count 255."""
    result = bytearray()
    i = 0
    while i < len(data):
        value = data[i]
        count = 1
        while i + count < len(data) and data[i + count] == value and count < 255:
            count += 1
        result.append(value)
        result.append(count)
        i += count
    return bytes(result)


def main():
    rows, cols, res = 1800, 3600, 0.1

    grid = generate_grid(rows, cols, res)
    validate_grid(grid, res)

    print("Bitpacking...", file=sys.stderr)
    packed = bitpack(grid)
    print(f"  Packed size: {len(packed)} bytes", file=sys.stderr)

    print("RLE encoding...", file=sys.stderr)
    rle = rle_encode(packed)
    print(f"  RLE size: {len(rle)} bytes ({len(rle)/len(packed)*100:.1f}% of packed)", file=sys.stderr)

    print("Base64 encoding...", file=sys.stderr)
    b64 = base64.b64encode(rle).decode('ascii')
    print(f"  Base64 size: {len(b64)} chars", file=sys.stderr)

    # Output JavaScript constant
    print(f'const LAND_BITMAP_RLE_B64 = "{b64}";')
    print(f"  Output: {len(b64)} character JS constant", file=sys.stderr)


if __name__ == '__main__':
    main()
