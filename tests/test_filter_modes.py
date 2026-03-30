import os
import sys
from typing import List

# Add the parent directory to sys.path so we can import 'core'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.settings import AppSettings
from core.parser import parse_line, LogEntry
from core.filter import LogFilter

def run_filter_test(settings: AppSettings, lines: List[str]) -> List[LogEntry]:
    """Helper function to run the filter for a given settings object."""
    log_filter = LogFilter(settings)
    valid_entries = []
    for line in lines:
        entry = parse_line(line)
        if entry and log_filter.is_valid(entry):
            valid_entries.append(entry)
    return valid_entries

def test_filter_modes():
    log_path = os.path.join(os.path.dirname(__file__), "..", "test_log.txt")
    
    if not os.path.exists(log_path):
        print(f"FATAL: test_log.txt not found at {log_path}")
        return

    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    print("--- Filter Modes Test Suite ---")

    # --- Test Case 1: Filter for FREE entries ---
    print("
[TEST 1: Filter FREE]")
    settings_free = AppSettings(free_filter_mode="free")
    free_results = run_filter_test(settings_free, lines)
    print(f"Expected 2, Found {len(free_results)} free entries.")
    for entry in free_results:
        print(f"  -> OK: {entry.url} (Flag: '{entry.free_flag}', Meta: '{entry.meta_raw}')")
    # Basic assertion
    assert len(free_results) == 2
    assert "artist1" in free_results[0].url
    assert "artist6" in free_results[1].url

    # --- Test Case 2: Filter for PAID entries ---
    print("
[TEST 2: Filter PAID]")
    settings_paid = AppSettings(free_filter_mode="paid")
    paid_results = run_filter_test(settings_paid, lines)
    print(f"Expected 2, Found {len(paid_results)} paid entries.")
    for entry in paid_results:
        print(f"  -> OK: {entry.url} (Flag: '{entry.free_flag}', Meta: '{entry.meta_raw}')")
    # Basic assertion
    assert len(paid_results) == 2
    assert "artist2" in paid_results[0].url
    assert "artist5" in paid_results[1].url

    # --- Test Case 3: Filter for ALL entries ---
    print("
[TEST 3: Filter ALL]")
    settings_all = AppSettings(free_filter_mode="all")
    all_results = run_filter_test(settings_all, lines)
    print(f"Expected 4, Found {len(all_results)} entries.")
    for entry in all_results:
        print(f"  -> OK: {entry.url} (Flag: '{entry.free_flag}', Meta: '{entry.meta_raw}')")
    # Basic assertion
    assert len(all_results) == 4

    # --- Test Case 4: Min/Max Tracks ---
    print("
[TEST 4: Filter with Track Count (min=10, max=15)]")
    settings_tracks = AppSettings(free_filter_mode="all", min_tracks=10, max_tracks=15)
    track_results = run_filter_test(settings_tracks, lines)
    print(f"Expected 2, Found {len(track_results)} entries.")
    for entry in track_results:
        print(f"  -> OK: {entry.url} (Tracks: {entry.track_count})")
    assert len(track_results) == 2
    assert "artist2" in track_results[0].url
    assert "artist5" in track_results[1].url
    
    print("
--- All tests completed ---")

if __name__ == "__main__":
    test_filter_modes()
