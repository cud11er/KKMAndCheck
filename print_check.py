from libfptr10 import IFptr
import datetime
import json
from tqdm import tqdm


def initializationKKT(inn_company):
    # инициализация драйвера
    fptr = IFptr("")
    # Подгрузка данных для кассы
    with open('settings.json', 'r', encoding='utf-8') as file:
        jsonData = json.load(file)
    ip_kassy = jsonData['ip_kassy']
    connectType = jsonData['connection_Type']
    port = jsonData['port']
    remote_IP_address = jsonData['remote_address_IP']
    # подключение ККТ
    if connectType == "TCP/IP":
        settings = {
            IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
            IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_TCPIP,  # \\\\\\\\\\\\ Для подключения к кассе по TCP/IP
            IFptr.LIBFPTR_SETTING_IPADDRESS: ip_kassy,  # \\\\\\\\\\\\ Для подключения к кассе по TCP/IP
            IFptr.LIBFPTR_SETTING_IPPORT: port  # \\\\\\\\\\\\ Для подключения к кассе по TCP/IP
        }
    if connectType == "Удаленный ПК":
        settings = {
            IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
            IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_USB,
            # \\\\\\\\\\\\ Для удаленного подключения к кассе через ПК
            IFptr.LIBFPTR_SETTING_REMOTE_SERVER_ADDR: remote_IP_address
            # \\\\\\\\\\\\ Для удаленного подключения к кассе через ПК
        }
    if connectType == "USB":
        settings = {
            IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
            IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_USB,  # \\\\\\\\\\\\ Для подключения к кассе по USB
        }

    fptr.setSettings(settings)
    fptr.open()
    isOpened = fptr.isOpened()
    fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_REG_INFO)
    fptr.fnQueryData()
    # if isOpened == 1 and inn_company != fptr.getParamString(1018).strip():
    #    isOpened = 9  # ИНН ККТ не соответсвует ИНН Организации (код ошибки - 9)
    print('\nСтатус готовности к обмену с ККТ: ' + str(isOpened))
    return isOpened, fptr


def jsonDisassembly(content):
    ip_kassy = content['ip_kassy']
    inn_company = content['inn_сompany']
    operator = content['operator']
    num_predpisania = content['num_predpisania']
    clientInfo = content['clientInfo']
    rnm = content['rnm']
    fn = content['fn']
    adress = content['adress']
    fd_number = content['fd_number']
    fd_type = content['fd_type']
    corr_type = content['corr_type']
    sign_calc = content['sign_calc']
    check_data = content['check_data']
    shift_number = content['shift_number']
    check_sum = content['check_sum']
    check_cash = content['check_cash']
    check_electron = content['check_electron']
    check_prepay = content['check_prepay']
    check_prepay_offset = content['check_prepay_offset']
    check_postpay = content['check_postpay']
    barter_pay = content['barter_pay']
    sum_NO_VAT = content['sum_NO_VAT']
    sum_0_VAT = content['sum_0_VAT']
    sum_10_VAT = content['sum_10_VAT']
    sum_18_VAT = content['sum_18_VAT']
    sum_20_VAT = content['sum_20_VAT']
    sum_110_VAT = content['sum_110_VAT']
    sum_120_VAT = content['sum_120_VAT']
    doc_osn = content['doc_osn']
    sno = content['sno']
    inn_operator = content['inn_operator']
    check_print = content['check_print']
    itemsQuantity = len(content['items'])

    return ip_kassy, inn_company, operator, num_predpisania, clientInfo, rnm, fn, adress, fd_number, fd_type, \
        corr_type, sign_calc, check_data, shift_number, check_sum, check_cash, check_electron, check_prepay, \
        check_prepay_offset, check_postpay, barter_pay, sum_NO_VAT, sum_0_VAT, sum_10_VAT, sum_18_VAT, sum_20_VAT, \
        sum_110_VAT, sum_120_VAT, doc_osn, sno, inn_operator, check_print, itemsQuantity


