
from app import create_app

app = create_app()


class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        prefix = "/api/index"

        if path == prefix:
            environ["PATH_INFO"] = "/"
        elif path.startswith(prefix + "/"):
            environ["PATH_INFO"] = path[len(prefix):]

        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
