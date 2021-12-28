aTuple = (123, 'xyz', 'zara', 'abc')
aList = list(aTuple)
print("List elements : ", aList)
# from flask import Flask, jsonify
# from databases import Database

# app = Flask(__name__)
# database = Database(
#     f"'mysql://third:aqEp)TWzYSUpWT49@192.168.102.1:3306/third_demo'")


# @app.route("/")
# def hello_world():
#     return "<p>Hello, World!</p>"


# @app.route("/get-data")
# async def get_data():
#     await database.connect()
#     get_panel_query = "SELECT * FROM `panels`"
#     panel = await database.fetch_one(query=get_panel_query)
#     database.disconnect()

#     return jsonify([i for i in panel])


# @app.route("/get-data")
# async def get_data():
#     async with database as db:
#         get_panel_query = "SELECT * FROM `panels`"
#         panel = await db.fetch_one(query=get_panel_query)
#     return jsonify([i for i in panel])

# if __name__ == '__main__':
#     app.run()
