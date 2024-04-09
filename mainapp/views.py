from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from django.http import HttpResponse
from datetime import datetime
from pymongo import ASCENDING, DESCENDING
import json
import ijson
import pandas as pd

def read_sql_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()
    
def parse_date(date_string):
    """Parses a string to a datetime object."""
    try:
        return datetime.strptime(date_string, '%Y/%m/%d')
    except ValueError as e:
        print(f"Date parsing error: {e}")
        return None
    
def fetch_filtered_data_from_mongodb(min_date=None, max_date=None, skip=0, limit=None):
    client = MongoClient('mongodb://togclick:P%40ssw0rd@localhost:27017')
    db = client['togclick']
    collection = db['togclick']

    # Prepare the filter and projection within an aggregation pipeline
    pipeline = [
        {
            "$addFields": {
                "parsedOrderDate": {
                    "$dateFromString": {
                        "dateString": "$orderDate",
                        "format": "%Y/%m/%d %H:%M:%S"  # Adjust to match the format used in your MongoDB
                    }
                }
            }
        },
        {
            "$match": {}
        }
    ]

    # Add date filters to the match stage if they are provided
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
        pipeline[1]["$match"]["parsedOrderDate"] = date_filter

    # Skip and limit if they are provided
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
            return redirect('dashboard')  # Redirect to the dashboard
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'mainapp/login.html')

@login_required
def dashboard_view(request):
    username_to_customergroup = {
        'YZO': 'YZO',
        'Blueeyes': 'Blueeyes',
        'NSTall': 'NSTall'
    }

    # Get the username of the logged-in user.
    current_username = request.user.username

    if request.GET.get('export') == 'true':
        # If it's an export request, call the export function.
        return export_data_to_excel(request)
    
    elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))  # Default to 10 if not provided.
        min_date = request.GET.get('minDate', '')
        max_date = request.GET.get('maxDate', '')

        client = MongoClient('mongodb://togclick:P%40ssw0rd@localhost:27017')
        db = client['togclick']
        collection = db['togclick']

        # Construct the base query.
        # If the user is not togAdmin, filter data based on the CustomerGroup.
        base_query = {}
        if current_username != 'togAdmin':
            # Use the username to get the specific CustomerGroup,
            # falling back to the username if no specific mapping is found.
            customergroup = username_to_customergroup.get(current_username, current_username)
            base_query['CustomerGroup'] = customergroup

        if min_date and max_date:
            base_query['orderDate'] = {
                '$gte': min_date + ' 00:00:00',
                '$lte': max_date + ' 23:59:59'
            }
        
        total_records = collection.count_documents(base_query)
        filtered_records = collection.count_documents(base_query)

        # Fetch the sorted and paginated data.
        sort_column_number = request.GET.get('order[0][column]', '')
        sort_direction = request.GET.get('order[0][dir]', 'asc')
        sort_column_name = request.GET.get(f'columns[{sort_column_number}][data]', '')
        sort_order = ASCENDING if sort_direction == 'asc' else DESCENDING
        data = list(collection.find(base_query).sort(sort_column_name, sort_order).skip(start).limit(length))
        client.close()

        formatted_data = [
            {
                'Side': item.get('Side', ''),
                'Cust_ID': item.get('Cust_ID', ''),
                'AuthorizationKey': item.get('AuthorizationKey', ''),
                'Customer': item.get('Customer', ''),
                'orderDate': item.get('orderDate', '').split(' ')[0] if item.get('orderDate') else '',
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
                # Continue with other fields...
            }
            for item in data
        ]

        # Prepare the response for DataTables.
        response = {
            "draw": int(request.GET.get('draw', 0)),
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": formatted_data
        }

        return JsonResponse(response)

    else:
        # Render the dashboard page for non-AJAX requests.
        return render(request, 'mainapp/dashboard.html')

def export_data_to_excel(request):
    min_date = request.GET.get('minDate')
    max_date = request.GET.get('maxDate')
    
    print(f"Export requested with min_date: {min_date}, max_date: {max_date}")
    
    data = fetch_filtered_data_from_mongodb(min_date=min_date, max_date=max_date, skip=0, limit=None)
    
    if not data:
        print("No data was returned for export.")

    df = pd.DataFrame(data)
    
    if df.empty:
        print("DataFrame is empty after attempting to convert data to DataFrame.")
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="exported_data.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    return response
def logged_out_view(request):
    return render(request, 'logged_out.html')