def jsonItemsDisassembly(item):
    item_number = item['item_number']
    item_name = item['item_name']
    item_sign_sub_calc = item['item_sign_sub_calc']
    item_price = item['item_price']
    item_quantity = item['item_quantity']
    item_sum = item['item_sum']
    sign_way_calc = item['sign_way_calc']
    item_mera = item['item_mera']
    t1200_VAT_no = item['t1200_VAT_no']
    t1200_VAT_0 = item['t1200_VAT_0']
    t1200_VAT_10 = item['t1200_VAT_10']
    t1200_VAT_18 = item['t1200_VAT_18']
    t1200_VAT_20 = item['t1200_VAT_20']
    t1200_VAT_110 = item['t1200_VAT_110']
    t1200_VAT_120 = item['t1200_VAT_120']
    sign_agent = item['sign_agent']
    tel_OP = item['tel_OP']
    transaction_BPA = item['transaction_BPA']
    tel_PA = item['tel_PA']
    tel_OPP = item['tel_OPP']
    name_OP = item['name_OP']
    adress_OP = item['adress_OP']
    inn_OP = item['inn_OP']
    data_supplier = item['data_supplier']
    inn_supplier = item['inn_supplier']
    dop_rekvizit = item['dop_rekvizit']
    return item_number, item_name, item_sign_sub_calc, item_price, item_quantity, item_sum, sign_way_calc, item_mera, \
        t1200_VAT_no, t1200_VAT_0, t1200_VAT_10, t1200_VAT_18, t1200_VAT_20, t1200_VAT_110, t1200_VAT_120, sign_agent, \
        tel_OP, transaction_BPA, tel_PA, tel_OPP, name_OP, adress_OP, inn_OP, data_supplier, inn_supplier, dop_rekvizit


def productRegistration(item_number, item_name, item_sign_sub_calc, item_price, item_quantity, item_sum, sign_way_calc,
                        item_mera, t1200_VAT_no, t1200_VAT_0, t1200_VAT_10, t1200_VAT_18,
                        t1200_VAT_20, t1200_VAT_110, t1200_VAT_120, sign_agent, tel_OP, transaction_BPA, tel_PA,
                        tel_OPP, name_OP, adress_OP, inn_OP, data_supplier, inn_supplier, dop_rekvizit, sno, fptr):
    if sign_agent == 3:
        fptr.setParam(1225, data_supplier)
        fptr.utilFormTlv()
        suplierInfo = fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)

        fptr.setParam(1222, IFptr.LIBFPTR_AT_ANOTHER)
        fptr.setParam(1226, str(inn_supplier))
        fptr.setParam(1224, suplierInfo)

    fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME, item_name)
    fptr.setParam(IFptr.LIBFPTR_PARAM_PRICE, item_price)
    fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, item_quantity)
    if item_mera == 71:  # единица измеренения - час
        fptr.setParam(IFptr.LIBFPTR_PARAM_MEASUREMENT_UNIT, IFptr.LIBFPTR_IU_HOUR)
    else:  # единица измеренения - штука
        fptr.setParam(IFptr.LIBFPTR_PARAM_MEASUREMENT_UNIT, IFptr.LIBFPTR_IU_PIECE)

    if sno == 1:
        fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, IFptr.LIBFPTR_TAX_VAT20)  # для ПР НДС - 20% (ОСН)
        fptr.setParam(IFptr.LIBFPTR_PARAM_USE_ONLY_TAX_TYPE, True)
    else:
        fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, IFptr.LIBFPTR_TAX_NO)  # для ПР - НДС не облагается (не ОСН)

    if (item_number != 1) and (item_sign_sub_calc == 10):
        sign_way_calc = 3

    fptr.setParam(1214, sign_way_calc)  # признак способа расчета: полный расчет (4), аванс (3)
    fptr.setParam(1212, item_sign_sub_calc)  # предмет расчета: товар (1), услуга (4), платеж (7)

    fptr.registration()
    return


