from asyncio.runners import run
from concurrent.futures import process
from distutils.log import info
from ntpath import join
from telnetlib import STATUS
from traceback import print_tb
from flask import Flask, render_template, request, redirect, jsonify, abort
from databases import Database
from dotenv import load_dotenv
import os
import asyncio
import queue
from matplotlib.cbook import print_cycles
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
import threading
from queue import Queue
import functools
import concurrent.futures

database = Database(
    f'mysql://root:28017103@127.0.0.1:3306/meters')

newIPQueue = Queue()
delIPQueue = Queue()

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
        health_check = form["health_check"]
        values = {"ip": ip, "port": port,
                  "meter_type": meterType, "health_check": health_check}
        async with database as db:
            query = "INSERT INTO meters(ip, port, meter_type, health_check) VALUES (:ip, :port, :meter_type, :health_check); select LAST_INSERT_ID(); "
            retID = await db.execute(query=query, values=values)
            newIPProfile = []
            newIPProfile.append(int(health_check))
            newIPProfile.append(retID)
            newIPProfile.append(ip)
            newIPProfile.append(port)
            newIPQueue.put(newIPProfile)

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
            infos = await db.fetch_all(query=query, values=values)
            # await db.disconnect()
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
            pages = await db.fetch_all(query=getPageQuery, values=paramValues)
            paramValues["off"] = int((page-1)*40)

            infos = await db.fetch_all(query=query, values=paramValues)

            # await db.disconnect()

        return render_template("nav.html", pages=pages[0][0]+1, infos=infos, page=page)


@app.route("/del/<id>", methods=["DELETE"])
async def delID(id):

    async with database as db:
        getTime = "select health_check from meters WHERE id = :id;"
        query = "DELETE FROM meters WHERE id = :id;"
        time_for_del = await db.fetch_one(query=getTime, values={"id": id})
        await db.execute(query=query, values={"id": id})
        # await db.disconnect()

        delIPQueue.put([time_for_del[0], int(id)])
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


def main():
    app.run()


def toJson(arr):
    tmp = []
    tmp.append(arr[0])
    tmp.append(arr[1])
    tmp.append(arr[2])
    return tmp


def checkHealth(host: str, port: str, regi: int = 1, count: int = 0):
    # client = Client(host=host, port=port)
    client = Client(host='192.168.1.180', port='502')

    try:

        r = get_registers_by_address(client=client, address=regi, count=count)
        return r
        # return True
    except ConnectionException as e:
        return None


async def implementCheckHealth(obj: dict, time):
    # print("now doing...", obj[0])
    r = checkHealth(host=obj[1], port=obj[2], regi=5, count=2)
    # TODO update DB
    async with database as db:
        query = "insert into health_check_log (meter_id, content) VALUES (:meter_id, :content);"
        # if r:
        #     await db.execute(query=query, values={"meter_id": obj[0], "content": {"health": 1}})
        # else:
        isHealth = 0
        if r:
            isHealth = 1

        await db.execute(query=query, values={"meter_id": obj[0], "content": json.dumps({"health": isHealth})})
        print("eeeee")
        print(obj[0])
        print(isHealth)

        print("finish ", obj[0])


def wrapper(coro):
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def checkQueue(arr, timeT):
    timeT = datetime.fromtimestamp(
        timeT).strftime('%Y-%m-%d %H:%M:%S')
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        arr = [implementCheckHealth(obj, timeT) for obj in arr]
        results = executor.map(wrapper, arr)
        # results = [executor.submit(
        #     implementCheckHealth, obj, timeT) for obj in arr]
        print("\n")


async def fetchDB():
    async with database as db:
        res = {}
        # search for pages
        query = "SELECT health_check FROM `meters` GROUP by health_check;"
        health_checks = await db.fetch_all(query=query)

        for health_check in health_checks:
            qq = "SELECT id, ip, port FROM `meters` where health_check=:health_check"
            results = await db.fetch_all(query=qq, values={"health_check": health_check[0]})
            results = [toJson(result) for result in results]
            obj = {}
            obj[str(health_check[0])] = {}
            obj[str(health_check[0])]["lists"] = results
            res = {**res, **obj}
        # await db.disconnect()
    return res


def startHealthCheck():
    print("SHC")
    # fetch all data from db
    # create a queue for ips that are ready to check health

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    res = loop.run_until_complete(
        asyncio.gather(fetchDB()))[0]
    nowT = time.time()
    for Obj in res:
        res[Obj]["timeTag"] = nowT

    readyList = []
    # threadList = []
    T = time.time()

    checkQueueT = threading.Thread(target=checkQueue, args=(readyList, T,))

    while True:
        if not delIPQueue.empty():
            while not delIPQueue.empty():
                delIP = delIPQueue.get()
                # print("delIP is ", delIP)
                for i, li in enumerate(res[str(delIP[0])]["lists"]):
                    # print(li)
                    if delIP[1] in li:
                        # print("DEL: ", res[str(delIP[0])]["lists"][i])
                        del res[str(delIP[0])]["lists"][i]

        if not newIPQueue.empty():
            while not newIPQueue.empty():
                newIP = newIPQueue.get()
                if not newIP[0] in res:
                    res[newIP[0]] = {}
                    res[newIP[0]]["lists"] = []
                    res[newIP[0]]["lists"].append([newIP[1], newIP[2]])
                    res[newIP[0]]["timeTag"] = nowT

                else:
                    res[newIP[0]]["lists"].append([newIP[1], newIP[2]])
                    res[newIP[0]]["timeTag"] = nowT

        T = time.time()
        for el in res:
            if (T - int(res[el]["timeTag"])) >= int(el):

                readyList += res[el]["lists"]
                res[el]["timeTag"] = T
        if readyList and not checkQueueT.is_alive():
            checkQueueT.start()
            readyList = []
            checkQueueT = threading.Thread(
                target=checkQueue, args=(readyList, T,))

        # pass
        # checkHealth(host=info[1], port=info[2], regi=5, count=2)
        # checkHealth(host='192.168.1.180', port='502', regi=5, count=2)


if __name__ == '__main__':
    p = threading.Thread(target=startHealthCheck)
    p.start()
    main()
