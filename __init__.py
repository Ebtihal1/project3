#!/usr/bin/env python3

from flask import Flask, render_template, request 
from flask import redirect, jsonify, url_for, flash  
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, CatalogItem, ItemDetail, User
from sqlalchemy import desc
from flask import session as login_session
from flask import make_response
import random
import string
import json
import httplib2
import requests
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError


app = Flask(__name__)

# load google sign-in API Client-id server path /var/www/catalog/catalog/

CLIENT_ID = json.loads(open('/var/www/catalog/catalog/client_secrets.json', 'r').read())['web']['client_id']

# Connect to Postgresql database username:catalog password:password

engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.bind = engine

# Create database session

DBSession = sessionmaker(bind=engine)
session = DBSession()

# User Helper Functions

def createUser(login_session):

    new_user = User(email=login_session['email'], 
                    picture=login_session['picture'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):

    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):

    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# JSON API

@app.route('/catalog/<int:catalog_id>/item/JSON')
def catagoryJSON(catalog_id):

    catagory = session.query(CatalogItem).filter_by(id=catalog_id).one()
    items = session.query(ItemDetail).filter_by(
        catalog_id=catalog_id).all()
    return jsonify(ItemDetail=[i.serialize for i in items])


@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/JSON')
def itemJSON(catalog_id, item_id):

    item_detail = session.query(ItemDetail).filter_by(id=item_id).one()
    return jsonify(item_detail=item_detail.serialize)


@app.route('/catalog/JSON')
def catagorysJSON():

    catagorys = session.query(CatalogItem).all()
    return jsonify(catagorys=[c.serialize for c in catagorys])


# Show all catalogs and Latest 5 items

@app.route('/')
@app.route('/catalog/')
def showcatalogs():
    
    catalogs = session.query(CatalogItem).all()
    items = session.query(ItemDetail).order_by(desc(ItemDetail.id)).limit(5)

    return render_template('main.html', catalogs=catalogs, items=items)


# Create a new catalog

@app.route('/catalog/new/', methods=['GET', 'POST'])
def newcatalog():

    if 'email' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        new = CatalogItem(name=request.form['name'],
                         user_id=login_session['user_id'])
        session.add(new)
        session.commit()
        flash("New Catalog added")
        return redirect(url_for('showcatalogs'))
    else:
        return render_template('newcatalog.html')

# Show item list

@app.route('/catalog/<int:catalog_id>/')
@app.route('/catalog/<int:catalog_id>/item/')
def showitem(catalog_id):

    catagory = session.query(CatalogItem).filter_by(id=catalog_id).one()
    items = session.query(ItemDetail).filter_by(catalog_id=catalog_id).all()

    return render_template('item.html', catagory=catagory, items=items)

# Show item detail

@app.route('/catalog/<int:catalog_id>/item/<int:item_id>')
def showdetailitem(catalog_id, item_id):

    catagory = session.query(CatalogItem).filter_by(id=catalog_id).one()
    item = session.query(ItemDetail).filter_by(id=item_id).one()

    return render_template('detailitem.html', catagory=catagory, item=item)

# Create a new item

@app.route(
    '/catalog/<int:catalog_id>/item/new/', methods=['GET', 'POST'])
def newitem(catalog_id):
    
    catagory = session.query(CatalogItem).filter_by(id=catalog_id).one()
    categories = session.query(CatalogItem).all()

    if 'email' not in login_session:
        return redirect('/login')
   
    if request.method == 'POST':
        newi = ItemDetail(name=request.form['name'], 
                          description=request.form['description'], 
                          catalog_id=request.form['category'],
                          user_id=login_session['user_id'])
        session.add(newi)
        session.commit()
        flash("New item added")

        return redirect(url_for('showitem', catalog_id=catalog_id))
    else:
        return render_template('newitem.html', catalog_id=catalog_id, 
                                catagory=catagory, 
                                categories=categories)


# Edit item

@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/edit',
           methods=['GET', 'POST'])
def edititem(catalog_id, item_id):

    if 'email' not in login_session:
        return redirect('/login')

    edit_item = session.query(ItemDetail).filter_by(id=item_id).one()
    catagory = session.query(CatalogItem).filter_by(id=catalog_id).one()
    categories = session.query(CatalogItem).all()

    # Check if the user creat the item same user edit it 
    if edit_item.user_id != login_session['user_id']:
        return "You are not authorized to edit item"

    if request.method == 'POST':
        if request.form['name']:
            edit_item.name = request.form['name']
        if request.form['description']:
            edit_item.description = request.form['description']
        if request.form['category']:
            edit_item.catalog_id = request.form['category']
        
        session.add(edit_item)
        session.commit()
        flash("Item updated !")
        return redirect(url_for('showitem', catalog_id=edit_item.catalog_id, 
                                item_id=edit_item.id))
    else:
        return render_template('edit.html', catalog_id=catalog_id, item_id=item_id, 
                                item=edit_item, 
                                categories=categories)


# Delete item

@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteitem(catalog_id, item_id):

    if 'email' not in login_session:
        return redirect('/login')

    delete_item = session.query(ItemDetail).filter_by(id=item_id).one()
    catagory = session.query(CatalogItem).filter_by(id=catalog_id).one()

    # Check if the user creat the item same user delete it 
    if delete_item.user_id != login_session['user_id']:
        return "You are not authorized to edit item"

    if request.method == 'POST':
        session.delete(delete_item)
        session.commit()
        flash("Item deleted !")
        return redirect(url_for('showitem', catalog_id=catalog_id))
    else:
        return render_template('delete.html', item=delete_item)

# Create anti-forgery state token

@app.route('/login')
def login():

    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state

    return render_template('login.html', STATE=state)


@app.route('/logout')
def logout():

    if 'email' in login_session:
        gdisconnect()
        del login_session['gplus_id']
        del login_session['access_token']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have been successfuly logout..")
        return redirect(url_for('showcatalogs'))

# Connect to google sign-in oAuth

@app.route('/gconnect', methods=['POST'])
def gconnect():

    # Validate anti-forgery state token

    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code

    code = request.data

    try:
        # Upgrade the authorization code into a credentials object

        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
            response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

    # Check that the access token is valid.

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.

    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['email'] = data['email']
    login_session['picture'] = data['picture']
    login_session['provider'] = 'google'

    # Check if user exists

    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    return "Login Successful"

# Disconnect google account

@app.route('/gdisconnect')
def gdisconnect():

    # Only disconnect a connected user.

    access_token = login_session.get('access_token')

    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] != '200':
        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response
# change app.run from local host to domain public IP address and the port 80
if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'super_secret_key'
    app.run(host='45.33.56.207', port=80)
