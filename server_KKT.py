from flask import Flask, request, jsonify, json
from libfptr10 import IFptr
from pybase64 import b64decode
from threading import Thread
import sqlite3 as sql
import time
import datetime
import telebot
app = Flask(__name__)
import os
from dotenv import load_dotenv

load_dotenv()
BOT_API = os.getenv('BOT_API')
GROUP_ID = os.getenv('GROUP_ID')
bot = telebot.TeleBot(BOT_API)
version = '24.05.14.2'
current_date = datetime.datetime.now()
now = current_date.strftime('%m/%d/%y %H:%M:%S')
bot.send_message(GROUP_ID, f"{now} Запуск сервера v.{version}")

#region Методы

def jsonDisassembly(content):
    # разбор контейнера json
    uuid = content['uuid']
    kassa = content['kassa']
    type = content['request'][0]['type']
    taxationType = content['request'][0]['taxationType']
    electronically = content['request'][0]['electronically']
    operatorName = content['request'][0]['operator']['name']
    clientInfoEmailOrPhone = content['request'][0]['clientInfo']['emailOrPhone']
    paymentsTypeQuantity = len(content['request'][0]['payments'])   # Количество способов расчета в чеке
    paymentsType = content['request'][0]['payments'][0]['type']
    paymentsSum = content['request'][0]['payments'][0]['sum']
    total = content['request'][0]['total']
    validateMarkingCodes = content['request'][0]['validateMarkingCodes']
    itemsQuantity = len(content['request'][0]['items'])
    return uuid, kassa, type, taxationType, electronically, operatorName, clientInfoEmailOrPhone, paymentsType, paymentsSum, total, validateMarkingCodes, itemsQuantity, paymentsTypeQuantity

def jsonItemsDisassembly(item):
    # разбор контейнера json по товару
    typeItem = item['type']
    nameItem = item['name']
    price = item['price']
    quantity = item['quantity']
    amount = item['amount']
    paymentMethod = item['paymentMethod']
    paymentObject = item['paymentObject']
    taxType = item['tax']['type']
    if len(item) == 10:
        measurementUnit = item['measurementUnit']
        imcType = item['imcParams']['imcType']
        imc = item['imcParams']['imc']
        imcModeProcessing = item['imcParams']['imcModeProcessing']
        itemEstimatedStatus = item['imcParams']['itemEstimatedStatus']
    else:
        measurementUnit = 0
        imcType = ""
        imc = ""
        imcModeProcessing = ""
        itemEstimatedStatus = ""
    return typeItem, nameItem, price, quantity, amount, paymentMethod, paymentObject, taxType, measurementUnit, imcType, imc, imcModeProcessing, itemEstimatedStatus

def newDB():
    con = sql.connect('checks.db')
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS 'check' (" \
    "uuid TEXT NOT NULL, status INTEGER, type TEXT NOT NULL, operatorName TEXT NOT NULL, " \
    "clientInfoEmailOrPhone TEXT NOT NULL, paymentsType TEXT NOT NULL, paymentsSum TEXT NOT NULL, itemsQuantity INTEGER, " \
    "timeFD TEXT NOT NULL, numFD INTEGER, typeFD INTEGER, sumFD REAL, fpFD INTEGER, fnFD INTEGER, rnKKT TEXT NOT NULL, numSmeny INTEGER, kassa TEXT NOT NULL, json TEXT NOT NULL)")
    cur.execute('CREATE INDEX idx_uuid_check ON "check" (uuid)')
    cur.execute("CREATE TABLE IF NOT EXISTS 'item' (" \
    "uuid TEXT NOT NULL, nameItem TEXT NOT NULL, price REAL, quantity INTEGER, imc TEXT NOT NULL, paymentObject TEXT NOT NULL, taxType TEXT NOT NULL, paymentMethod TEXT NOT NULL)")
    cur.execute('CREATE INDEX idx_uuid_item ON "item" (uuid)')
    cur.execute("CREATE TABLE IF NOT EXISTS 'payment' (uuid TEXT NOT NULL, cash REAL, electron REAL, prepaid REAL, credit REAL, other REAL)")
    cur.execute('CREATE INDEX idx_uuid_payment ON "payment" (uuid)')
    con.commit()
    con.close()
    return

