from django.http import HttpResponse,HttpResponseRedirect
from django.urls import reverse
import datetime
from django import template
from django.utils import timezone
from keras.models import load_model
import keras.backend as tf
from fraud.models import Aadhar,Bank_formalities,Bank_details,bank_statement,predicted_features
from django.shortcuts import render,get_object_or_404
from fraud.forms import Authentic
from django.urls import reverse
import numpy as np
import os
import random
import pickle


from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate,login,logout
#from codefundo.models import user_details,gov_fund,track_users
from datetime import datetime,date,timedelta
path = os.path.join(os.getcwd(),'fraud')


def index(request):
    return render(request,"fraud/index.html")   

def itofficials(request):
    return render(request,"fraud/itofficials.html")

def getFamily(address):
    family = Bank_formalities.objects.filter(address = address)
    return family

def process(familyaadhar):
    bankStatements = [bank_statement.objects.filter(aadhar_no=aadhar)[0] for aadhar in familyaadhar]
        
    lEdu=0             
    hEdu=0                         
    jewellery=0        
    cars=0             
    bikes=0            
    tax=0              
    credit=0           
    debit=0
    
    for bankstatement in bankStatements:
        lEdu+= bankstatement.lEdu
        hEdu+= bankstatement.hEdu
        jewellery+= bankstatement.jewellery
        cars+= bankstatement.cars
        bikes+= bankstatement.bikes
        tax+= bankstatement.tax
        credit+= bankstatement.credit
        debit+= bankstatement.debit
        
     
    area = bankStatements[0].area
    aadhar = bankStatements[0].aadhar_no
    input_data = [lEdu,hEdu,jewellery,cars,bikes,tax,credit,debit]
    if area == 'slum':
        input_data += [1,0,0]
    elif area == 'middle':
        input_data += [0,1,0]
    else:
        input_data += [0,0,1]
    
    model = load_model(os.path.join(path, 'data.h5'))
    with open(os.path.join(path,'scaler'), 'rb') as sc:
        scaler = pickle.load(sc)
    
    print(input_data)
    input_data = np.array( [input_data])
    input_data = scaler.transform(input_data)
    
    input_data.dtype = 'float'
    print(type(input_data),input_data.shape)
    print(input_data)
    final_data = model.predict(input_data)
    print(final_data)

    #save all the final data in predicted features
    checkForPredict = predicted_features.objects.filter(aadhar_no=aadhar)
    
    if len(checkForPredict) == 0:
        form = predicted_features()
    else:
	    form = predicted_features.objects.filter(aadhar_no=aadhar)[0]
    # i = form.save(commit=False)

    #mark model as done
    citizen = Aadhar.objects.filter(aadhar_no=aadhar)[0]
    print(citizen)
    print(form)
    form.lEdu = lEdu
    form.hEdu = hEdu
    form.jewellery = jewellery
    form.cars = cars
    form.bikes = bikes
    form.tax = tax
    form.credit = credit
    form.debit = debit
    form.aadhar_no = aadhar
    form.fraud = True if final_data[0][0] > 0.5 else False
    form.save()
   
        
    #print(familyMembers) #family members of type bankformalities


def fraud_list(aadharno):
    allUsers = Aadhar.objects.filter(aadhar_no=aadharno)
    for user in allUsers:
 

        familyMembers = getFamily(user.address)
        process([familyMember.aadhar_no for familyMember in familyMembers])
    return allUsers[0].aadhar_no


    

def new_case(request):
   
    if request.method=="POST":
        aadharno=request.POST.get("aadharno")
        lEdu=request.POST.get("lEdu")
        hEdu=request.POST.get("hEdu")
        area=request.POST.get("area")
        jewellery=request.POST.get("jewellery")
        cars=request.POST.get("cars")
        bikes=request.POST.get("bikes")
        tax=request.POST.get("tax")
        credit=request.POST.get("credit")
        debit=request.POST.get("debit")
        #get the user with that particular aadhar number
        print(aadharno)
        
        #get the account number from the aadhar number for changing the data
        fraudUser = Bank_formalities.objects.filter(aadhar_no=aadharno) 
        for fraudUser in fraudUser:
            accountNo = fraudUser 
        
        #get the bank statements of that particular account number
        fraudAccount = Bank_details.objects.filter(ac_no = accountNo.ac_no)
        for fraudAccount in fraudAccount:
            print(fraudAccount.bank_statement)
        
        #till here fraudAccount contains the bank_statement details of the fraud account and we need to rewrite that
        fraudAccount.bank_statement.lEdu = lEdu
        fraudAccount.bank_statement.hEdu = hEdu
        fraudAccount.bank_statement.area = area
        fraudAccount.bank_statement.jewellery = jewellery
        fraudAccount.bank_statement.cars = cars
        fraudAccount.bank_statement.bikes = bikes
        fraudAccount.bank_statement.tax = tax
        fraudAccount.bank_statement.credit = credit
        fraudAccount.bank_statement.debit = debit
        fraudAccount.bank_statement.save()
        
        head = fraud_list(aadharno)
        print(head)
                
        predict = predicted_features.objects.filter(aadhar_no = head)
        return render(request,"fraud/generate_report.html",{"predict":predict})
    


    return render(request,"fraud/new_case.html",{},)



def user_login(request):
    if request.method=="POST":
        username=request.POST.get("username")
        password=request.POST.get("password")

        user=authenticate(username=username,password=password)


        if user:
            login(request,user)
            return HttpResponseRedirect(reverse("fraud:itofficials"))
        else:
            return render(request,"fraud/return_invalid_user.html")
    else :
        return render(request,"fraud/login.html",{},)

def generate_list(request):
    predict = predicted_features.objects.all()
    return render(request,"fraud/generate_list.html",{"predict":predict})

def generate_report(request,aadharno):
    predict = predicted_features.objects.filter(aadhar_no = aadharno)
    return render(request,"fraud/generate_report.html",{"predict":predict})
