import csv

from staticjinja import Renderer


def parse_csv(filename):
    """Parse a CSV into a list."""
    with open(filename, 'rbU') as f:
        return list(csv.DictReader(f))


def index():
    players = parse_csv('data/players.csv')
    return {
        'players': sorted(players, key=lambda p: int(p['score']), reverse=True)
    }


if __name__ == "__main__":
    renderer = Renderer(contexts=[
        ('index.html', index),
    ])
    renderer.run(debug=True, use_reloader=True)