def initializationKKT(kassa):

    # инициализация драйвера
    fptr = IFptr("")
    #version = fptr.version()
    #print('driver version:  ' + str(version))
    try:
        with open('kassa.json', 'r', encoding='utf-8') as file:
            kassaJson = json.load (file)
        KASSA_IP = kassaJson[kassa]

        # подключение ККТ
        settings = {
            IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
            IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_TCPIP,
            IFptr.LIBFPTR_SETTING_IPADDRESS: KASSA_IP,
            IFptr.LIBFPTR_SETTING_IPPORT: 5555
        }
        fptr.setSettings(settings)
        fptr.open()
        isOpened = fptr.isOpened()
        print('Статус готовности к обмену с ККТ: '+ str(isOpened))
        numSmeny = 0
        if isOpened == 1:
            fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHIFT_STATE)
            fptr.queryData()
            state = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE)
            if (state == 2):
                botMessage = "# Закрытие смены после 24 часов (" + kassa + ")"
                bot.send_message(GROUP_ID, botMessage)
                fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_ELECTRONICALLY, True)
                fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_CLOSE_SHIFT)
                fptr.report()
                fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_ELECTRONICALLY, True)
                fptr.openShift()
            fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHIFT_STATE)
            fptr.queryData()
            numSmeny = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
    except KeyError:
        isOpened = 9
        numSmeny = 0
    return isOpened, numSmeny, fptr

def checkReceiptClosed(fptr):
    while fptr.checkDocumentClosed() < 0:   # не удалось проверить закрытие чека
        print(fptr.errorDescription())
        continue
    CheckClosed = True
    if not fptr.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_CLOSED):  # чек не закрылся,- отменяем его
        fptr.cancelReceipt()
        CheckClosed = False
        botMessage = "! Неудачная обработка чека"
        bot.send_message(GROUP_ID, botMessage)
    print("Результат закрытия чека: " + fptr.errorDescription())       
    return CheckClosed

def checkOfMarring(markingCodeBase64, fptr):

    markingCode = (b64decode(markingCodeBase64)).decode()
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_TYPE, IFptr.LIBFPTR_MCT12_AUTO)
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, markingCode)
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_STATUS, 2)   # товар с КМ в стадии реализации
    fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, 1.000)
    fptr.setParam(IFptr.LIBFPTR_PARAM_MEASUREMENT_UNIT, IFptr.LIBFPTR_IU_PIECE)
    fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_PROCESSING_MODE, 0)
    fptr.beginMarkingCodeValidation()
    # дожидаемся окончания проверки и запоминаем результат
    while True:
        fptr.getMarkingCodeValidationStatus()
        if fptr.getParamBool(IFptr.LIBFPTR_PARAM_MARKING_CODE_VALIDATION_READY):
            break
    validationResult = fptr.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT)
    # подтверждаем реализацию товара с указанным КМ
    fptr.acceptMarkingCode()
    print("КМ товара прошел проверку - ", markingCode)

    return markingCode, validationResult

def productRegistration(nameItem, price, quantity, markingCode, validationResult, paymentObject, taxType, paymentMethod, fptr):

    fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME, nameItem)
    fptr.setParam(IFptr.LIBFPTR_PARAM_PRICE, price)
    fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, quantity)
    fptr.setParam(IFptr.LIBFPTR_PARAM_MEASUREMENT_UNIT, IFptr.LIBFPTR_IU_PIECE)

    if taxType == "none":
        fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, IFptr.LIBFPTR_TAX_NO)
    if taxType == "vat0":
        fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, IFptr.LIBFPTR_TAX_VAT0)
    if taxType == "vat10":
        fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, IFptr.LIBFPTR_TAX_VAT10)
    if taxType == "vat20":
        fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, IFptr.LIBFPTR_TAX_VAT20)

    if paymentMethod == "fullPayment":
        fptr.setParam(1214, 4)  # способ расчета: 4 - полный расчет
    if paymentMethod == "prepayment":
        fptr.setParam(1214, 2)  # способ расчета: 2 - предоплата

    fptr.setParam(1212, 13) # предмет расчета - иной (если не товар (в т.ч. с КМ) и не услуга)
    if paymentObject == "commodity":
        fptr.setParam(1212, 1) # предмет расчета - товар
    if paymentObject == "service":
        fptr.setParam(1212, 4) # предмет расчета - услуга

    if markingCode != "":
        fptr.setParam(1212, 33) # предмет расчета - товар с кодом маркировки  
        fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, markingCode)
        fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_STATUS, 2)
        fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT, validationResult)
        fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_PROCESSING_MODE, 0)

    fptr.registration()
    return

