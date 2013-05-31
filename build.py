from staticjinja import Renderer


def index():
    knights = [
        'sir arthur',
        'sir lancelot',
        'sir galahad',
    ]
    return {'players': knights}


if __name__ == "__main__":
    renderer = Renderer(contexts=[
        ('index.html', index),
    ])
    renderer.run(debug=True, use_reloader=True)
