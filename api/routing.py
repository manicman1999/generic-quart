import json
from quart import Quart
from api.abstractEntity.abstractController import AbstractController
from api.auth.authController import AuthController
from api.users.userController import UserController


def addRoutes(app: Quart):
    controllers: list[AbstractController] = [
        UserController(),
        AuthController(),
    ]

    for controller in controllers:
        app.register_blueprint(controller.blueprint)

    registryData = [
        {controller.controllerName: [r.toDict() for r in controller.routeRegistry]}
        for controller in controllers
    ]
    with open("registry.json", "w") as f:
        jsonString = json.dumps(registryData, indent=4)
        f.write(jsonString)
