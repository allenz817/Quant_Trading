from futu import *
import time

quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
simple_filter = SimpleFilter()
simple_filter.filter_min = 2
simple_filter.filter_max = 1000
simple_filter.stock_field = StockField.CUR_PRICE
simple_filter.is_no_filter = False
# simple_filter.sort = SortDir.ASCEND

financial_filter = FinancialFilter()
financial_filter.filter_min = 0.5
financial_filter.filter_max = 50
financial_filter.stock_field = StockField.CURRENT_RATIO
financial_filter.is_no_filter = False
financial_filter.sort = SortDir.ASCEND
financial_filter.quarter = FinancialQuarter.ANNUAL

custom_filter = CustomIndicatorFilter()
custom_filter.ktype = KLType.K_DAY
custom_filter.stock_field1 = StockField.MA10
custom_filter.stock_field2 = StockField.MA60
custom_filter.relative_position = RelativePosition.MORE
custom_filter.is_no_filter = False

nBegin = 0
last_page = False
ret_list = list()
while not last_page:
    nBegin += len(ret_list)
    ret, ls = quote_ctx.get_stock_filter(market=Market.HK, filter_list=[simple_filter, financial_filter, custom_filter], begin=nBegin)  # filter with simple, financial and indicator filter for HK market
    if ret == RET_OK:
        last_page, all_count, ret_list = ls
        print('all count = ', all_count)
        for item in ret_list:
            print(item.stock_code)  # Get the stock code
            print(item.stock_name)  # Get the stock name
            print(item[simple_filter])   # Get the value of the variable corresponding to simple_filter
            print(item[financial_filter])   # Get the value of the variable corresponding to financial_filter 
            print(item[custom_filter])  # Get the value of custom_filter
    else:
        print('error: ', ls)
        break
    time.sleep(3)  # Sleep for 3 seconds to avoid trigger frequency limitation

quote_ctx.close()  # After using the connection, remember to close it to prevent the number of connections from running out
