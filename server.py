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
    name = [session['name']]
    context = dict(username = name)
    return render_template("index.html", **context)


@app.route('/signin', methods=['GET', 'POST'])
def signin():
  if request.method == 'GET':
		return render_template("signin.html")

  else:
    email = request.form['email']
    password = request.form['password']

    try:
      sql = "SELECT * FROM customer WHERE email=(:email) and password=(:passw)"
      data = {'email': email, 'passw': password}
      customer_cursor = g.conn.execute(text(sql), data)

      user = []
      for result in customer_cursor:
        for info in result:
          user.append(str(info))
      customer_cursor.close()

      # If a customer logged in
      if user:
        session['logged_in'] = True
        session['user'] = 'customer'
        session['id'] = user[0]
        session['name'] = user[1]
        session['type'] = user[4]

        return redirect(url_for('index'))

      else:
        try:
          sql = "SELECT * FROM staff WHERE email=(:email) and password=(:passw)"
          data = {'email': email, 'passw': password}
          staff_cursor = g.conn.execute(text(sql), data)

          user = []
          for result in staff_cursor:
            for info in result:
              user.append(str(info))
          staff_cursor.close()

          #If a staff logged in
          if user:
            session['logged_in'] = True
            session['user'] = 'staff'
            session['id'] = user[0]
            session['name'] = user[1]
            session['type'] = user[4]
            return redirect(url_for('index'))

        except:
          return redirect(url_for('warning'))

    except:
      return redirect(url_for('warning'))

  return render_template("signin.html")


@app.route('/signin_warning')
def warning():
  if not session.get('logged_in'):
    return render_template('index.html')
  return render_template('signin_warning.html')


@app.route('/not_exist')
def not_exist():
  if not session.get('logged_in'):
    return render_template('index.html')
  return render_template('not_exist.html')


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
  if not session.get('logged_in'):
    return render_template('index.html')

  customerid = session["id"]

  sql = 'SELECT cast(orders.timestamp as date) as date, menu.itemname as itemname, menu.price as price, contain.quantity as quantity\
          FROM orders left join contain on orders.orderid=contain.orderid \
          left join menu on menu.shopid=contain.shopid and menu.itemid=contain.itemid\
          WHERE orders.customerid = (:id)\
          order by date'

  act_cursor = g.conn.execute(text(sql), id = customerid)
  activity = []
  for result in act_cursor:
    activity.append(result)
  act_cursor.close()

  return render_template("activity.html", act_data = activity, username=session["name"])


@app.route('/profile')
def profile():
  if not session.get('logged_in'):
    return render_template('index.html')

  customerid = session["id"]

  dates_sql = text("SELECT date_part('day', now() - timestamp)::int \
                    FROM orders \
                    WHERE customerid = (:id)\
                    ORDER by timestamp\
                    LIMIT 1;")

  dates_cursor = g.conn.execute(dates_sql, id = customerid)

  dates = 0
  for row in dates_cursor:
    dates = row[0]

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
    food = str(row[0])

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
      purchase = int(row[0])

  pur_cursor.close()

  sql_hist = text("SELECT year_month, sum(spend_per_order) as monthly_spend\
                  FROM(\
                      SELECT to_char(orders.timestamp, 'YYYY-MM') as year_month, \
                          menu.price as price,\
                          contain.quantity as units,\
                          (menu.price * contain.quantity) as spend_per_order\
                      FROM orders left join contain on orders.orderid=contain.orderid \
                              left join menu on menu.shopid=contain.shopid and menu.itemid=contain.itemid\
                      WHERE orders.customerid = (:id)) t\
                  GROUP BY year_month\
                  ORDER BY year_month")

  hist_cursor = g.conn.execute(sql_hist, id = session["id"])
  month = []
  amount = []
  for result in hist_cursor:
    month.append(str(result[0]))
    amount.append(result[1])
  hist_cursor.close()

  return render_template("profile.html", date_data = dates, fav_food_data = food, purchase_data = purchase,
                                        amount_data = amount, month_data = month, username = session["name"])


