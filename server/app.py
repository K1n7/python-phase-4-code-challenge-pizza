#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from sqlalchemy.exc import IntegrityError

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


class RestaurantsResource(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return [r.to_dict(only=("id", "name", "address")) for r in restaurants], 200


class RestaurantByIdResource(Resource):
    def get(self, id):
        restaurant = Restaurant.query.get(id)
        if not restaurant:
            return {"error": "Restaurant not found"}, 404

       
        data = restaurant.to_dict(only=("id", "name", "address"))
        data["restaurant_pizzas"] = [rp.to_dict() for rp in restaurant.restaurant_pizzas]
        return data, 200

    def delete(self, id):
        restaurant = Restaurant.query.get(id)
        if not restaurant:
            return {"error": "Restaurant not found"}, 404

        db.session.delete(restaurant)
        db.session.commit()
        return "", 204


class PizzasResource(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return [p.to_dict() for p in pizzas], 200


class RestaurantPizzasResource(Resource):
    def post(self):
        data = request.get_json()

        price = data.get("price")
        pizza_id = data.get("pizza_id")
        restaurant_id = data.get("restaurant_id")

        errors = []

        
        if price is None:
            errors.append("Price is required")
        elif not isinstance(price, int) or price < 1 or price > 30:
            errors.append("Price must be an integer between 1 and 30")

        
        pizza = Pizza.query.get(pizza_id)
        if not pizza:
            errors.append("Pizza not found")

        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            errors.append("Restaurant not found")

        if errors:
            return {"errors": errors}, 400

        try:
            new_rp = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
            db.session.add(new_rp)
            db.session.commit()
            return new_rp.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"errors": ["Validation errors"]}, 400



api.add_resource(RestaurantsResource, "/restaurants")
api.add_resource(RestaurantByIdResource, "/restaurants/<int:id>")
api.add_resource(PizzasResource, "/pizzas")
api.add_resource(RestaurantPizzasResource, "/restaurant_pizzas")


if __name__ == "__main__":
    app.run(port=5555, debug=True)
