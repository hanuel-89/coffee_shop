from crypt import methods
import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
# db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:
        drinks = Drink.query.order_by(Drink.id).all()
        if len(drinks) == 0:
            abort(404)

        drinks = [drink.short() for drink in drinks]
        return jsonify(
            {
                'success': True,
                'drinks': drinks
            }
        )
    except Exception:
        abort(422)


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail():
    try:
        drinks = Drink.query.order_by(Drink.id).all()
        if len(drinks) == 0:
            abort(404)

        formatted_drinks = [drink.long() for drink in drinks]
        return jsonify(
            {
                'success': True,
                'drinks': formatted_drinks
            }
        )
    except Exception:
        abort(422)

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drinks():
    try:
        body = request.get_json()  # Get the json from the frontend
        new_title = body.get('title')  # Get the new drink's title
        new_recipe = body.get('recipe')  # Get the new drink's recipe

        # Create an instance of the new drink and insert into the db
        new_drink = Drink(title=new_title, recipe=new_recipe)
        new_drink.insert()

        return jsonify(
            {
                'success': True,
                'drinks': new_drink.long()
            }
        )
    except Exception:
        abort(422)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(id):
    try:
        drink_to_patch = Drink.query.filter_by(Drink.id==id).one_or_none()
        if drink_to_patch is None:
            abort(404)
        body = request.get_json()
        drink_to_patch.title = body.get('title')
        drink_to_patch.recipe = body.get('recipe')
        drink_to_patch.update()

        return jsonify(
            {
                'success': True,
                'drinks': drink_to_patch.long()
            }
        )
    except Exception:
        abort(422)

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:id>')
@requires_auth('delete:drinks')
def delete_drink(id):
    try:
        drink_to_delete = Drink.query.filter_by(Drink.id == id).one_or_none()
        if drink_to_delete is None:
            abort(404)
        drink_to_delete.delete()
        return json(
            {
                'success': True,
                'delete': id
            }
        ), request.status_code()
    except Exception:
        abort(422)

# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify(
        {
            'success': False,
            'error': 422,
            'message': 'unprocessable'
        }
    ), 422

@app.errorhandler(404)
def not_found(error):
    return jsonify(
        {
            'success': False,
            'error': 404,
            'message': "resource not found"
        }
    ), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify(
        {
            'success': False,
            'error': 400,
            'message': 'bad request'
        }
    ), 400

@app.errorhandler(401)
def auth_error(error):
    return jsonify(
        {
            'success': False,
            'error': 401,
            'message': 'authorization error'
        }
    )
