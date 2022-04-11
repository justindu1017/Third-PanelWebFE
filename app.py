from __future__ import print_function
from calendar import c
from distutils.log import error
from flask import Flask, render_template, request, redirect, jsonify, abort
from databases import Database
from dotenv import load_dotenv
import asyncio
import queue
import json
from datetime import datetime, timedelta, date
import time
from pymodbus.client.sync import ModbusTcpClient as Client
from get_data import get_registers_by_address
from pymodbus.exceptions import ConnectionException
import threading
from queue import Queue
import os
from dotenv import load_dotenv
from async_modbus import AsyncTCPClient


load_dotenv()

# print(os.getenv('Database_Route'))

database = Database(
    os.getenv('Database_Route'))

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
            print(newIPProfile)
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
    # app.run()
    app.run(host='0.0.0.0')


async def conn(ips):
    print(f'start {ips[0]} at {datetime.now().strftime("%H:%M:%S")}')
    try:
        reader, writer = await asyncio.open_connection(ips[1], ips[2])
        # reader, writer = await asyncio.open_connection('192.168.1.180', '502')
        client = AsyncTCPClient((reader, writer))
        reply = await client.read_holding_registers(slave_id=1, starting_address=5, quantity=2)
        # await client.close()
        writer.close()
        async with database as db:
            await db.connect()
            query = "insert into health_check_log (meter_id, content) VALUES (:meter_id, :content);"

            isHealth = 0
            if not len(reply) == 0:
                # if True:
                isHealth = 1

            await db.execute(query=query, values={"meter_id": ips[0], "content": json.dumps({"health": isHealth})})
            await db.disconnect()
        print(f'finish {ips[0]} at {datetime.now().strftime("%H:%M:%S")}')
    except Exception as e:
        print("e: ", e)
        print(
            f'connect failed {ips[0]} at {datetime.now().strftime("%H:%M:%S")}')


# async def conn(ips):
#     print("getting ", ips[0])
    # try:
    #     reader, writer = await asyncio.open_connection(ips[1], ips[2])
    #     client = AsyncTCPClient((reader, writer))
    #     reply = await client.read_holding_registers(slave_id=1, starting_address=1, quantity=len(5))
    #     await client.close()
    #     if reply:
    #         return True
    #     else:
    #         return False
    # except:
    #     print("Failed")
    #     return False


def toJson(arr):
    tmp = []
    tmp.append(arr[0])
    tmp.append(arr[1])
    tmp.append(arr[2])
    return tmp


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


async def startHealthCheck(loop: asyncio.windows_events.ProactorEventLoop, res):
    print("SHC")

    # fetch all data from db
    # create a queue for ips that are ready to check health

    # {'_second': {'lists': [[_id, '_ip', '_port'],....]},....}

    nowT = time.time()
    for Obj in res:
        res[Obj]["timeTag"] = nowT

    readyList = []

    while True:
        T = time.time()
        for el in res:
            if (T - int(res[el]["timeTag"])) >= int(el):
                readyList += res[el]["lists"]
                res[el]["timeTag"] = T
        if readyList:
            print(readyList)
            asyncio.gather(*[conn(ips) for ips in readyList])
            # ???????????
            await asyncio.sleep(0.1)
        readyList = []
        # for ip waiting for delete
        if not delIPQueue.empty():
            print("will del")
            while not delIPQueue.empty():
                delIP = delIPQueue.get()
                # print("delIP is ", delIP)
                for i, li in enumerate(res[str(delIP[0])]["lists"]):
                    # print(li)
                    if delIP[1] in li:
                        print("DEL: ", res[str(delIP[0])]["lists"][i])
                        del res[str(delIP[0])]["lists"][i]

        # for ip that is newly added
        if not newIPQueue.empty():
            while not newIPQueue.empty():
                newIP = newIPQueue.get()
                if not str(newIP[0]) in res:
                    res[str(newIP[0])] = {}
                    res[str(newIP[0])]["lists"] = []
                    res[str(newIP[0])]["lists"].append(
                        [newIP[1], newIP[2], newIP[3]])
                    res[str(newIP[0])]["timeTag"] = nowT

                else:
                    res[str(newIP[0])]["lists"].append([newIP[1], newIP[2]])
                    res[str(newIP[0])]["timeTag"] = nowT


def startHealthCheckWrapper(loop: asyncio.windows_events.ProactorEventLoop):
    asyncio.set_event_loop(loop=loop)
    res = loop.run_until_complete(
        asyncio.gather(fetchDB()))[0]
    loop.run_until_complete(startHealthCheck(loop, res))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    p = threading.Thread(target=startHealthCheckWrapper, args=(loop,))
    p.start()
    loop.call_soon_threadsafe(
        main()
    )
