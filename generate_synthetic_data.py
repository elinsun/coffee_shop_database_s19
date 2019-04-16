import pandas as pd
import numpy as np
from datetime import datetime
from random import randint

### 1. Five base tables generated in excel: Customer, Staff, Shop, Position, Menu

# read excel files

with ib.open('Shop.csv') as f:
    Shop = pd.read_csv(f)
    
with ib.open('Staff.csv') as f:
    Staff = pd.read_csv(f)

with ib.open('Customer_toOrder.csv') as f:
    Customer_toOrder = pd.read_csv(f)

with ib.open('Position.csv') as f:
    Position = pd.read_csv(f)

with ib.open('Menu.csv') as f:
    Menu = pd.read_csv(f)

### 2. Four other tabls generated based on previous ones: Orders, Contain, Stock, Buy

### 1) Orders table - orderid, customerid, staffid, timestamp

"""""""""""""""""""""""""""
target number of orders
"""""""""""""""""""""""""""
num_item = len(set(Menu.itemid))
n = num_item * 200

start = 181900001 # orderid start number

"""""""""""""""""""""""""""
no need to modify below
"""""""""""""""""""""""""""
#### get unique(staff, customer)combination: assume each customer goes to only one shop
# join staff & customer based on shopid
order = pd.merge(Staff, Customer_toOrder, on='shopid')[['staffid', 'position','customerid']]
order = order.loc[order.position == 'cashier'].drop_duplicates().drop('position', axis=1)

# cross join ny area shop & customer
nystaff = Staff.loc[Staff.shopid < 107].loc[Staff.position == 'cashier']['staffid'] #ny cashiers
nycustomer = Customer_toOrder.loc[Customer_toOrder.shopid < 107]['customerid'] #ny customers

nystaff = len(set(nycustomer))*list(nystaff)
nycustomer = len(set(nystaff))*list(nycustomer)

nyorder = pd.DataFrame({'staffid' :nystaff, 'customerid':nycustomer})

# concat two df & get unique combination of (staff, customer)
orders = pd.concat([order, nyorder], axis=0).drop_duplicates().reset_index(drop=True)

# upsample
orders = orders.sample(n, replace=True).reset_index(drop=True)

# generate random timestamp 
i = 1
timestamp = []

# random time from 2018-07-01 to 2018-12-31
while i <= n:
    #year
    year = randint(2018, 2019) 
    
    #month
    if year == 2018:
        month = randint(7,12)
    else:
        month = randint(1,4)
    
    #day
    if month == 2:
        day = randint(1, 28)
    elif month == 4:
        day = randint(1, 15)
    elif month == 6 or month == 9 or month == 11:
        day = randint(1, 30)
    else:
        day = randint(1, 31)

    hh = randint(7, 16)
    mm = randint(1, 59)
    ss = randint(1, 59)

    a = datetime(year, month, day, hh, mm, ss).strftime("%Y-%m-%d %H:%M:%S")
    timestamp.append(a)
    i += 1
    
# generate orderid
orderid = list(range(start, start+n))

# convert to df
time_orderid = pd.DataFrame({'timestamp': timestamp, 'orderid':orderid})

# append timestamp and orderid 
allorder =pd.concat([orders, time_orderid], axis=1, ignore_index=True)

# rename & reorder
allorder.columns = ['customerid','staffid','orderid','timestamp']
allorder = allorder[['orderid', 'customerid', 'staffid', 'timestamp']]

# save to csv
with ib.open("Orders.csv", "w") as file:
    output = allorder.to_csv() # df must convert to df first
    file.write(output)
    
### 2) Contain table - orderid, shopid, itemid, quantity

# add shopid in the end
orderwithshop = pd.merge(allorder, Staff[['staffid', 'shopid']], on='staffid', how='left')
#orderwithshop.head()

# generate random itemid
rand_coffee = pd.DataFrame({'itemid':list(range(1, 7))}).sample(int(0.8*n), replace=True).reset_index()
rand_pastry = pd.DataFrame({'itemid':list(range(7, 16))}).sample(int(0.2*n), replace=True).reset_index()
itemid = pd.concat([rand_coffee, rand_pastry], axis=0).drop('index',axis=1).sample(frac=1).reset_index(drop=True)
# add itemid
orderwithshop = pd.concat([orderwithshop, itemid], axis=1)
orderwithshop.head()

