from asyncio.runners import run
from flask import Flask, render_template, request, redirect, jsonify
from databases import Database
from dotenv import load_dotenv
import os
import asyncio
import queue
from sqlalchemy import Integer
import json
from datetime import datetime, timedelta, date
import time
import sys

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
        await db.execute(query=query, values=values)
        await db.disconnect()
    return redirect("/")


@app.route("/meter_list", methods=["GET", "POST"])
async def get_meter_list():
    if request.method == 'GET':
        page = request.args.get("page", default=1, type=int)
        # the offset of current query
        values = {"off": int((page-1)*40)}
        async with database as db:
            # search for pages
            getPageQuery = "SELECT FLOOR(count(id)/40) FROM `meters`;"
            query = "SELECT * FROM `meters` LIMIT 40 OFFSET :off;"
            pages = await db.fetch_all(query=getPageQuery)
            infos = await db.fetch_all(query=query, values=values)
            await db.disconnect()
        meterLists = jsonify(([list(i) for i in infos]))
        # return render_template("meter_list.html", pages=pages[0][0]+1, infos=infos, page=page)
        return render_template("nav.html", pages=pages[0][0]+1, infos=infos, page=page)
    elif request.method == "POST":
        # do Query Search
        queryStr = "Select * from `meters` where "
        form = request.form
        q = queue.Queue()
        tmpStr = ""
        # print(form["createAt"]-1)
        if form["ID"]:
            tmpStr += "ID="
            tmpStr += form["ID"]
            q.put(tmpStr)
            tmpStr = ""

        # SELECT * FROM meters WHERE ip like "%.168.%.82";
        tmpStr = ' ip like "'
        if form["ip1"]:
            tmpStr += form["ip1"]
        else:
            tmpStr += "%"
        tmpStr += "."
        if form["ip2"]:
            tmpStr += form["ip2"]
        else:
            tmpStr += "%"
        tmpStr += "."
        if form["ip3"]:
            tmpStr += form["ip3"]
        else:
            tmpStr += "%"
        tmpStr += "."
        if form["ip4"]:
            tmpStr += form["ip4"]
        else:
            tmpStr += "%"
        tmpStr += '"'
        q.put(tmpStr)
        tmpStr = ""

        if form["CreateAt"]:
            dateTo = datetime.strftime(
                datetime.strptime(form["CreateAt"], "%Y-%m-%d"), '%Y-%m-%d')
            dateFrom = datetime.strftime((datetime.strptime(form["CreateAt"],
                                          "%Y-%m-%d")-timedelta(days=1)).date(), '%Y-%m-%d')
            tmpStr += ' created_at BETWEEN "'
            tmpStr += dateTo
            tmpStr += '" AND "'
            tmpStr += dateFrom
            tmpStr += '"'
            q.put(tmpStr)
        tmpStr = ""
        if form["UpdatedAt"]:
            dateTo = datetime.strftime(
                datetime.strptime(form["UpdatedAt"], "%Y-%m-%d"), '%Y-%m-%d')
            dateFrom = datetime.strftime((datetime.strptime(form["UpdatedAt"],
                                          "%Y-%m-%d")-timedelta(days=1)).date(), '%Y-%m-%d')
            tmpStr += ' updated_at BETWEEN "'
            tmpStr += dateTo
            tmpStr += '" AND "'
            tmpStr += dateFrom
            tmpStr += '"'
            q.put(tmpStr)
        queryStr = "SELECT * FROM `meters` where "
        while not (q.empty()):
            queryStr += q.get()
            if not q.empty():
                queryStr += " or "

        print(queryStr)
        # INJECTION!!!!!!!!
        async with database as db:
            # search for pages
            getPageQuery = "SELECT FLOOR(count(id)/40) FROM `meters`;"
            query = "SELECT * FROM `meters` LIMIT 40 OFFSET :off;"
            pages = await db.fetch_all(query=getPageQuery)
            infos = await db.fetch_all(query=queryStr, values=values)
            await db.disconnect()

        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
        # return render_template("nav.html")


def main():
    app.run()


if __name__ == '__main__':
    main()
