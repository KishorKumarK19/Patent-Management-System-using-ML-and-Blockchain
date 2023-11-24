from pymongo import MongoClient

cluster = MongoClient("localhost", 27017)

db = cluster["Patent"]
collection_user = db["Users"]
collection_patents = db["Patents"]
collection_transaction = db["Transactions"]