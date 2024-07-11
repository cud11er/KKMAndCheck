import json
import datetime
from flask import Flask, request
from libfptr10 import *

app = Flask(__name__)

# Функция инициализации ККТ
def initializationKKT(connectType, ip_kas, inn_company):
    fptr = IFptr("")
    ip_kas = "192.168.1.1"
    settings = {
        IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO
    }

    # Настройки в зависимости от типа подключения
    if connectType == "TCP/IP":
        settings.update({
            IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_TCPIP,
            IFptr.LIBFPTR_SETTING_IPADDRESS: ip_kas,
            IFptr.LIBFPTR_SETTING_IPPORT: 5555
        })
    elif connectType == "Удаленный ПК":
        settings.update({
            IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_USB,
            IFptr.LIBFPTR_SETTING_REMOTE_SERVER_ADDR: ip_kas
        })
    elif connectType == "USB":
        settings.update({
            IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_USB
        })

    # Применение настроек и открытие соединения с ККТ
    fptr.setSettings(settings)
    fptr.open()
    isOpened = fptr.isOpened()
    fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_REG_INFO)
    fptr.fnQueryData()

    # Проверка успешного открытия и сравнение ИНН компании
    if isOpened == 1 and inn_company != fptr.getParamString(1018).strip():
        isOpened = 9

    return isOpened, fptr

# Функция разбора JSON данных
def jsonDisassembly(content):
    return (
        content['ip_kassy'], content['inn_сompany'], content['operator'], content['num_predpisania'],
        content['clientInfo'], content['rnm'],
        content['fn'], content['adress'], content['fd_number'], content['fd_type'], content['corr_type'],
        content['sign_calc'], content['check_data'],
        content['shift_number'], content['check_sum'], content['check_cash'], content['check_electron'],
        content['check_prepay'], content['check_prepay_offset'],
        content['check_postpay'], content['barter_pay'], content['sum_NO_VAT'], content['sum_0_VAT'],
        content['sum_10_VAT'], content['sum_18_VAT'],
        content['sum_20_VAT'], content['sum_110_VAT'], content['sum_120_VAT'], content['doc_osn'], content['sno'],
        content['inn_operator'],
        content['check_print'], len(content['items'])
    )

# Функция разбора JSON данных для товаров
def jsonItemsDisassembly(item):
    return (
        item['item_number'], item['item_name'], item['item_sign_sub_calc'], item['item_price'], item['item_quantity'],
        item['item_sum'], item['sign_way_calc'],
        item['item_mera'], item['t1200_VAT_no'], item['t1200_VAT_0'], item['t1200_VAT_10'], item['t1200_VAT_18'],
        item['t1200_VAT_20'], item['t1200_VAT_110'], item['t1200_VAT_120'], item['sign_agent'], item['tel_OP'],
        item['transaction_BPA'], item['tel_PA'], item['tel_OPP'], item['name_OP'], item['adress_OP'], item['inn_OP'],
        item['data_supplier'], item['inn_supplier'], item['dop_rekvizit']
    )

# Функция регистрации товара
def productRegistration(item_number, item_name, item_sign_sub_calc, item_price, item_quantity, item_sum, sign_way_calc,
                        item_mera, t1200_VAT_no, t1200_VAT_0, t1200_VAT_10, t1200_VAT_18,
                        t1200_VAT_20, t1200_VAT_110, t1200_VAT_120, sign_agent, tel_OP, transaction_BPA, tel_PA,
                        tel_OPP, name_OP, adress_OP, inn_OP, data_supplier, inn_supplier, dop_rekvizit, sno, fptr):
    # Если есть поставщик
    if sign_agent == 3:
        fptr.setParam(1225, data_supplier)
        fptr.utilFormTlv()
        suplierInfo = fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)
        fptr.setParam(1222, IFptr.LIBFPTR_AT_ANOTHER)
        fptr.setParam(1226, str(inn_supplier))
        fptr.setParam(1224, suplierInfo)

    # Установка параметров товара
    fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME, item_name)
    fptr.setParam(IFptr.LIBFPTR_PARAM_PRICE, item_price)
    fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, item_quantity)
    fptr.setParam(IFptr.LIBFPTR_PARAM_MEASUREMENT_UNIT,
                  IFptr.LIBFPTR_IU_HOUR if item_mera == 71 else IFptr.LIBFPTR_IU_PIECE)
    fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, IFptr.LIBFPTR_TAX_VAT20 if sno == 1 else IFptr.LIBFPTR_TAX_NO)
    fptr.setParam(IFptr.LIBFPTR_PARAM_USE_ONLY_TAX_TYPE, True)
    fptr.setParam(1214, sign_way_calc)
    fptr.setParam(1212, item_sign_sub_calc)
    fptr.registration()

# Функция закрытия чека
def checkReceiptClosed(fptr):
    while fptr.checkDocumentClosed() < 0:
        continue
    if fptr.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_CLOSED):
        CheckClosed = True
        fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_LAST_DOCUMENT)
        fptr.fnQueryData()
        fiscalSign = fptr.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_SIGN)
        dateTime = fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
    else:
        fptr.cancelReceipt()
        CheckClosed = False
    return CheckClosed, fiscalSign, dateTime