def connectKKT_daemon():

    # SELECT FROM WHERE status = 'новый'
       # <новый> status = '0'
       # <пробит> status = '1' 
       # <не обработан> status = '2' 

    # if not(os.path.isfile('checks.db')):    # если база чеков не существует, то создаем её  /// ОТКЛЮЧЕНО ///
    #     newDB() 

    while True:      
        con = sql.connect('checks.db')
        cur = con.cursor()           
        cur.execute('SELECT COUNT(*) FROM "check" WHERE status = ?', (0,))      # проверка наличия "непробитых" чеков в базе
        totalNewCheck = cur.fetchone()[0]       # количество "непробитых" чеков
        #botMessage = "... новых чеков в базе: " + str(totalNewCheck)
        #bot.send_message(GROUP_ID, botMessage)
        if totalNewCheck > 0:         
            cur.execute('SELECT uuid, status, type, operatorName, clientInfoEmailOrPhone, paymentsType, paymentsSum, itemsQuantity, kassa FROM "check" WHERE status = ?', (0,))   # Выбираем "непробитые" чеки
            resultsCheck = cur.fetchall()   # выборка "непробитых" чеков
            for rowCheck in resultsCheck:   # конкретный чек
                print("Новый чек с uuid: " + rowCheck[0])
                connectStatus, numSmeny, fptr = initializationKKT(rowCheck[8])   # инициализация и подключение ККТ  
                if connectStatus == 1:      # ККТ готова  
                    fptr.setParam(1021, rowCheck[3]) # кассир
                    fptr.operatorLogin()
                    fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_SELL)  # LIBFPTR_RT_SELL - это продажа (по умолчанию, если не возврат)
                    typeFD = 1 
                    if rowCheck[2] == "sellReturn":
                        fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_SELL_RETURN)  # LIBFPTR_RT_SELL_RETURN - это возврат
                        typeFD = 2
                    fptr.setParam(1008, rowCheck[4])
                    fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY, True)
                    fptr.openReceipt()
      
                    cur.execute('SELECT uuid, nameItem, price, quantity, imc, paymentObject, taxType, paymentMethod FROM "item" WHERE uuid = ?', (rowCheck[0],))
                    resultsItem = cur.fetchall()    # выборка товаров в чеке из выборки
                    for rowItem in resultsItem:     # для каждого товара в выбранном чеке
                        markingCode = ""
                        validationResult = 0
                        if rowItem[4] != "":  # если это товар с КМ (imc не пустой)
                            markingCode, validationResult = checkOfMarring(rowItem[4], fptr)      # проверка КМ товара
                        productRegistration(rowItem[1], rowItem[2], rowItem[3], markingCode, validationResult, rowItem[5], rowItem[6], rowItem[7], fptr)      # регистрация товара в чеке

                    cur.execute('SELECT uuid, cash, electron, prepaid, credit, other FROM "payment" WHERE uuid = ?', (rowCheck[0],))
                    resultsPayment= cur.fetchall()    # выборка товаров в чеке из выборки
                    for rowPayment in resultsPayment:
                        if rowPayment[3] > 0:
                            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_PREPAID) # LIBFPTR_PT_PREPAID - предоплата
                            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, rowPayment[3])
                            fptr.payment() 
                        if rowPayment[2] > 0:
                            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_ELECTRONICALLY) # LIBFPTR_PT_ELECTRONICALLY - безналичная оплата
                            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, rowPayment[2])
                            fptr.payment()                     
                        if rowPayment[1] > 0:
                            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_CASH) # LIBFPTR_PT_CASH - наличный расчет
                            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, rowPayment[1])
                            fptr.payment()

                    fptr.closeReceipt()     # закрытие чека
                    CheckClosed = checkReceiptClosed(fptr)    # обработка результата операции
                    if CheckClosed:
                        fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_REG_INFO)
                        fptr.fnQueryData()
                        rnKKT = fptr.getParamString(1037)

                        fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_FN_INFO)
                        fptr.fnQueryData()
                        fnSerial            = fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)

                        fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_LAST_RECEIPT)
                        fptr.fnQueryData()
                        documentNumber      = fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
                        receiptType         = fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE)
                        receiptSum          = fptr.getParamDouble(IFptr.LIBFPTR_PARAM_RECEIPT_SUM)
                        fiscalSign          = fptr.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_SIGN)
                        dateTime            = str(fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME))
                        cur.execute('UPDATE "check" SET status = ? WHERE uuid = ?', (1, rowCheck[0]))               # изменение статуса чека на <пробит>
                        cur.execute('UPDATE "check" SET timeFD = ? WHERE uuid = ?', (dateTime, rowCheck[0]))        # запись фискальных данных (дата)
                        cur.execute('UPDATE "check" SET numFD = ? WHERE uuid = ?', (documentNumber, rowCheck[0]))   # запись фискальных данных (номер документа)
                        cur.execute('UPDATE "check" SET typeFD = ? WHERE uuid = ?', (typeFD, rowCheck[0]))          # запись фискальных данных (тип документа)
                        cur.execute('UPDATE "check" SET sumFD = ? WHERE uuid = ?', (receiptSum, rowCheck[0]))       # запись фискальных данных (сумма документа)
                        cur.execute('UPDATE "check" SET fpFD = ? WHERE uuid = ?', (fiscalSign, rowCheck[0]))        # запись фискальных данных (ФП документа)
                        cur.execute('UPDATE "check" SET fnFD = ? WHERE uuid = ?', (fnSerial, rowCheck[0]))          # запись фискальных данных (номер ФН)
                        cur.execute('UPDATE "check" SET rnKKT = ? WHERE uuid = ?', (rnKKT, rowCheck[0]))            # запись фискальных данных (номер ККТ)
                        cur.execute('UPDATE "check" SET numSmeny = ? WHERE uuid = ?', (numSmeny, rowCheck[0]))      # запись фискальных данных (номер смены)
                        botMessage = "--> чек ОФД : " + str(f"{receiptSum:.2f}") + " (" + rowCheck[8] + ")"
                        bot.send_message(GROUP_ID, botMessage)
                        totalNewCheck -= 1
                else:
                    cur.execute('UPDATE "check" SET status = ? WHERE uuid = ?', (2, rowCheck[0]))    # изменение статуса чека на <не обработан>                  
                    message = "--> чек не пробит ККТ (" + rowCheck[8] + ")"
                    if connectStatus == 9:
                        message = message + ": не определен ip"
                    bot.send_message(GROUP_ID, message)
                fptr.close()
        con.commit()
        con.close()     
        time.sleep(30)

