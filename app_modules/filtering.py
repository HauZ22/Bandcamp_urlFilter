from typing import List

from logic.bandcamp_filter import filter_entries


def get_download_link(data_list: List[dict]) -> str:
    qobuz_urls = [d["qobuz_url"] for d in data_list if d.get("qobuz_url")]
    return "\n".join(qobuz_urls)


def validate_filters(
    min_tracks,
    max_tracks,
    min_duration,
    max_duration,
    start_date,
    end_date,
) -> List[str]:
    errors = []
    if min_tracks is not None and max_tracks is not None and min_tracks > max_tracks:
        errors.append("Min Tracks must be less than or equal to Max Tracks.")
    if min_duration is not None and max_duration is not None and min_duration > max_duration:
        errors.append("Min Duration must be less than or equal to Max Duration.")
    if start_date and end_date and start_date > end_date:
        errors.append("Start Date must be on or before End Date.")
    return errors


def build_filtered_entries(lines: List[str], filter_config: dict, start_date, end_date):
    filtered_entries = filter_entries(lines, filter_config)

    if start_date or end_date:
        date_filtered_entries = []
        for entry in filtered_entries:
            if not entry.release_date:
                continue

            start_ok = not start_date or entry.release_date >= start_date
            end_ok = not end_date or entry.release_date <= end_date
            if start_ok and end_ok:
                date_filtered_entries.append(entry)

        filtered_entries = date_filtered_entries

    deduped_entries = []
    seen_urls = set()
    for entry in filtered_entries:
        key = entry.url.strip().lower()
        if key in seen_urls:
            continue
        seen_urls.add(key)
        deduped_entries.append(entry)

    return deduped_entries