@app.route('/edit_menu', methods=['GET', 'POST'])
def edit_menu():

  if not session.get('logged_in'):
    return render_template('index.html')

  shop_sql = "SELECT shopid FROM staff WHERE staffid=(:id)"
  shop_cursor = g.conn.execute(text(shop_sql), id = session["id"])
  shopid = str(shop_cursor.next()[0])
  shop_cursor.close()

  # Insert orders to database
  if request.method == 'POST':

    itemname = request.form["input_itemname"]
    price = request.form["input_price"]

    max_id_sql = text('select max(itemid) from menu where shopid=(:id)')
    max_id_cursor = g.conn.execute(max_id_sql, id=shopid)
    max_id = int(max_id_cursor.next()[0])+1
    max_id_cursor.close()

    try:
      print shopid
      price = float(price)
      print price
      sql = text("insert into menu values ((:shopid), (:itemid), (:itemname), (:price))")
      data = {'shopid': shopid, 'itemid': max_id, 'itemname': itemname, 'price': price}
      cursor = g.conn.execute(sql, data)
      cursor.close()

    except:
      return redirect(url_for('edit_menu'))

  sql = 'SELECT distinct itemid, itemname, price\
        FROM menu\
        WHERE shopid=(:shopid)'

  menu_cursor = g.conn.execute(text(sql), shopid = shopid)
  menu = []
  for result in menu_cursor:
    menu.append(result)
  menu_cursor.close()

  context = dict(menu_data = menu, username = session["name"])

  return render_template("edit_menu.html", **context)



@app.route('/menu', methods=['GET', 'POST'])
def menu(shop=None):
  if not session.get('logged_in'):
    return render_template('index.html')

  shopid = request.args.get('shop')
  shop_cursor = g.conn.execute("SELECT shopid, address FROM shop")
  shops = []
  for result in shop_cursor:
    shops.append(result)
  shop_cursor.close()

  sql = 'SELECT itemid, itemname, price FROM menu, shop WHERE shop.shopid=menu.shopid and shop.shopid = (:id)'
  menu_cursor = g.conn.execute(text(sql), id = shopid)
  menu = []
  for result in menu_cursor:
    menu.append(result)
  menu_cursor.close()

  context = dict(shop_data = shops,
                menu_data = menu)

  if request.method == 'POST':

    max_id_sql = text('select max(orderid) from orders')
    max_id_cursor = g.conn.execute(max_id_sql)
    max_id = int(max_id_cursor.next()[0])+1
    max_id_cursor.close()

    print max_id

    customerid = session["id"]
    staffid = 9102000

    order_sql = text("insert into Orders values ((:orderid), (:customerid), (:staffid), now())")
    order_input = {"orderid": max_id, "customerid": customerid, "staffid": staffid}
    order_cursor = g.conn.execute(order_sql, order_input)
    order_cursor.close()

    for item in menu:
      form_name = str(item[0])
      print form_name
      if request.form[form_name] != "":
        quantity = int(request.form[form_name])
        print quantity
        contain_sql = text("insert into Contain values((:orderid), (:shopid), (:itemid), (:quantity))")

        contain_input = {"orderid": max_id, "shopid": shopid, "itemid": form_name, "quantity": quantity}
        contain_cursor = g.conn.execute(contain_sql, contain_input)
        contain_cursor.close()

  return render_template("menu.html", **context)



@app.route('/menu_staff', methods=['GET', 'POST'])
def menu_staff():

  if not session.get('logged_in'):
    return render_template('index.html')

  staffid = session["id"]
  shop_sql = "SELECT shopid FROM staff WHERE staffid=(:id)"
  shop_cursor = g.conn.execute(text(shop_sql), id = staffid)
  shopid = str(shop_cursor.next()[0])
  shop_cursor.close()

  sql = 'SELECT distinct itemid, itemname, price\
        FROM menu\
        WHERE shopid=(:shopid)'

  menu_cursor = g.conn.execute(text(sql), shopid = shopid)
  menu = []
  for result in menu_cursor:
    menu.append(result)
  menu_cursor.close()

  context = dict(menu_data = menu, username = session["name"])

  # Insert orders to database
  if request.method == 'POST':

    customerid = 2019000
    input_email = request.form["input_email"]

    if input_email != "":
      try:
        print input_email
        customer_sql = text("select customerid from customer where email = (:input)")
        customer_cursor = g.conn.execute(customer_sql, input=str(input_email))
        for row in customer_cursor:
          customerid = int(row[0])
        customer_cursor.close()

      except:
        return redirect(url_for('not_exist'))

    max_id_sql = text('select max(orderid) from orders')
    max_id_cursor = g.conn.execute(max_id_sql)
    max_id = int(max_id_cursor.next()[0])+1
    max_id_cursor.close()

    staffid = session["id"]

    counter = 0
    for item in menu:
      form_name = str(item[0])
      if request.form[form_name] != "":
        if counter == 0:
          order_sql = text("insert into Orders values ((:orderid), (:customerid), (:staffid), now())")
          order_input = {"orderid": max_id, "customerid": customerid, "staffid": staffid}
          order_cursor = g.conn.execute(order_sql, order_input)
          order_cursor.close()
          counter +=1

        quantity = str(request.form[form_name])

        contain_sql = text("insert into Contain values((:orderid), (:shopid), (:itemid), (:quantity))")

        contain_input = {"orderid": max_id, "shopid": shopid, "itemid": form_name, "quantity": quantity}
        contain_cursor = g.conn.execute(contain_sql, contain_input)
        contain_cursor.close()

  return render_template("menu_staff.html", **context)