# Главная страница
@app.route("/")
def root():
    return "PCS KKT ATOL SERVER (5034)"

# Обработка POST запроса для загрузки чека
@app.route("/checkProcessing", methods=['POST'])
def loadCheck():
    with open('all_checks3.json', 'r', encoding='utf-8') as f:
        content = json.load(f)

    print(f"Received JSON data: {content}")

    connectType = content['connect']
    operator = content['operator']

    # Обработка операторов 'service-ping' и 'service-X-report'
    if operator in ['service-ping', 'service-X-report']:
        ip_kassy = content['ip_kassy']
        inn_company = content['inn_сompany']
        connectStatus, fptr = initializationKKT(connectType, ip_kassy, inn_company)
        status = 2
        fiscalSign = ""
        dateTime = ""
        if connectStatus == 1:
            status = 1
            if operator == 'service-X-report':
                fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_X)
                fptr.report()
        elif connectStatus == 9:
            status = 9
        return f"{status}={fiscalSign}={dateTime}"

    # Вывод JSON данных перед обработкой
    print(f"Processing JSON data: {content}")

    # Разбор JSON данных для обычной загрузки чека
    ip_kassy, inn_company, operator, num_predpisania, clientInfo, rnm, fn, adress, fd_number, fd_type, corr_type, sign_calc, check_data, shift_number, check_sum, check_cash, check_electron, check_prepay, check_prepay_offset, check_postpay, barter_pay, sum_NO_VAT, sum_0_VAT, sum_10_VAT, sum_18_VAT, sum_20_VAT, sum_110_VAT, sum_120_VAT, doc_osn, sno, inn_operator, check_print, itemsQuantity = jsonDisassembly(content)

    # Инициализация ККТ и проверка срока действия сертификата
    connectStatus, fptr = initializationKKT(connectType, ip_kassy, inn_company)

    now = datetime.datetime.now()
    date_expired = datetime.datetime(2030, 7, 14)
    if now > date_expired:
        connectStatus = 9

    if connectStatus == 1:
        fiscalSign = '0'
        dateTime = '0'

        # Логин оператора
        fptr.setParam(1021, operator)
        fptr.operatorLogin()

        # Установка типа чека
        if fd_type == 1:
            fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE,
                          IFptr.LIBFPTR_RT_SELL if sign_calc == 1 else IFptr.LIBFPTR_RT_SELL_RETURN if sign_calc == 2 else IFptr.LIBFPTR_RT_BUY)
        elif fd_type == 2:
            fptr.setParam(1178, datetime.datetime(int(check_data[6:10]), int(check_data[3:5]), int(check_data[:2])))
            fptr.setParam(1179, num_predpisania)
            fptr.utilFormTlv()
            correctionInfo = fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)
            fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE,
                          IFptr.LIBFPTR_RT_SELL_CORRECTION if sign_calc == 1 else IFptr.LIBFPTR_RT_SELL_RETURN_CORRECTION if sign_calc == 2 else IFptr.LIBFPTR_RT_BUY_CORRECTION)
            fptr.setParam(1173, 0)
            fptr.setParam(1174, 1 if corr_type == 1 else 0)
            fptr.setParam(1177, correctionInfo)

        # Открытие чека
        fptr.openReceipt()

        # Регистрация товаров
        for item in content['items']:
            item_number, item_name, item_sign_sub_calc, item_price, item_quantity, item_sum, sign_way_calc, item_mera, t1200_VAT_no, t1200_VAT_0, t1200_VAT_10, t1200_VAT_18, t1200_VAT_20, t1200_VAT_110, \
                t1200_VAT_120, sign_agent, tel_OP, transaction_BPA, tel_PA, tel_OPP, name_OP, adress_OP, inn_OP, data_supplier, inn_supplier, dop_rekvizit = jsonItemsDisassembly(
                item)

            productRegistration(item_number, item_name, item_sign_sub_calc, item_price, item_quantity, item_sum,
                                sign_way_calc, item_mera, t1200_VAT_no, t1200_VAT_0, t1200_VAT_10, t1200_VAT_18,
                                t1200_VAT_20, \
                                t1200_VAT_110, t1200_VAT_120, sign_agent, tel_OP, transaction_BPA, tel_PA, tel_OPP,
                                name_OP, adress_OP, inn_OP, data_supplier, inn_supplier, dop_rekvizit, sno, fptr)

        # Закрытие чека и получение результатов
        fptr.receiptTotal()
        if check_cash > 0:
            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_CASH)
            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, check_cash)
            fptr.payment()

        if check_electron > 0:
            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_ELECTRONICALLY)
            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, check_electron)
            fptr.payment()

        fptr.closeReceipt()

        # Проверка закрытия чека
        CheckClosed, fiscalSign, dateTime = checkReceiptClosed(fptr)

        if CheckClosed:
            fptr.close()
            status = 1
        else:
            fptr.close()
            status = 4
    elif connectStatus == 9:
        status = 9
        fiscalSign = ""
        dateTime = ""
    else:
        status = 2
        fiscalSign = ""
        dateTime = ""

    print(f"Processed request. Status={status}, fiscalSign={fiscalSign}, dateTime={dateTime}")
    return f"{status}={fiscalSign}={dateTime}"

# Запуск Flask сервера
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5034)