#endregion


#region Обработчик чеков в цикле

Thread(target=connectKKT_daemon, daemon=True).start()   # запуск обработчика

#endregion


#region WEB API Основной

@app.route("/")
def root():
    now = datetime.datetime.now()
    bot.send_message(GROUP_ID, f"{now}: Вход на http://cs-develop.ru:4005/")
    return f"{now}: romakkt-server v. {version}"

@app.route("/check", methods = ['POST'])
def checkSend():
  
    current_date = datetime.datetime.now()
    now = current_date.strftime('%d.%m.%y %H:%M')

    content = request.json  # "разбор" json
    bot.send_message(GROUP_ID, f"--> новый чек: {now}")
    uuid, kassa, type, taxationType, electronically, operatorName, clientInfoEmailOrPhone, paymentsType, paymentsSum, total, validateMarkingCodes, itemsQuantity, paymentsTypeQuantity = jsonDisassembly(content)
    fullJson = json.dumps(content)
    status = 0
    # clientInfoEmailOrPhone = 'kotyurov@pcs.ru'  # /// ВРЕМЕННО ДЛЯ ОТЛАДКИ ///

    con = sql.connect('checks.db')      # запись нового чека в базу
    cur = con.cursor()

    cur.execute('SELECT COUNT(*) FROM "check" WHERE uuid = ?', (uuid,))      # проверка на "дубль"
    message = "! uuid чека уже имеется в базе"
    writeStatus = False
    if cur.fetchone()[0] == 0:      # нет такого uuid в базе
        message = "--> чек записан в базу (" + kassa + ")"
        writeStatus = True
        cur.execute(f"INSERT INTO `check` VALUES ('{uuid}', '{status}', '{type}', '{operatorName}', '{clientInfoEmailOrPhone}', '{paymentsType}', '{total}', '{itemsQuantity}', '', '', '', '', '', '', '', '','{kassa}','{fullJson}')")

        for numberItem in range(itemsQuantity):     # запись каждого товара (чека) из чека в базу
            items = content['request'][0]['items']
            typeItem, nameItem, price, quantity, amount, paymentMethod, paymentObject, taxType, measurementUnit, imcType, imc, imcModeProcessing, itemEstimatedStatus = jsonItemsDisassembly(items[numberItem])       
            cur.execute(f"INSERT INTO `item` VALUES ('{uuid}', '{nameItem}', '{price}', '{quantity}', '{imc}', '{paymentObject}', '{taxType}', '{paymentMethod}')")

        cash = 0
        electron = 0
        prepaid = 0
        credit = 0
        other = 0
        for numberPayments in range(paymentsTypeQuantity):     # запись каждого типа оплаты из чека в базу
            Payments = content['request'][0]['payments'][numberPayments]
            if Payments['type'] == "cash":
                cash = Payments['sum']
            if Payments['type'] == "electronically":
                electron = Payments['sum']
            if Payments['type'] == "prepaid":
                prepaid = Payments['sum']
        cur.execute(f"INSERT INTO `payment` VALUES ('{uuid}', '{cash}', '{electron}', '{prepaid}', '{credit}', '{other}')")

    con.commit()
    con.close()
    
    bot.send_message(GROUP_ID, message)
    return jsonify({
        "status": writeStatus,
        "message": message
        })