@app.route('/stock')
def stock():
  if not session.get('logged_in'):
    return render_template('index.html')

  staffid = session["id"]

  sql = 'SELECT stock_name, unit_price, quantity\
                FROM Stock\
                WHERE shopid = (select shopid from Staff where staffid = (:id))'

  stock_cursor = g.conn.execute(text(sql), id = staffid)
  stock = []
  for result in stock_cursor:
    stock.append(result)
  stock_cursor.close()
  # context = dict(stock_data = stock)
  name = session['name']

  return render_template("stock.html",  username = name, stock_data = stock)


@app.route('/orders')
def orders():
  if not session.get('logged_in'):
    return render_template('index.html')

  sql = text("SELECT t.orderid as orderid, t.date as date, sum(t.cost) as total_price, t.customerid as customerid\
            FROM(\
                SELECT contain.orderid as orderid, \
                    cast(orders.timestamp as date) as date,\
                    contain.quantity*menu.price as cost, \
                    orders.customerid as customerid\
                FROM orders left join contain on orders.orderid=contain.orderid \
                        left join menu on menu.shopid=contain.shopid and menu.itemid=contain.itemid\
                WHERE contain.shopid = (SELECT shopid FROM Staff WHERE staffid = (:id))) t  \
            GROUP BY t.customerid, t.orderid, t.date\
            ORDER BY date")

  order_cursor = g.conn.execute(sql, id = session['id'])
  record = []
  for result in order_cursor:
    record.append(result)
  order_cursor.close()

  name = session['name']

  # context = dict(record = record)

  return render_template("orders.html", username = name, record = record)

@app.route('/employee')
def employee():
  if not session.get('logged_in'):

    return render_template('index.html')
  sql = text('SELECT staff.staffid, staff.firstname, staff.lastname, staff.position, position.salary\
              FROM staff left join position on staff.position = position.position\
              WHERE staff.shopid = (select shopid from staff where staffid = (:id));')

  emp_cursor = g.conn.execute(sql, id = session["id"])
  employee = []
  for result in emp_cursor:
    employee.append(result)
  emp_cursor.close()

  return render_template("employee.html", employee_data = employee, username=session['name'])

@app.route('/summary')
def summary():
  if not session.get('logged_in'):
    return render_template('index.html')

  sql_buy = text("SELECT concat(year,'-',month) as year_month, monthly_cost\
                  FROM(\
                      SELECT extract(month from buy.date)::int as month, \
                          extract(year from buy.date)::int as year,\
                          sum(total_price) as monthly_cost\
                      FROM buy \
                      WHERE shopid=(SELECT shopid FROM staff WHERE staffid=(:id)) \
                      GROUP BY month, year) t \
                  ORDER BY year, month")\

  pur_cursor = g.conn.execute(sql_buy, id = session["id"])
  month_pur = []
  amount_pur = []
  for result in pur_cursor:
    month_pur.append(str(result[0]))
    amount_pur.append(result[1])
  pur_cursor.close()

  sql_revenue = text("SELECT year_month, monthly_revenue\
              FROM(\
                  SELECT distinct extract(month from orders.timestamp)::int as month,\
                      sum(contain.quantity*menu.price) OVER (PARTITION BY extract(month from orders.timestamp)) as monthly_revenue,\
                      to_char(orders.timestamp, 'YYYY-MM') as year_month\
                  FROM orders left join contain on orders.orderid=contain.orderid \
                              left join menu on menu.shopid=contain.shopid and menu.itemid=contain.itemid\
                  WHERE contain.shopid = (SELECT shopid FROM Staff WHERE staffid = (:id))\
                  ORDER BY month) t\
               ORDER BY year_month;")\

  rev_cursor = g.conn.execute(sql_revenue, id = session["id"])
  month_rev = []
  amount_rev = []
  for result in rev_cursor:
    month_rev.append(str(result[0]))
    amount_rev.append(result[1])
  rev_cursor.close()

  return render_template("summary.html", pur_month_data = month_pur, pur_amount_data = amount_pur,
                        rev_month_data = month_rev, rev_amount_data = amount_rev, username=session["name"])



# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
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
