"""Generate statistics from ctags JSON output."""
import json
import sys
from pathlib import Path
from collections import defaultdict

def main(timestamp):
    tags_file = Path('.tags.json')
    stats = defaultdict(lambda: defaultdict(int))
    total = 0
    files = set()

    try:
        with open(tags_file, encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get('_type') != 'tag':
                        continue

                    lang = data.get('language', 'Unknown')
                    kind = data.get('kind', 'other')
                    path = data.get('path', '')

                    stats[lang][kind] += 1
                    total += 1
                    files.add(path)
                except:
                    continue

        # Write statistics
        output = {
            'generated': timestamp,
            'total_symbols': total,
            'files_analyzed': len(files),
            'by_language': {}
        }

        for lang in sorted(stats.keys()):
            output['by_language'][lang] = dict(stats[lang])

        output_file = Path('docs/codemap/statistics.json')
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)

        print(f'[SUCCESS] Statistics: {output_file}')
        print()
        print('Summary:')
        print(f'  Total symbols: {total}')
        print(f'  Files analyzed: {len(files)}')
        print(f'  Languages: {len(stats)}')
        print()
        print('By Language:')
        for lang in sorted(stats.keys()):
            count = sum(stats[lang].values())
            print(f'  {lang}: {count} symbols')

    except Exception as e:
        print(f'[ERROR] Failed to generate statistics: {e}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    timestamp = sys.argv[1] if len(sys.argv) > 1 else 'unknown'
    main(timestamp)
