from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from pathlib import Path
import json
import ijson
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import pandas as pd
from django.http import HttpResponse

def read_sql_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

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
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))  # Default to 10 if not provided
        page = start // length + 1
        
        # Connect to MongoDB
        client = MongoClient('mongodb://togclick:P%40ssw0rd@localhost:27017')
        db = client['togclick']
        collection = db['togclick']
        
        # Calculate total number of records
        total_records = collection.count_documents({})
        
        # Fetch paginated data
        data = list(collection.find({}).skip(start).limit(length))
        client.close()
        

        formatted_data = [
            {
                'Side': item.get('Side', ''),
                'Cust_ID': item.get('Cust_ID', ''),
                'AuthorizationKey': item.get('AuthorizationKey', ''),
                'Customer': item.get('Customer', ''),
                'orderDate': item.get('orderDate', ''),
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

        # Prepare the response
        response = {
            "draw": int(request.GET.get('draw', 0)),
            "recordsTotal": total_records,
            "recordsFiltered": total_records,
            "data": formatted_data
        }
        
        return JsonResponse(response)
        #return render(request, 'mainapp/dashboard.html', {'data': formatted_data})
    else:
        return render(request, 'mainapp/dashboard.html')
    
def export_all_data(request):
# Connect to MongoDB
    client = MongoClient('mongodb://togclick:P%40ssw0rd@localhost:27017')
    db = client['togclick']
    collection = db['togclick']
        
    # Calculate total number of records
    total_records = collection.count_documents({})
        
    # Fetch paginated data
    data = list(collection.find({}))
    client.close()
    
    df = pd.DataFrame(list(data))
    # Create a Pandas Excel writer using openpyxl as the engine
    with pd.ExcelWriter('togclick_export.xlsx', engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    # Read the saved Excel file and create an HttpResponse
    with open('togclick_export.xlsx', 'rb') as excel:
        data = excel.read()
        
    response = HttpResponse(content=data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="togclick_export.xlsx"'
    return response

def logged_out_view(request):
    return render(request, 'logged_out.html')