def checkReceiptClosed(fptr, check_key, content):
    while fptr.checkDocumentClosed() < 0:  # не удалось проверить закрытие чека
        print(fptr.errorDescription())
        continue
    if fptr.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_CLOSED):
        CheckClosed = True
        fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_LAST_DOCUMENT)
        fptr.fnQueryData()
        fiscalSign = fptr.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_SIGN)
        dateTime = fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
        print("Фискальные данные чека: ", fiscalSign, " ", dateTime)

        # Установка check_print в True после успешного закрытия чека
        content[check_key]['check_print'] = True

    elif not fptr.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_CLOSED):  # чек не закрылся, отменяем его
        fptr.cancelReceipt()
        CheckClosed = False

    print("Результат закрытия чека: " + fptr.errorDescription())
    return CheckClosed, fiscalSign, dateTime


def loadCheck():
    # Загрузка чека из файла
    with open('all_checks2.json', 'r', encoding='utf-8') as file:
        content = json.load(file)

    results = []  # Создание массива для записи каждого чека

    # Используем tqdm для отслеживания прогресса
    with tqdm(total=len(content), desc="Обработка чеков", unit="чек") as pbar:
        # Старт обработки тела чека
        for key, check in content.items():
            connectType = check['connect']
            printStatus = check.get('check_print', False)

            if printStatus:
                print(f"Чек с ключом {key} уже напечатан.")
                continue
            else:
                if check['operator'] == 'service-ping':
                    ip_kassy = check['ip_kassy']
                    inn_company = check['inn_сompany']
                    connectStatus, fptr = initializationKKT(inn_company)  # инициализация и подключение ККТ
                    status = 2  # по умолчанию - касса не готова!
                    fiscalSign = ""
                    dateTime = ""
                    if connectStatus == 1:  # касса готова
                        status = 1
                    if connectStatus == 9:  # ИНН не ИНН!
                        status = 9
                    results.append(f"{status}={fiscalSign}={dateTime}")

                elif check['operator'] == 'service-X-report':
                    ip_kassy = check['ip_kassy']
                    inn_company = check['inn_сompany']
                    connectStatus, fptr = initializationKKT(inn_company)  # инициализация и подключение ККТ
                    status = 2
                    fiscalSign = ""
                    dateTime = ""
                    if connectStatus == 1:  # касса готова
                        status = 1
                        fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_X)
                        fptr.report()
                    if connectStatus == 9:  # ИНН не ИНН!
                        status = 9
                    results.append(f"{status}={fiscalSign}={dateTime}")

                else:
                    # Используем функции jsonDisassembly и jsonItemsDisassembly для разбора JSON
                    ip_kassy, inn_company, operator, num_predpisania, clientInfo, rnm, fn, adress, fd_number, fd_type, \
                        corr_type, sign_calc, check_data, shift_number, check_sum, check_cash, check_electron, \
                        check_prepay, check_prepay_offset, check_postpay, barter_pay, sum_NO_VAT, sum_0_VAT, \
                        sum_10_VAT, sum_18_VAT, sum_20_VAT, sum_110_VAT, sum_120_VAT, doc_osn, sno, inn_operator, \
                        check_print, itemsQuantity = jsonDisassembly(check)

                    connectStatus, fptr = initializationKKT(inn_company)  # инициализация и подключение ККТ

                    if connectStatus == 1:  # ККТ готова
                        fiscalSign = '0'
                        dateTime = '0'

                        fptr.setParam(1021, operator)  # кассир
                        fptr.operatorLogin()

                        # Развилка: простой чек или чек коррекции?
                        if fd_type == 1:  # кассовый чек
                            # fptr.setParam(1062, sno)  # применяемая система налогообложения  # ОШИБКА ПРИ ИСПОЛЬЗОВАНИИ !!!
                            if sign_calc == 1:
                                fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_SELL)  # ПРИХОД
                            if sign_calc == 2:
                                fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE,
                                              IFptr.LIBFPTR_RT_SELL_RETURN)  # ВОЗВРАТ ПРИХОДА
                            if sign_calc == 3:
                                fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_BUY)  # РАСХОД

                        if fd_type == 2:  # чек коррекции
                            # fptr.setParam(1062, sno)  # применяемая система налогообложения  # ОШИБКА ПРИ ИСПОЛЬЗОВАНИИ !!!
                            fptr.setParam(1178, datetime.datetime(int(check_data[6:10]), int(check_data[3:5]),
                                                                  int(check_data[
                                                                      :2])))  # нужны, если по предписанию ФНС
                            fptr.setParam(1179, num_predpisania)  # нужны, если по предписанию ФНС
                            fptr.utilFormTlv()  # нужны, если по предписанию ФНС
                            correctionInfo = fptr.getParamByteArray(
                                IFptr.LIBFPTR_PARAM_TAG_VALUE)  # нужны, если по предписанию ФНС

                            if sign_calc == 1:
                                fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE,
                                              IFptr.LIBFPTR_RT_SELL_CORRECTION)  # КОРРЕКЦИЯ ПРИХОДА
                            if sign_calc == 2:
                                fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE,
                                              IFptr.LIBFPTR_RT_SELL_RETURN_CORRECTION)  # КОРРЕКЦИЯ ВОЗВРАТА ПРИХОДА
                            if sign_calc == 3:
                                fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE,
                                              IFptr.LIBFPTR_RT_BUY_CORRECTION)  # КОРРЕКЦИЯ РАСХОДА

                            fptr.setParam(1173, 0)  # тип коррекции - самостоятельно (по предписанию - 1)
                            fptr.setParam(1174, correctionInfo)  # составной реквизит, состоит из "1178" и "1179"
                            if doc_osn != 0:
                                fptr.setParam(1192, str(doc_osn))

                        # дальше - общее и для чека и для коррекции

                        fptr.setParam(1008, clientInfo)  # данные клиента (приходит пустая строка)
                        # !!! уБРАТЬ КОММЕНТАРИИ НИЖЕ ЕСЛИ clientInfo НЕ ПУСТОЙ !!!
                        # if not check_print:
                        #     fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY, True)  # чек не печатаем
                        fptr.openReceipt()

                        for i in range(itemsQuantity):
                            item_number, item_name, item_sign_sub_calc, item_price, item_quantity, item_sum, \
                                sign_way_calc, item_mera, t1200_VAT_no, t1200_VAT_0, t1200_VAT_10, t1200_VAT_18, \
                                t1200_VAT_20, t1200_VAT_110, t1200_VAT_120, sign_agent, tel_OP, transaction_BPA, \
                                tel_PA, tel_OPP, name_OP, adress_OP, inn_OP, data_supplier, inn_supplier, \
                                dop_rekvizit = jsonItemsDisassembly(check['items'][i])

                            productRegistration(item_number, item_name, item_sign_sub_calc, item_price, item_quantity,
                                                item_sum, sign_way_calc, item_mera, t1200_VAT_no, t1200_VAT_0,
                                                t1200_VAT_10, t1200_VAT_18, t1200_VAT_20, t1200_VAT_110, t1200_VAT_120,
                                                sign_agent, tel_OP, transaction_BPA, tel_PA, tel_OPP, name_OP,
                                                adress_OP, inn_OP, data_supplier, inn_supplier, dop_rekvizit, sno, fptr)

                        if check_cash > 0:
                            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_CASH)
                            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, check_cash)
                            fptr.payment()
                        if check_electron > 0:
                            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_ELECTRONICALLY)
                            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, check_electron)
                            fptr.payment()

                        # if check_prepay > 0:
                        #    fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_PREPAID) # аванс

                        if check_postpay > 0:
                            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_CREDIT)  # кредит
                            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, check_postpay)
                            fptr.payment()
                        if check_prepay_offset > 0:
                            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE,
                                          IFptr.LIBFPTR_PT_PREPAID)  # зачет предоплаты (аванса)
                            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, check_prepay_offset)
                            fptr.payment()

                        fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, IFptr.LIBFPTR_TAX_VAT20)
                        fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_SUM, sum_20_VAT)
                        fptr.receiptTax()

                        fptr.setParam(IFptr.LIBFPTR_PARAM_SUM, check_sum)
                        fptr.receiptTotal()

                        fptr.closeReceipt()  # закрытие чека
                        CheckClosed, fiscalSign, dateTime = checkReceiptClosed(fptr, key,
                                                                               content)  # обработка результата операции
                        status = 0
                        if CheckClosed:
                            status = 1
                        fptr.close()
                    # !!! Снять комментарии ниже при наличии корректного ИНН организации !!!
                    # elif connectStatus ==9:
                    #    status = 9
                    #    fiscalSign = ""
                    #    dateTime = ""
                    #    print("ИНН ККТ не соответствует ИНН организации!")
                    else:
                        status = 2
                        fiscalSign = ""
                        dateTime = ""
                        print("КАССА ЗАНЯТА!")

                    results.append(f"{status}={fiscalSign}={dateTime}")

            pbar.update(1)  # Обновляем прогрессбар на каждой итерации

    # Сохраняем обновленные данные в файл
    with open('all_checks2.json', 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False)

    return results


