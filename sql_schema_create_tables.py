# SQL Schema to Create Tables

# 1. Shop
drop table if exists Shop CASCADE;

create table Shop(
    shopid text primary key,
    state text not null,
    city text not null,
    address text not null,
    postcode int not null,
    tel bigint not null
);

# 2. Staff
drop table if exists Staff CASCADE;

create table Staff(
    staffid int primary key,
    firstname text not null,
    lastname text not null,
    email text not null unique,
    position text,
    shopid text not null references Shop(shopid) ON DELETE CASCADE,
    password int not null
);

# 3. Customer
drop table if exists Customer CASCADE;

create table Customer(
    customerid int primary key,
    firstname text not null,
    lastname text not null,
    email text not null unique,
    membership text not null,
    password int not null
);

# 4. Position
drop table if exists Position CASCADE;

create table Position(
    position text primary key,
    salary float,
    access boolean not null
);

# 5. Menu
drop table if exists Menu CASCADE;

create table Menu(
    shopid text references Shop(shopid) ON DELETE CASCADE,
    itemid int,
    itemname text,
    price float,

    primary key(shopid, itemid)
);

# 6. Orders
drop table if exists Orders CASCADE;

create table Orders(
    orderid int primary key,
    customerid int not null references Customer(customerid) ON DELETE CASCADE,
    staffid int not null references Staff(staffid) ON DELETE CASCADE,
    timestamp timestamp not null
);

# 7. Contain
drop table if exists Contain CASCADE;

create table Contain(
    orderid int references Orders(orderid) ON DELETE CASCADE,
    shopid text not null,
    itemid int not null,
    quantity int not null,

    primary key(orderid, itemid, shopid),
    foreign key(shopid, itemid) references Menu(shopid, itemid) ON DELETE CASCADE
);

# 8. Stock
drop table if exists Stock CASCADE;

create table Stock(
    shopid text references Shop(shopid) ON DELETE CASCADE,
    stockid int not null,
    stock_name text not null,
    unit_price float not null,
    quantity float not null,

    primary key(shopid, stockid)
);

# 9. Buy
drop table if exists Buy CASCADE;

create table Buy(
    purchaseid int primary key,
    shopid text references Shop(shopid) ON DELETE CASCADE,
    stockid int not null,
    date date not null,
    total_price float not null,

    foreign key (shopid, stockid) references Stock(shopid, stockid) ON DELETE CASCADE
);
