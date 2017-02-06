from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret-key'

db = SQLAlchemy(app)

# Models
class InventoryModel(db.Model):
    __tablename__ = 'inventories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __init__(self, name):
        self.name = name

    def json(self):
        return {
            "name": self.name,
            "items": [item.json() for item in self.items]
        }


class ItemModel(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    quantity = db.Column(db.Integer)

    inventory_id = db.Column(db.Integer, db.ForeignKey('inventories.id'))
    inventory = db.relationship('InventoryModel',
        backref=db.backref('items', cascade='all, delete-orphan', lazy='dynamic')
    )

    def __init__(self, name, quantity, inventory_id):
        self.name = name
        self.quantity = quantity
        self.add_inventory(inventory_id)

    def add_inventory(self, inventory_id):
        inventory = InventoryModel.query.filter_by(id=inventory_id).first()
        self.inventory = inventory

    def json(self):
        return {
            "name": self.name,
            "quantity": self.quantity,
            "stocked_in": self.inventory.name
        }


# Resources
class InventoryList(Resource):
    def get(self):
        inventories = InventoryModel.query.all()

        return [inventory.json() for inventory in inventories]

    def post(self):
        data = request.get_json()
        inventory = InventoryModel(data['name'])
        db.session.add(inventory)
        db.session.commit()

        return inventory.json()


class ItemList(Resource):
    def get(self, inventory_id):
        items = ItemModel.query.filter_by(inventory_id=inventory_id)

        return [item.json() for item in items]

    def post(self, inventory_id):
        data = request.get_json()
        item = ItemModel(data['name'], data['quantity'], inventory_id)
        db.session.add(item)
        db.session.commit()

        return item.json()


api = Api(app)
api.add_resource(InventoryList, '/inventories')
api.add_resource(ItemList, '/inventories/<int:inventory_id>/items')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