def testKkt():
    # Инициализация драйвера
    fptr = IFptr("")
    version = fptr.version()

    print('version')
    print(version)
    with open('settings.json', 'r', encoding='utf-8') as file:
        jsonData = json.load(file)
    ip_kassy = jsonData['ip_kassy']
    port = jsonData['port']

    # Подключение ККТ
    settings = {
        IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
        IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_TCPIP,
        IFptr.LIBFPTR_SETTING_IPADDRESS: ip_kassy,
        IFptr.LIBFPTR_SETTING_IPPORT: port
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

    # fptr.setParam(IFptr.LIBFPTR_PARAM_PRINT_REPORT, False)
    # fptr.deviceReboot()

    return 'Cмена закрыта'


def testOFD():
    # Инициализация драйвера
    fptr = IFptr("")
    version = fptr.version()
    print('version')
    print(version)
    # Подключение ККТ
    with open('settings.json', 'r', encoding='utf-8') as file:
        jsonData = json.load(file)
    ip_kassy = jsonData['ip_kassy']
    port = jsonData['port']
    settings = {
        IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
        IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_TCPIP,
        IFptr.LIBFPTR_SETTING_IPADDRESS: ip_kassy,
        IFptr.LIBFPTR_SETTING_IPPORT: port
    }
    fptr.setSettings(settings)
    fptr.open()
    isOpened = fptr.isOpened()
    print(f'isOpened {isOpened}')
    fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_OFD_TEST)
    fptr.report()

    return 'OK'


