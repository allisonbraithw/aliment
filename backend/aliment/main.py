# import os
from dotenv import load_dotenv
from flask import Flask
from flask_graphql import GraphQLView
from flask_cors import CORS

from schema.schema import schema

load_dotenv()
# BASE_URL = os.getenv("BASE_URL")

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173","https://codenames.arb.haus"])
app.debug = True

app.add_url_rule(
    "/graphql",
    view_func=GraphQLView.as_view(
        "graphql",
        schema=schema,
        graphiql=True,
    ),
)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=4000)
