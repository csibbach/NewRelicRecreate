#!/bin/env python
import newrelic.agent
newrelic.agent.initialize()
import eventlet
eventlet.monkey_patch()

from flask_injector import FlaskInjector
from injector import Injector, singleton, inject, Module
from flask_socketio import SocketIO
from flask import Flask, Response, current_app, request, Blueprint, jsonify
from functools import partial, wraps
from typing import Callable

def decorator_shoehorn(decorator, injection):
    def new_decorator(*args, **kwargs):
        def wrapper(handler):
            if getattr(handler, f'_wrapped_{injection}', False):
                return decorator(*args, **kwargs)(handler)
            setattr(handler, f'_wrapped_{injection}', True)
            _injection = partial(injection, handler)
            wraps(handler)(_injection)
            return decorator(*args, **kwargs)(_injection)
        return wrapper
    return new_decorator

def always_jsonify(handler: Callable, *args, **kwargs):
    result = handler(*args, **kwargs)

    return jsonify(result)

rest = Blueprint(__name__, __name__)

rest.route = decorator_shoehorn(rest.route, always_jsonify)

socketio = SocketIO()

@singleton
class SomeServiceToInject:
    @inject
    def __init__(self):
        pass

    def some_func(self)->str:
        return "some_func called!"

class MyModule(Module):
    def configure(self, binder):
        binder.bind(SomeServiceToInject)
   


def create_app(debug=False, no_redis=False) -> Flask:
    """Create an application."""
    app = Flask(__name__, instance_relative_config=True)

    app.register_blueprint(rest, url_prefix='/')

    socketio.init_app(app,
                    cors_allowed_origins="*",
                    async_mode='eventlet',
                    ping_timeout=30,
                    ping_interval=10,
                    monitor_client=True)

    my_injector = Injector(auto_bind=False)

    FlaskInjector(
        app=app,
        injector=my_injector,
        modules=[MyModule()],
    )

    return app

@rest.route("/test", methods=["GET"])
def test_route(some_service: SomeServiceToInject):
    return some_service.some_func()

if __name__ == '__main__':
    app = create_app()

    socketio.run(app=app,
                 host='0.0.0.0',
                 port=8080,
                 log_output=False,
                 debug=False)
