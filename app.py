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


@app.route("/meter_list", methods=["GET"])
async def get_meter_list():
    ID = request.args.get("ID")
    ip1 = request.args.get("ip1")
    ip2 = request.args.get("ip2")
    ip3 = request.args.get("ip3")
    ip4 = request.args.get("ip4")
    port = request.args.get("port")
    meterType = request.args.get("meterType")
    CreateAt = request.args.get("CreateAt")
    UpdatedAt = request.args.get("UpdatedAt")
    page = request.args.get("page", default=1, type=int)
    values = {"off": int((page-1)*40)}

    if not (ID or ip1 or ip2 or ip3 or ip4 or port or meterType or CreateAt or UpdatedAt):
        # page = request.args.get("page", default=1, type=int)
        # the offset of current query
        # values = {"off": int((page-1)*40)}
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
    else:
        # do Query Search
        # queryStr = "Select * from `meters` where "
        form = request.form
        q = queue.Queue()
        tmpStr = ""
        # print(CreateAt-1)
        if ID:
            tmpStr += "id="
            tmpStr += str(ID)
            q.put(tmpStr)
            tmpStr = ""

        # SELECT * FROM meters WHERE ip like "%.168.%.82";
        if (not ip1 and not ip2 and not ip3 and not ip4):
            pass
        else:
            tmpStr = ' ip like "'
            if ip1:
                tmpStr += str(ip1)
            else:
                tmpStr += "%"
            tmpStr += "."
            if ip2:
                tmpStr += str(ip2)
            else:
                tmpStr += "%"
            tmpStr += "."
            if ip3:
                tmpStr += str(ip3)
            else:
                tmpStr += "%"
            tmpStr += "."
            if ip4:
                tmpStr += str(ip4)
            else:
                tmpStr += "%"
            tmpStr += '"'
            q.put(tmpStr)
            tmpStr = ""

        if CreateAt:
            dateFrom = datetime.strftime(
                datetime.strptime(CreateAt, "%Y-%m-%d"), '%Y-%m-%d')
            dateTo = datetime.strftime((datetime.strptime(CreateAt,
                                                          "%Y-%m-%d")+timedelta(days=1)).date(), '%Y-%m-%d')
            tmpStr += ' created_at BETWEEN "'
            tmpStr += dateFrom
            tmpStr += '" AND "'
            tmpStr += dateTo
            tmpStr += '"'
            q.put(tmpStr)
        tmpStr = ""
        if UpdatedAt:
            dateFrom = datetime.strftime(
                datetime.strptime(UpdatedAt, "%Y-%m-%d"), '%Y-%m-%d')
            dateTo = datetime.strftime((datetime.strptime(UpdatedAt,
                                                          "%Y-%m-%d")+timedelta(days=1)).date(), '%Y-%m-%d')
            tmpStr += ' updated_at BETWEEN "'
            tmpStr += dateFrom
            tmpStr += '" AND "'
            tmpStr += dateTo
            tmpStr += '"'
            q.put(tmpStr)
        queryStr = ""
        while not (q.empty()):
            queryStr += q.get()
            if not q.empty():
                queryStr += " or "

        # print(queryStr)

        # INJECTION!!!!!!!!
        async with database as db:
            # search for pages
            getPageQuery = "SELECT FLOOR(count(id)/40) FROM `meters` where " + \
                queryStr+";"
            query = 'SELECT * FROM `meters` where '+queryStr + " LIMIT 40 OFFSET :off;"
            print(getPageQuery)

            pages = await db.fetch_all(query=getPageQuery)
            infos = await db.fetch_all(query=query, values=values)
            await db.disconnect()
        print(pages)
        print(infos)
        return render_template("nav.html", pages=pages[0][0]+1, infos=infos, page=page)
        # return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
        # return render_template("nav.html")


def main():
    app.run()


if __name__ == '__main__':
    main()
