from quart import Quart
from quart_cors import cors
from quart_jwt_extended import JWTManager
from api.routing import addRoutes

app = Quart(__name__)
app = cors(app, allow_origin="*")

app.config["JWT_SECRET_KEY"] = "supersecretz"
jwt = JWTManager(app)

addRoutes(app)

if __name__ == "__main__":
    app.run(debug=False)
