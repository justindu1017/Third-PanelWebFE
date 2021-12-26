from asyncio.runners import run
from flask import Flask, render_template, request, redirect
from databases import Database
from dotenv import load_dotenv
import os
import asyncio


database = ""


async def dbConnect():
    load_dotenv()
    global database
    database = Database(os.getenv("Database_Route"))
    print("DB is ", database)
    await database.connect()


async def queryInsert(values):
    query = "INSERT INTO meters(ip, port) VALUES (:ip, :port)"
    print("here is ", database)
    await database.execute(query=query, values=values)


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/post", methods=['POST'])
def getPost():
    form = request.form
    if form["selection"] == "UseIP":
        ip = form["ip1"]+"."+form["ip2"]+"."+form["ip3"]+"."+form["ip4"]
        port = form["port"]
        values = {"ip": ip, "port": port}
    asyncio.run(queryInsert(values))
    print("OK")
    return redirect("/")


def main():
    asyncio.run(dbConnect())
    app.run()


if __name__ == '__main__':
    main()
