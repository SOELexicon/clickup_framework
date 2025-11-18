"""Display statistics from existing ctags output."""
import json
from pathlib import Path

def main():
    tags_file = Path('.tags.json')
    if not tags_file.exists():
        print('[ERROR] .tags.json not found. Run without --stats first.')
        exit(1)

    stats_file = Path('docs/codemap/statistics.json')
    if stats_file.exists():
        with open(stats_file) as f:
            stats = json.load(f)
        print(json.dumps(stats, indent=2))
    else:
        print('[ERROR] Run generate_codemap.bat to generate statistics first')
        exit(1)

if __name__ == '__main__':
    main()
