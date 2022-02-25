from asyncio.runners import run
from flask import Flask, render_template, request, redirect, jsonify
from databases import Database
from dotenv import load_dotenv
import os
import asyncio
from sqlalchemy import Integer


database = Database(
    f'mysql://root:28017103@127.0.0.1:3306/meters')


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


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


@app.route("/meter_list", methods=['GET'])
async def get_meter_list():

    page = request.args.get("page", default=1, type=int)
    # the offset of current query
    values = {"off": int((page-1)*40)}
    async with database as db:
        # search for pages
        getPageQuery = "SELECT FLOOR(count(id)/40) FROM `meters`;"
        query = "SELECT * FROM `meters` LIMIT 40 OFFSET :off;"
        pages = await database.fetch_all(query=getPageQuery)
        infos = await database.fetch_all(query=query, values=values)
        await database.disconnect()
    meterLists = jsonify(([list(i) for i in infos]))
    # return render_template("meter_list.html", pages=pages[0][0]+1, infos=infos, page=page)
    return render_template("nav.html", pages=pages[0][0]+1, infos=infos, page=page)


def main():
    app.run()


if __name__ == '__main__':
    main()
