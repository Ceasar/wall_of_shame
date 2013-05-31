import csv
import collections

from staticjinja import Renderer


def parse_csv(filename):
    """Parse a CSV into a list."""
    with open(filename, 'rbU') as f:
        for line in csv.DictReader(f):
            yield line


def index():
    counter = collections.defaultdict(list)
    for player in parse_csv('data/players.csv'):
        counter[player['name']].append({
            'file': player['file'],
            'line': player['line']
        })

    players = ({'name': k, 'score': len(v), 'methods': sorted(v)}
               for k, v in counter.iteritems())
    return {
        'players': sorted(players,
                          key=lambda p: int(p['score']), reverse=True)
    }


if __name__ == "__main__":
    renderer = Renderer(contexts=[
        ('index.html', index),
    ])
    renderer.run(debug=True, use_reloader=True)
