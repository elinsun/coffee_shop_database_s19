# insert csv files into database

def insert_values(table_name):
    """
    - make sure table name == csv file name
    """
    # read csv
    filename = table_name + '.csv'
    with ib.open(filename) as file:
        data = pd.read_csv(file)

    # drop the first col: index col
    if table_name not in ('Staff', 'Customer', 'Menu', 'Position', 'Shop'):
        data = data.drop('Unnamed: 0', axis=1)

    print "csv file:\n"
    print data.head()

    # connect engine
    user = "UNIHERE"
    password = "PASSWORDHERE"
    server = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

    database_url = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"
    engine = create_engine(database_url)

    # insert values row by row
    for record in range(data.shape[0]):
        value = ','.join([('\''+ str(i)+'\'') for i in data.iloc[record].values])
        sql = 'insert into {} values({})'.format(table_name, value)
        engine.execute(sql)

# sample implementation
# read Shop info from  'Shop.csv' and insert values into table 'Shop'


table_name = 'Shop'
insert_values(table_name)