# generate random quantity
q = pd.DataFrame({'quantity':[1,1,1,1,2]}).sample(n, replace=True).reset_index(drop=True)

# add quantity
orderwithshop = pd.concat([orderwithshop, q], axis=1)
orderwithshop.head()

# choose useful column for Contain table
contain = orderwithshop[['orderid', 'shopid', 'itemid', 'quantity']]

# check shopid + itemid is in Menu
menuhas = Menu[['shopid', 'itemid']]
containhas = pd.merge(menuhas, contain, on='shopid', how='left')
containhas = containhas.loc[containhas.itemid_x == containhas.itemid_y].drop('itemid_y', axis=1)

containhas.columns = ['shopid', 'itemid', 'orderid', 'quantity']
contain = containhas[['orderid', 'shopid', 'itemid', 'quantity']]
contain.head()

# export result
with ib.open("Contain.csv", "w") as file:
    output = contain.to_csv() # df must convert to df first
    file.write(output)
    

### 3) Stock table - shopid, stockid, stock_name, unit_price, quantity
stockname = ['coffee beans', 'milk', 'soymilk', 'almondmilk', 'oatmilk', 'flour', 'napkins', 'cups', 'straws', 'lids', 'sleeves']
stockid = list(range(10, len(stockname)+10))
unit_price = [2.09, 3.00, 4.89, 4.79, 5.09, 13.13, 10, 3.05, 5.00, 0.05, 0.01]
quantity =   [200, 30, 30, 30, 30, 15, 20, 10, 10, 200, 300]

# combine 3 cols to df
stock = pd.DataFrame({'stockid': stockid, 'stock_name': stockname, 'unit_price': unit_price, 'quantity': quantity})

# each shop has the same stock (for simplicity reason)
shopid = np.repeat(list(range(101, 111)), len(stockid))
ind = list(range(len(stockid)))*len(set(shopid))

# repeat each shopid
stock = stock.iloc[ind].reset_index(drop=True)
stock['shopid'] = shopid

# re-order columns
stock = stock[['shopid', 'stockid', 'stock_name', 'unit_price', 'quantity']]
stock.head(15)

# export result
with ib.open("Stock.csv", "w") as file:
    output = stock.to_csv() # df must convert to df first
    file.write(output)
    
### 4) Buy table - purchaseid, shopid, stockid, date, total_price

date = []

i = 1
while i<= len(shopid):
    
    #year
    if i%11 <= 6:
        year = 2018
        month = i%11 + 6
    else:
        year = 2019
        month = i%11 - 6
        
    #year = randint(2018, 2019) 
    
    """
    #month
    if year == 2018:
        month = randint(7,12)
    else:
        month = randint(1,4)
    """
    
    #day
    day = randint(1,5)
    """
    if month == 2:
        day = randint(1, 28)
    elif month == 4 or month == 6 or month == 9 or month == 11:
        day = randint(1, 30)
    else:
        day = randint(1, 31)
    """
    day = datetime(year, month, day)
    date.append(day)
    i += 1
    
# generate total_price
stock['total_price'] = stock.unit_price * stock.quantity + 50

# generate purchaseid
purchaseid = list(range(500, 500+len(date)))

# merge total_price
buy = pd.DataFrame({'shopid':shopid, 'stockid':stockid*len(set(shopid)), 'date':date, 'purchaseid': purchaseid})
buy = pd.merge(buy, stock, on='shopid', how='left')

# select useful col
buy = buy.loc[buy.stockid_x == buy.stockid_y][['purchaseid', 'shopid', 'stockid_x', 'date', 'total_price']]
# rename
buy.columns = ['purchaseid', 'shopid', 'stockid', 'date', 'total_price']

# export result
with ib.open("Buy.csv", "w") as file:
    output = buy.to_csv() # df must convert to df first
    file.write(output)