def get_INN():
    # Инициализация драйвера
    fptr = IFptr("")
    version = fptr.version()
    print('version')
    print(version)
    with open('settings.json', 'r', encoding='utf-8') as file:
        jsonData = json.load(file)
    ip_kassy = jsonData['ip_kassy']
    port = jsonData['port']

    # Подключение ККТ
    settings = {
        IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
        IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_TCPIP,
        IFptr.LIBFPTR_SETTING_IPADDRESS: ip_kassy,
        IFptr.LIBFPTR_SETTING_IPPORT: port
    }
    fptr.setSettings(settings)
    fptr.open()
    isOpened = fptr.isOpened()
    print(f"isOpened {isOpened}")

    fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_REG_INFO)
    fptr.fnQueryData()
    INN = fptr.getParamString(1018)
    print(f'ИНН {INN}')
    return INN


if __name__ == "__main__":
    while True:
        # Выводим меню для пользователя
        print("Выберите действие:")
        print("1. Начать печать чеков из JSON")
        print("2. Тест ОФД")
        print('3. Получить ИНН')
        print('4. Тест ККМ')
        print('5. Выход')

        # Получаем выбор пользователя
        choice = input("Введите цифру выбора: ")

        # Обрабатываем выбор пользователя
        if choice == "1":
            loadCheck()  # Вызываем функцию loadCheck()
        elif choice == "2":
            testOFD()
        elif choice == '3':
            get_INN()
        elif choice == '4':
            testKkt()
        elif choice == '5':
            print("Выход из программы.")
            exit()
        else:
            print("Некорректный ввод. Попробуйте снова.")