# Flask Setup

Flask is a lightweight, flexible web framework for Python, ideal for building REST APIs and web applications. It follows a microframework philosophy—minimal by default, extensible via extensions.

## Installation

Install Flask using pip:

```bash
pip install Flask
```

## Application Factory Pattern

For scalable projects, use an application factory to create your Flask app:

```python
from flask import Flask
import os

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'app.sqlite'),
    )
    if test_config:
        app.config.from_mapping(test_config)
    else:
        app.config.from_pyfile('config.py', silent=True)
    os.makedirs(app.instance_path, exist_ok=True)
    @app.route('/hello')
    def hello():
    return 'Hello, World!'
    return app
```

## Configuration Management

- Use environment variables for secrets and deployment-specific settings.
- Load configuration from files or environment using `app.config.from_envvar` or `from_prefixed_env`.

## Running the App

```bash
flask --app yourmodule:create_app run --debug
```

## Further Reading
- [Flask Official Documentation](https://flask.palletsprojects.com/)
- [Flask Application Factories](https://flask.palletsprojects.com/en/latest/patterns/appfactories/)