@app.route("/checkStatus", methods = ['GET'])
def checkStatus():
    uuid = request.args['guid']
    statusFD = False
    inProgress = False
    message = "uuid чека отсутствует в базе"
    con = sql.connect('checks.db')  
    cur = con.cursor()
    cur.execute('SELECT COUNT(*) FROM "check" WHERE uuid = ?', (uuid,))  # Выбираем чек по запрошенному uuid 
    if cur.fetchone()[0] > 0:
        cur.execute('SELECT timeFD, numFD, typeFD, sumFD, fpFD, fnFD, status, rnKKT, numSmeny FROM "check" WHERE uuid = ?', (uuid,))   # Выбираем ФД по запрошенному uuid
        resultsFD = cur.fetchall()
        for rowFD in resultsFD:
            statusCheck = rowFD[6]
            if statusCheck == 1:
                statusFD = True
                timeFD = rowFD[0]
                timeFD_iso = timeFD[:10]+"T"+timeFD[11:]
                timeFD = timeFD[:4]+timeFD[5:7]+timeFD[8:10]+"T"+timeFD[11:13]+timeFD[14:16]
                numFD  = rowFD[1]
                typeFD = rowFD[2]
                sumFD  = f"{rowFD[3]:.2f}"
                fpFD   = rowFD[4]
                fnFD   = rowFD[5]
                rnKKT   = rowFD[7]
                numSmeny = rowFD[8]
                #message = "https://api.qrserver.com/v1/create-qr-code/?data=t="+timeFD+"%26s="+str(sumFD)+"%26fn="+str(fnFD)+"%26i="+str(numFD)+"%26fp="+str(fpFD)+"%26n="+str(typeFD)+"&size=200x200&margin=5"
                message = timeFD+"&s="+str(sumFD)+"&fn="+str(fnFD)+"&i="+str(numFD)+"&fp="+str(fpFD)+"&n="+str(typeFD)+" / "+ rnKKT
            elif statusCheck == 0:
                message = "чек еще не обрабатывался на ККТ (новый), uuid=" + uuid
                inProgress = True
            elif statusCheck == 2:
                message = "при обработке чека на ККТ возникла ошибка, uuid=" + uuid
            else:
                message = "неизвестный статус чека, uuid=" + uuid # исключение
    con.commit()
    con.close()
    #bot.send_message(GROUP_ID, message)
    if statusFD:
        return jsonify({
            "status": statusFD,
            "timeFD": timeFD_iso,
            "numFD": str(numFD),
            "typeFD": str(typeFD),
            "sumFD": sumFD,
            "fpFD": str(fpFD),
            "fnFD": str(fnFD),
            "rnKKT": rnKKT,
            "numSmeny": str(numSmeny)
        })
    else:
        return jsonify({
            "status": statusFD,
            "inProgress": inProgress, 
            "message": message
        })

