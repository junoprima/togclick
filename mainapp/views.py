from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from pymongo import MongoClient
from datetime import datetime
import pandas as pd

def parse_date(date_string):
    try:
        return datetime.strptime(date_string, '%Y/%m/%d')
    except ValueError as e:
        print(f"Date parsing error: {e}")
        return None

def fetch_filtered_data_from_mongodb(min_date=None, max_date=None, skip=0, limit=None, search_value=None):
    client = MongoClient('mongodb://togclick:P%40ssw0rd@localhost:27017')
    db = client['togclick']
    collection = db['togclick']

    pipeline = [{"$match": {}}]

    if min_date or max_date:
        date_filter = {}
        if min_date:
            parsed_min_date = parse_date(min_date)
            if parsed_min_date:
                date_filter["$gte"] = parsed_min_date
        if max_date:
            parsed_max_date = parse_date(max_date)
            if parsed_max_date:
                date_filter["$lte"] = parsed_max_date
        pipeline[0]["$match"]["orderDate"] = date_filter

    if search_value:
        search_filter = {
            "$or": [
                {"OrderCode": {"$regex": search_value, "$options": "i"}},
                {"Customer": {"$regex": search_value, "$options": "i"}},
                {"AuthorizationKey": {"$regex": search_value, "$options": "i"}}
            ]
        }
        pipeline[0]["$match"].update(search_filter)

    if skip:
        pipeline.append({"$skip": skip})
    if limit:
        pipeline.append({"$limit": limit})

    try:
        cursor = collection.aggregate(pipeline)
        data = list(cursor)
    finally:
        client.close()

    return data


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'mainapp/login.html')

