import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import sys
import json

def delete_collection(coll_ref, batch_size):
    if batch_size == 0:
        return

    docs = coll_ref.list_documents(page_size=batch_size)
    deleted = 0

    for doc in docs:
        doc.delete()
        deleted = deleted + 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)
    print("All documents from collection deleted.")

if __name__ == "__main__":
    # get the data file from program run command
    data_file = sys.argv[1]
    # connect to firestore
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    db=firestore.client()

    # read in the data
    f = open(data_file)
    data = json.load(f)
    f.close()
    # delete the old data
    delete_collection(db.collection('Vermont_Municipalities'), len(data))
    # add the data to the firestore
    for idx, item in enumerate(data):
        db.collection('Vermont_Municipalities').add(item)
        if idx == len(data) - 1:
            print("Upload successful")

    # Find All towns in Chittenden County
    print("All towns in Chittenden County:")
    q = db.collection("Vermont_Municipalities").where("County", "==", "Chittenden")
    for doc in q.stream():
        data = doc.to_dict()
        print(data.get("Town_Name"))

    # Find the 5 largest towns by population
    print("5 largest towns by population:")
    q = (db.collection("Vermont_Municipalities")
       .where("Population", ">", 0)
       .order_by("Population", direction=firestore.Query.DESCENDING)
       .limit(5))
    for doc in q.stream():
        t = doc.to_dict()
        print(t["Town_Name"], t["Population"])
