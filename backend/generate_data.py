from faker import Faker
import random
import pandas as pd

fake = Faker('en_IN')
warehouse_products = ['spices','saree','lehnga','tshirt','shirt','kurta','jeans','formal jeans','jacket',
           'sweater','trouser','mobile','laptop','computer','bottle','pen','copy',
           'noodles','books','groceries','bags']
categories = ["groceries","women wear","mens wear","home appliances", "beauty","books","furniture","pharmaceuticals","kids"]
def warehouse_data():
    data = []
    for i in range(5001):
        warehouseid = i+1
        owner = fake.name()
        first_name = owner.split(" ")[0]
        sector = random.choice(["Foods", "Agro", "Spices", "Grains", "Dry Fruits", "clothing"])
        company_type = random.choice(["Limited", "Pvt Ltd", "Enterprises", "Industries"])
        name = first_name + " " + sector + " " + company_type
        address = fake.city()
        product = random.choice(warehouse_products)
        quantity = random.randint(0,1000)
        priceperpiece = random.randint(10,10000)
        phoneNumber = int(fake.phone_number())
        email = owner.lower().replace(" ", "") + "@gmail.com"
        data.append((warehouseid,name,address,product,quantity,priceperpiece,phoneNumber,email,owner))
        Data =pd.DataFrame(data=data,columns=["warehouseid","name","address","product","quantity","priceperpiece","phoneNumber","email","owner"])
        
    return Data.to_csv("warehouse.csv",index=False)

def itemspecifications():
    data = []
    for i in range(5000):
        quantity = random.randint(1,1000)
        procuredate = fake.date_between(start_date='-2y')
        expiry = fake.date_between(start_date= '-1y',end_date='+1y')
        priceperpiece = random.randint(10,10000)
        bookedquantity = random.randint(1,quantity)
        availablequantity = quantity - bookedquantity
        itemname = random.choice(warehouse_products)
        data.append((quantity,procuredate,expiry,priceperpiece,bookedquantity,availablequantity,itemname))
        dataframe = pd.DataFrame(data,columns=[quantity,procuredate,expiry,priceperpiece,bookedquantity,availablequantity,itemname])
    return dataframe.to_csv("items.csv",index = False)

if __name__ == "__main__":
    #print(warehouse_data())
    result = itemspecifications()
    print(result)