@login_required
def dashboard_view(request):
    username_to_customergroup = {
        'YZO': 'YZO',
        'Blueeyes': 'Blueeyes',
        'NSTall': 'NSTall',
        'togAdmin': None,
    }

    current_username = request.user.username
    customergroup = username_to_customergroup.get(current_username, current_username)

    if request.GET.get('export') == 'true':
        return export_data_to_excel(request, customergroup)

    elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        min_date = request.GET.get('minDate', '')
        max_date = request.GET.get('maxDate', '')
        search_value = request.GET.get('search[value]', '')

        client = MongoClient('mongodb://togclick:P%40ssw0rd@13.251.191.127:27017')
        db = client['togclick']
        collection = db['togclick']

        base_query = {}
        if customergroup:
            base_query['CustomerGroup'] = customergroup

        if min_date and max_date:
            try:
                base_query['orderDate'] = {
                    '$gte': datetime.strptime(min_date, '%Y/%m/%d'),
                    '$lte': datetime.strptime(max_date, '%Y/%m/%d')
                }
            except ValueError:
                pass  # handle bad date format if needed

        if search_value:
            base_query["$or"] = [
                {"OrderCode": {"$regex": search_value, "$options": "i"}},
                {"Customer": {"$regex": search_value, "$options": "i"}},
                {"AuthorizationKey": {"$regex": search_value, "$options": "i"}}
            ]

        total_records = collection.count_documents({})
        filtered_records = collection.count_documents(base_query)

        data = list(collection.find(base_query).sort([
            ("orderDate", -1),
            ("AuthorizationKey", 1),
            ("OrderCode", -1),
            ("Side", 1)
        ]).skip(start).limit(length).allow_disk_use(True))

        client.close()
        formatted_data = [
            {
                'Side': item.get('Side', ''),
                'Cust_ID': item.get('Cust_ID', ''),
                'AuthorizationKey': item.get('AuthorizationKey', ''),
                'Customer': item.get('Customer', ''),
                'orderDate': item.get('orderDate').strftime('%Y-%m-%d') if isinstance(item.get('orderDate'), datetime.datetime) else '',
                'OrderCode': item.get('OrderCode', ''),
                'Express': item.get('Express', ''),
                'ProductionNumber': item.get('ProductionNumber', ''),
                'ShopNumber': item.get('ShopNumber', ''),
                'Est_ReadyDate': item.get('Est_ReadyDate', ''),
                'Update_Est_FinishedDate': item.get('Update_Est_FinishedDate', ''),
                'Customer_RequireDate': item.get('Customer_RequireDate', ''),
                'FinishedDate': item.get('FinishedDate', ''),
                'DispatchedDate': item.get('DispatchedDate', ''),
                'LensType': item.get('LensType', ''),
                'Corridor': item.get('Corridor', ''),
                'Degresstion': item.get('Degresstion', ''),
                'LensIndex': item.get('LensIndex', ''),
                'Dia': item.get('Dia', ''),
                'SubDia': item.get('SubDia', ''),
                'Color': item.get('Color', ''),
                'Coat': item.get('Coat', ''),
                'SPH': item.get('SPH', ''),
                'CYL': item.get('CYL', ''),
                'Axis': item.get('Axis', ''),
                'Addition': item.get('Addition', ''),
                'DECX': item.get('DECX', ''),
                'DECY': item.get('DECY', ''),
                'PSMH': item.get('PSMH', ''),
                'PSMH_VALUE': item.get('PSMH_VALUE', ''),
                'PSMV': item.get('PSMV', ''),
                'PSMV_VALUE': item.get('PSMV_VALUE', ''),
                'Tint': item.get('Tint', ''),
                'TINT_VALUE': item.get('TINT_VALUE', ''),
                'ORDER_TINT_GRADIENT': item.get('ORDER_TINT_GRADIENT', ''),
                'Material': item.get('Material', ''),
                'Cutting': item.get('Cutting', ''),
                'UV': item.get('UV', ''),
                'Qty': item.get('Qty', ''),
                'OrderStatus': item.get('OrderStatus', ''),
                'Attachment': item.get('Attachment', ''),
                'Remark': item.get('Remark', ''),
                'HorBox': item.get('HorBox', ''),
                'VerBox': item.get('VerBox', ''),
                'DBL': item.get('DBL', ''),
                'FarPD': item.get('FarPD', ''),
                'FittingHeight': item.get('FittingHeight', ''),
                'NearPD': item.get('NearPD', ''),
                'SegHeight': item.get('SegHeight', ''),
                'CVD': item.get('CVD', ''),
                'FFA': item.get('FFA', ''),
                'PTA': item.get('PTA', ''),
                'NormalReadingDistance': item.get('NormalReadingDistance', ''),
                'CustomizedInset': item.get('CustomizedInset', ''),
                'Pending': item.get('Pending', ''),
                'FlashMirror': item.get('FlashMirror', ''),
                'RoundShape': item.get('RoundShape', ''),
                'PreOptimized': item.get('PreOptimized', ''),
                'FrameType': item.get('FrameType', ''),
                'SharpEdge': item.get('SharpEdge', ''),
                'OC_Filename': item.get('OC_Filename', ''),
                'FrameShape': item.get('FrameShape', ''),
                'DiaOval': item.get('DiaOval', ''),
                'codemax5': item.get('codemax5', ''),
                'descriptionmax5': item.get('descriptionmax5', ''),
                'CustomerGroup': item.get('CustomerGroup', ''),
            }
            for item in data
        ]

        response = {
            "draw": int(request.GET.get('draw', 1)),
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": formatted_data
        }

        return JsonResponse(response)
    else:
        return render(request, 'mainapp/dashboard.html')


def export_data_to_excel(request, customergroup=None):
    min_date = request.GET.get('minDate')
    max_date = request.GET.get('maxDate')
    search_value = request.GET.get('search[value]', '')

    client = MongoClient('mongodb://togclick:P%40ssw0rd@13.251.191.127:27017')
    db = client['togclick']
    collection = db['togclick']

    query = {}
    if customergroup:
        query['CustomerGroup'] = customergroup

    if min_date and max_date:
        try:
            query['orderDate'] = {
                '$gte': datetime.strptime(min_date, '%Y/%m/%d'),
                '$lte': datetime.strptime(max_date, '%Y/%m/%d')
            }
        except ValueError:
            pass

    if search_value:
        query["$or"] = [
            {"OrderCode": {"$regex": search_value, "$options": "i"}},
            {"Customer": {"$regex": search_value, "$options": "i"}},
            {"AuthorizationKey": {"$regex": search_value, "$options": "i"}}
        ]

    data = list(collection.find(query).sort([
        ("orderDate", -1),
        ("AuthorizationKey", 1),
        ("OrderCode", -1),
        ("Side", 1)
    ]).allow_disk_use(True))
    client.close()

    df = pd.DataFrame(data)

    if df.empty:
        return HttpResponse("No data available for the selected filters.", content_type='text/plain')

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="exported_data.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    return response

def logged_out_view(request):
    return render(request, 'logged_out.html')
