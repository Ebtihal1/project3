#!/usr/bin/env python3

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import CatalogItem , Base, ItemDetail, User

engine = create_engine('postgresql://catalog:catalog-pw@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create system admin user

user_1 = User(name="Admin", email="admin@yahoo.com",
             picture='https://imgur.com/a/p4qh5Av')
session.add(user_1)
session.commit()

# Firest Catalog Laptop

cat_1 = CatalogItem(name="Laptop", user=user_1)

session.add(cat_1)
session.commit()

# List of Laptop items 

item_1 = ItemDetail(name="DELL laptop", description="DELL I3565-A453BLK-PUS Dell 15.6", 
                    catalogs = cat_1, user=user_1)

session.add(item_1)
session.commit()

item_2 = ItemDetail(name="HP laptop", description="HP Pavloen 7889 D321",
                    catalogs = cat_1, user=user_1)

session.add(item_2)
session.commit()


print ("Done , added catalog items!")
