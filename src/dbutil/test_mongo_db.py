from pymongo import MongoClient

uri= "mongodb+srv://kritaka_user:q3DCrlV5gg2xZZYr@cluster0.jkkz8m5.mongodb.net/admin?appName=Cluster0"

#uri ="mongodb://localhost:27017/"
client = MongoClient(uri)

kritaka_admin_db = client['kritaka_admin']

collection = kritaka_admin_db['customers']
customers = collection.find_one({})

print("customers: ", customers)


kritaka_admin_db = client['kritaka_guardaas']

collection = kritaka_admin_db['guardrails_metadata']
ret_iterator = collection.find({},{"_id" : False})
guardrails_policies = list(ret_iterator)

print("guardrails_policies: ", guardrails_policies)