from asyncio.runners import run
from flask import Flask, render_template, request, redirect, jsonify
from databases import Database
from dotenv import load_dotenv
import os
import asyncio
import queue
from numpy import insert
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
    else:
        ip = form["domainName"]
    port = form["port"]
    values = {"ip": ip, "port": port}
    async with database as db:
        query = "INSERT INTO meters(ip, port) VALUES (:ip, :port)"
        await db.execute(query=query, values=values)
        await db.disconnect()
    return redirect("/")


@app.route("/meter_list", methods=["GET"])
async def get_meter_list():
    selection = request.args.get("selection")
    domainName = request.args.get("domainName")
    ip1 = request.args.get("ip1")
    ip2 = request.args.get("ip2")
    ip3 = request.args.get("ip3")
    ip4 = request.args.get("ip4")
    port = request.args.get("port")
    meterType = request.args.get("meterType")
    CreateAt = request.args.get("CreateAt")
    UpdatedAt = request.args.get("UpdatedAt")
    page = request.args.get("page", default=1, type=int)

    if not (selection or domainName or ip1 or ip2 or ip3 or ip4 or port or meterType or CreateAt or UpdatedAt):
        # page = request.args.get("page", default=1, type=int)
        # the offset of current query
        # values = {"off": int((page-1)*40)}
        async with database as db:
            # search for pages
            values = {"off": int((page-1)*40)}
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
        paramValues = {}
        # SELECT * FROM meters WHERE ip like "%.168.%.82";

        # if not selection == "none":
        #     if not(ip1 or ip2 or ip3 or ip4):
        #         pass
        #     else:
        #         tmpStr = " ip like :ip "
        #         ipStr = ""
        #         if ip1:
        #             ipStr += (ip1)
        #         else:
        #             ipStr += "%"
        #         ipStr += "."
        #         if ip2:
        #             ipStr += (ip2)
        #         else:
        #             ipStr += "%"
        #         ipStr += "."
        #         if ip3:
        #             ipStr += (ip3)
        #         else:
        #             ipStr += "%"
        #         ipStr += "."
        #         if ip4:
        #             ipStr += (ip4)
        #         else:
        #             ipStr += "%"
        #         paramValues["ip"] = ipStr
        #         q.put(tmpStr)
        #         tmpStr = ""

        if not selection == "none":
            tmpStr = " ip like :ip "

            if domainName:
                paramValues["ip"] = "%" + str(domainName)+"%"
                q.put(tmpStr)
                tmpStr = ""
            else:
                ipStr = ""
                if ip1:
                    ipStr += (ip1)
                else:
                    ipStr += "%"
                ipStr += "."
                if ip2:
                    ipStr += (ip2)
                else:
                    ipStr += "%"
                ipStr += "."
                if ip3:
                    ipStr += (ip3)
                else:
                    ipStr += "%"
                ipStr += "."
                if ip4:
                    ipStr += (ip4)
                else:
                    ipStr += "%"
                paramValues["ip"] = ipStr
                q.put(tmpStr)
                tmpStr = ""

        if port:
            tmpStr += ' port = :port '
            paramValues["port"] = str(port)
            q.put(tmpStr)
            tmpStr = ""

        if meterType:
            tmpStr += ' meter_type = :meterType '
            paramValues["meterType"] = str(meterType)
            q.put(tmpStr)
            tmpStr = ""

        if CreateAt:
            createDateFrom = datetime.strftime(
                datetime.strptime(CreateAt, "%Y-%m-%d"), '%Y-%m-%d')
            createDateTo = datetime.strftime((datetime.strptime(CreateAt,
                                                                "%Y-%m-%d")+timedelta(days=1)).date(), '%Y-%m-%d')
            tmpStr += ' created_at BETWEEN :createDateFrom and :createDateTo'
            paramValues["createDateFrom"] = str(createDateFrom)
            paramValues["createDateTo"] = str(createDateTo)
            q.put(tmpStr)
        tmpStr = ""
        if UpdatedAt:
            updatedDateFrom = datetime.strftime(
                datetime.strptime(UpdatedAt, "%Y-%m-%d"), '%Y-%m-%d')
            updatedDateTo = datetime.strftime((datetime.strptime(UpdatedAt,
                                                                 "%Y-%m-%d")+timedelta(days=1)).date(), '%Y-%m-%d')
            tmpStr += ' updated_at BETWEEN :updatedDateFrom and :updatedDateTo'
            paramValues["updatedDateFrom"] = str(updatedDateFrom)
            paramValues["updatedDateTo"] = str(updatedDateTo)
            q.put(tmpStr)
        queryStr = ""
        while not (q.empty()):
            queryStr += q.get()
            if not q.empty():
                queryStr += " and "

        async with database as db:
            # search for pages
            getPageQuery = "SELECT FLOOR(count(id)/40) FROM `meters` where " + \
                queryStr+";"
            query = 'SELECT * FROM `meters` where '+queryStr + " LIMIT 40 OFFSET :off;"
            print(query)
            pages = await db.fetch_all(query=getPageQuery, values=paramValues)
            paramValues["off"] = int((page-1)*40)
            print(paramValues)
            infos = await db.fetch_all(query=query, values=paramValues)
            print(infos)
            await db.disconnect()

        return render_template("nav.html", pages=pages[0][0]+1, infos=infos, page=page)


def main():
    app.run()


if __name__ == '__main__':
    main()
