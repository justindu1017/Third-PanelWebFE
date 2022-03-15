from asyncio.runners import run
from concurrent.futures import process
from distutils.log import info
from flask import Flask, render_template, request, redirect, jsonify, abort
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
from time import sleep
from pymodbus.client.sync import ModbusTcpClient as Client
from get_data import get_registers_by_address
from pymodbus.exceptions import ConnectionException
from multiprocessing import Process, Value

database = Database(
    f'mysql://root:28017103@127.0.0.1:3306/meters')


app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
async def index():
    if request.method == 'GET':
        return render_template("index.html")
    elif request.method == "POST":
        form = request.form
        if form["selection"] == "UseIP":
            ip = form["ip1"]+"."+form["ip2"]+"."+form["ip3"]+"."+form["ip4"]
        else:
            ip = form["domainName"]
        port = form["port"]
        meterType = form["meterType"]
        values = {"ip": ip, "port": port, "meter_type": meterType}
        async with database as db:
            query = "INSERT INTO meters(ip, port, meter_type) VALUES (:ip, :port, :meter_type)"
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
        if page <= 0:
            return redirect("/meter_list")
        async with database as db:
            # search for pages
            values = {"off": int((page-1)*40)}
            getPageQuery = "SELECT CEILING(count(id)/40) FROM `meters`;"
            query = "SELECT * FROM `meters` LIMIT 40 OFFSET :off;"
            pages = await db.fetch_all(query=getPageQuery)
            print(pages)
            infos = await db.fetch_all(query=query, values=values)
            await db.disconnect()
        if page > pages[0][0]+1:
            return redirect("/meter_list?page="+str(pages[0][0]+1))
        while(not infos and not page == 1):
            page = page-1
            return redirect("/meter_list?page="+str(page))

        return render_template("nav.html", pages=(1 if pages[0][0] == 0 else pages[0][0]), infos=infos, page=page)
    else:
        # do Query Search
        # queryStr = "Select * from `meters` where "
        form = request.form
        q = queue.Queue()
        tmpStr = ""
        paramValues = {}

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


@app.route("/del/<id>", methods=["DELETE"])
async def delID(id):
    print("deleting id ", id)
    async with database as db:
        query = "DELETE FROM meters WHERE id = :id;"
        await db.execute(query=query, values={"id": id})
        await db.disconnect()
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


def main():
    app.run()


def checkHealth(host: str, port: str, regi: int = 1, count: int = 0):
    client = Client(host=host, port=port)
    try:

        r = get_registers_by_address(client=client, address=regi, count=count)
        print(r)
        return r
    except ConnectionException as e:
        return None


async def fetchDB():
    async with database as db:
        # search for pages
        query = "SELECT * FROM `meters`;"
        result = await db.fetch_all(query=query)
        await db.disconnect()
    return result


def startHealthCheck():
    # fetch all data from db
    # print("res = ", res[0])

    # while loop all the ips
    while True:
        res = asyncio.get_event_loop().run_until_complete(asyncio.gather(fetchDB()))
        for info in res[0]:
            print("IP: ", info[0])
            # checkHealth(host=info[1], port=info[2], regi=5, count=2)
            checkHealth(host='192.168.1.180', port='502', regi=5, count=2)
            sleep(1.5)


if __name__ == '__main__':
    # p = Process(target=checkHealth, args=(5, 2,))
    # p = Process(target=startHealthCheck)
    # p.start()
    main()
    # p.join()