@app.route("/howManyChecks", methods = ['GET'])
def howManyChecks():
    kassa = request.args['kassa']
    con = sql.connect('checks.db')  # выборка из базы
    cur = con.cursor()
    cur.execute('SELECT COUNT(*) FROM "check" WHERE status=? AND kassa=?', (0, kassa))  # выборка чеков со статусом "новый"
    newCheck = cur.fetchone()[0]       # количество "новых" чеков
    cur.execute('SELECT COUNT(*) FROM "check" WHERE status=? AND kassa=?', (1, kassa))  # выборка чеков со статусом "пробит"
    confirmedCheck = cur.fetchone()[0]  # количество "пробитых" чеков
    cur.execute('SELECT COUNT(*) FROM "check" WHERE status=? AND kassa=?', (2, kassa))  # выборка чеков со статусом "ошибка"
    errorCheck = cur.fetchone()[0]     # количество чеков "с ошибкой от ККТ"
    cur.execute('SELECT uuid, type, clientInfoEmailOrPhone, paymentsType, paymentsSum, timeFD, numFD, fpFD FROM "check" WHERE status=? AND kassa=?', (0, kassa))   # Выбираем "непробитые" чеки
    resultsNewCheck = cur.fetchall() 
    cur.execute('SELECT uuid, type, clientInfoEmailOrPhone, paymentsType, paymentsSum, timeFD, numFD, fpFD FROM "check" WHERE status=? AND kassa=?', (1, kassa))   # Выбираем "непробитые" чеки
    resultsConfirmCheck = cur.fetchall()
    cur.execute('SELECT uuid, type, clientInfoEmailOrPhone, paymentsType, paymentsSum, timeFD, numFD, fpFD FROM "check" WHERE status=? AND kassa=?', (2, kassa))   # Выбираем "непробитые" чеки
    resultsErrorCheck = cur.fetchall()  
    con.commit()
    con.close()
    total = newCheck + confirmedCheck + errorCheck
    message = "В базе для ККТ =" + kassa + "= " + str(total)+"/"+str(confirmedCheck)+ "/"+str(newCheck)+"/"+str(errorCheck)
    bot.send_message(GROUP_ID, message)
    return jsonify({
        "1_total": total,
        "3_new": newCheck,
        "2_confirm": confirmedCheck,
        "4_error": errorCheck,
        "5_newChecks": resultsNewCheck,
        "7_confirmChecks": resultsConfirmCheck,
        "6_errorChecks": resultsErrorCheck      
    })

#endregion


#region WEB API Вспомогательный

@app.route("/testKkt")
def testKkt():
    # Инициализация драйвера
    fptr = IFptr("")
    version = fptr.version()
    print('version')
    print(version)

    # Подключение ККТ
    settings = {
        IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
        IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_TCPIP,
        IFptr.LIBFPTR_SETTING_IPADDRESS: "192.0.0.153",
        IFptr.LIBFPTR_SETTING_IPPORT: 5555
    }
    fptr.setSettings(settings)

    fptr.open()
    isOpened = fptr.isOpened()
    print('isOpened')
    fptr.lineFeed()
    print(isOpened)
    # return 'version: ' + str(version)

    # Закрытие смены
    fptr.setParam(fptr.LIBFPTR_PARAM_REPORT_ELECTRONICALLY, 1)

    fptr.setParam(1021, "Кассир Иванов И.")
    fptr.setParam(1203, "123456789047")
    fptr.operatorLogin()

    fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_CLOSE_SHIFT)
    fptr.report()

    #fptr.setParam(IFptr.LIBFPTR_PARAM_PRINT_REPORT, False)
    #fptr.deviceReboot()

    return 'Cмена закрыта'

@app.route("/testOFD")
def testOFD():
    # Инициализация драйвера
    fptr = IFptr("")
    version = fptr.version()

    print('version')
    print(version)

    # Подключение ККТ
    settings = {
        IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
        IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_TCPIP,
        IFptr.LIBFPTR_SETTING_IPADDRESS: "192.0.0.153",
        IFptr.LIBFPTR_SETTING_IPPORT: 5555
    }
    fptr.setSettings(settings)

    fptr.open()
    isOpened = fptr.isOpened()
    print('isOpened')
    print(isOpened)

    fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_OFD_TEST)
    fptr.report()

    return 'OK'

@app.route("/smenaStatus")
def smenaStatus():
    connectStatus, numSmeny, fptr = initializationKKT('sevist')   # инициализация и подключение ККТ  
    if connectStatus == 1:      # ККТ готова
        # fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_ELECTRONICALLY, True)
        # fptr.openShift()
        fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHIFT_STATE)
        fptr.queryData()
        state       = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE)
        dateTime    = fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
        botMessage = "Смена завершится: " + str(dateTime)
        bot.send_message(GROUP_ID, botMessage)
        fptr.close()
        return jsonify({
        "smenaNumber": numSmeny,
        "smenaStatus": state,
        "smenaDateTime": dateTime
        })
    else:
        fptr.close()
        return "Нет ответа от ККТ"

#endregion


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=4005)