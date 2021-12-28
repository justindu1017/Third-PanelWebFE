from asyncio.runners import run
from flask import Flask, render_template, request, redirect, jsonify
from databases import Database
from dotenv import load_dotenv
import os
import asyncio


database = Database(
    f'mysql://root:28017103@127.0.0.1:3306/meters')


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/meter_list")
async def meter_list():
    await database.connect()
    get_panel_query = "SELECT * FROM `meters`"
    panel = await database.fetch_all(query=get_panel_query)
    await database.disconnect()
    # meterLists = jsonify(([list(i) for i in panel]))

    # return render_template("meter_list.html", meterLists=meterLists)
    return render_template("meter_list.html", meterLists=panel)


@app.route("/post", methods=['POST'])
async def getPost():
    form = request.form
    if form["selection"] == "UseIP":
        ip = form["ip1"]+"."+form["ip2"]+"."+form["ip3"]+"."+form["ip4"]
        port = form["port"]
        values = {"ip": ip, "port": port}
    async with database as db:
        query = "INSERT INTO meters(ip, port) VALUES (:ip, :port)"
        await database.execute(query=query, values=values)
        await database.disconnect()
    return redirect("/")


def main():
    app.run()


if __name__ == '__main__':
    main()
