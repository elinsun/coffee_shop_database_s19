#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for, session
from flask_sqlalchemy import SQLAlchemy

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = os.urandom(24)


# XXX: The Database URI should be in the format of:
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "ys2780"
DB_PASSWORD = "px1YI73YHb"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass



@app.route('/', methods=['GET', 'POST'])
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """
  print request.args

  if not session.get('logged_in'):
    return render_template('index.html')

  else:
  # cursor = g.conn.execute("SELECT name FROM test")
  # names = []
  # for result in cursor:
  #   names.append(result['name'])
  # cursor.close()
    name = [session['name']]
    context = dict(username = name)
    return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
#
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/menu', methods=['GET'])
def menu(shop=None):
  shopid = request.args.get('shop')
  shop_cursor = g.conn.execute("SELECT shopid, address FROM shop")
  shops = []
  for result in shop_cursor:
    shops.append(result)
  shop_cursor.close()

  sql = 'SELECT itemname, price FROM menu, shop WHERE shop.shopid=menu.shopid and shop.shopid = (:id)'
  menu_cursor = g.conn.execute(text(sql), id = shopid)
  menu = []
  for result in menu_cursor:
    menu.append(result)
  menu_cursor.close()

  context = dict(shop_data = shops,
                menu_data = menu)

  return render_template("menu.html", **context)


@app.route('/signin', methods=['GET', 'POST'])
def signin():
  if request.method == 'GET':
		return render_template("signin.html")
  else:
    email = request.form['email']
    password = request.form['password']

    print email
    print password

    try:
      # sql = "SELECT * FROM customer WHERE customerid=(:id) and password=(:passw)"
      # data = {'id': int(username), 'passw': password}

      sql = "SELECT * FROM customer WHERE email=(:email) and password=(:passw)"
      data = {'email': email, 'passw': password}
      customer_cursor = g.conn.execute(text(sql), data)

      user = []
      for result in customer_cursor:
        for info in result:
          user.append(str(info))
      customer_cursor.close()

      print user
      # If a customer logged in
      if user:
        session['logged_in'] = True
        session['user'] = 'customer'
        session['id'] = user[0]
        session['name'] = user[1]
        session['type'] = user[4]

        print session['name']
        return redirect(url_for('index'))

      else:
        sql = "SELECT * FROM staff WHERE email=(:email) and password=(:passw)"
        data = {'email': email, 'passw': password}
        staff_cursor = g.conn.execute(text(sql), data)

        user = []
        for result in staff_cursor:
          for info in result:
            user.append(str(info))
        staff_cursor.close()

        print user

        #If a staff logged in
        if user:
          session['logged_in'] = True
          session['user'] = 'staff'
          session['id'] = user[0]
          session['name'] = user[1]
          session['type'] = user[4]
          return redirect(url_for('index'))
    except:
      return "WRONG PASSWORD"

@app.route('/signup', methods=['GET', 'POST'])
def signup():
  if request.method == 'POST':
    max_id_sql = text('select max(customerid) from customer')
    max_id_cursor = g.conn.execute(max_id_sql)
    max_id = int(max_id_cursor.next()[0])

    max_id_cursor.close()

    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']
    password = request.form['password']

    sql = text("insert into customer values((:id), (:fn), (:ln), (:email), 'bronze', (:password))")
    data = {'id': max_id+1, 'fn': firstname, 'ln': lastname, 'email': email, 'password': password}

    cursor = g.conn.execute(sql, data)

    return render_template('signin.html')
  return render_template('signup.html')


@app.route("/logout")
def logout():
  session['logged_in'] = False
  session.pop("id")
  session.pop("user")
  session.pop("name")
  session.pop("type")
  return redirect(url_for('index'))


@app.route('/activity')
def activity():
  sql = 'SELECT itemname, price FROM menu, shop WHERE shop.shopid=menu.shopid and shop.shopid = (:id)'
  act_cursor = g.conn.execute(text(sql), id = shopid)
  activity = []
  for result in menu_cursor:
    activity.append(act_cursor)
  menu_cursor.close()

  context = dict(shop_data = shops,
                menu_data = menu)

  return render_template("activity.html", **context)


@app.route('/rewards')
def rewards():
  return render_template("rewards.html")

@app.route('/profile')
def profile():
  customerid = session["id"]

  dates_sql = text("SELECT date_part('day', now() - timestamp)::int \
                    FROM orders \
                    WHERE customerid = (:id)\
                    ORDER by timestamp\
                    LIMIT 1;")

  dates_cursor = g.conn.execute(dates_sql, id = customerid)

  dates = 0
  for row in dates_cursor:
    dates = row

  print dates

  dates_cursor.close()

  food_sql = text("SELECT menu.itemname\
                  FROM orders left join contain on orders.orderid = contain.orderid\
                  left join menu on menu.itemid = contain.itemid\
                  WHERE orders.customerid = (:id)\
                  GROUP BY contain.itemid, menu.itemname\
                  ORDER BY count(*) DESC\
                  LIMIT 1;")

  food_cursor = g.conn.execute(food_sql, id = customerid)

  food = ""
  for row in food_cursor:
    food = row

  food_cursor.close()

  pur_sql = text("select sum(cnt)/count(distinct(month))::float as average_purchase\
                  from(\
                      SELECT month::int, count(*) as cnt\
                      FROM (\
                          SELECT distinct orderid, extract(month from timestamp) as month\
                          FROM orders\
                          WHERE customerid=(:id)) t1\
                      GROUP BY month) t2")

  pur_cursor = g.conn.execute(pur_sql, id = customerid)

  purchase = 0
  for row in pur_cursor:
    if row[0]:
      purchase = row[0]

  pur_cursor.close()

  return render_template("profile.html", date_data = dates, fav_food_data = food, purchase_data = int(purchase))



@app.route('/menu_staff')
def menu_staff():
  return render_template("menu_staff.html")

@app.route('/stock')
def stock():
  staffid = session["id"]

  sql = 'SELECT stock_name, unit_price, quantity\
                FROM Stock\
                WHERE shopid = (select shopid from Staff where staffid = (:id))'

  stock_cursor = g.conn.execute(text(sql), id = staffid)
  stock = []
  for result in stock_cursor:
    stock.append(result)
  stock_cursor.close()
  context = dict(stock_data = stock)

  return render_template("stock.html", **context)


@app.route('/orders')
def orders():
  if not session.get('logged_in'):
    return render_template('index.html')

  staffid = session['id']
  sql = text(
    "with total(orderid, total_price, shopid) as\
      (select orderid, sum(quantity*price), contain.shopid\
      from contain\
      inner join menu\
      on contain.itemid = menu.itemid and contain.shopid::text = menu.shopid\
      group by orderid, contain.shopid)\
    select orderid, total_price\
    from total, staff\
    where staff.shopid = total.shopid\
    and staffid = (:staffid);")

  order_cursor = g.conn.execute(sql, staffid = staffid)
  record = []
  for result in order_cursor:
    record.append(result)
  order_cursor.close()

  name = [session['name']]

  context = dict(record = record, username = name)

  return render_template("orders.html", **context)

@app.route('/employee')
def employee():
  staffid = session["id"]

  sql = text('SELECT staff.staffid, staff.firstname, staff.lastname, staff.position, position.salary\
              FROM staff left join position on staff.position = position.position\
              WHERE staff.shopid = (select shopid from staff where staffid = (:id));')

  emp_cursor = g.conn.execute(sql, id = staffid)
  employee = []
  for result in emp_cursor:
    employee.append(result)

  emp_cursor.close()
  context = dict(employee_data = employee)
  return render_template("employee.html", **context)

@app.route('/summary')
def summary():
  return render_template("summary.html")



# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  print name
  cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
  g.conn.execute(text(cmd), name1 = name, name2 = name);
  return redirect('/')

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
