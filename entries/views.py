from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.conf import settings
from django.contrib import messages
import os

import pandas as pd

from .models import Entry, Company, Category, Subcategory
from .forms import CompanyForm, ReceiptForm, PaymentForm, ReceiptExcelUploadForm, PaymentExcelUploadForm, CategoryForm, SubcategoryForm


def admin_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'admin':
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return login_required(user_passes_test(lambda u: u.role == 'admin', login_url='login')(_wrapped_view_func))


@admin_required
def create_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dash')  # Redirect to the list of companies or any other page
    else:
        form = CompanyForm()
    return render(request, 'admin/create_company.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.role == 'accountant', login_url='login')
def create_receipt(request, company_name):
    print(company_name)
    company = Company.objects.get(name=company_name)

    if request.method == 'POST':
        form = ReceiptForm(request.POST, user=request.user, company=company)
        if form.is_valid():
            form.save(commit=True, company=company)
            return redirect('accountant_dash')  # Replace with your success URL
    else:
        form = ReceiptForm(user=request.user, company=company)
    return render(request, 'accountant/create_receipt.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.role == 'accountant', login_url='login')
def create_payment(request, company_name):
    company = get_object_or_404(Company, name =company_name)

    if request.method == 'POST':
        form = PaymentForm(request.POST, user=request.user, company=company)
        if form.is_valid():
            form.save(commit=True, company=company)
            return redirect('accountant_dash')  # Replace with your success URL
    else:
        form = PaymentForm(user=request.user, company=company)
    return render(request, 'accountant/create_payment.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.role == 'accountant', login_url='login')
def create_big_receipt(request, company_name):
    company = get_object_or_404(Company, name=company_name)

    if request.method == 'POST':
        form = ReceiptForm(request.POST, user=request.user, company=company, is_irregular=True)
        if form.is_valid():
            form.save(commit=True, company=company, is_irregular=True)
            return redirect('accountant_dash')  # Replace with your success URL
    else:
        form = ReceiptForm(user=request.user, company=company, is_irregular=True)
    return render(request, 'accountant/create_large_receipt.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.role == 'accountant', login_url='login')
def create_big_payment(request, company_name):
    company = get_object_or_404(Company, name=company_name)

    if request.method == 'POST':
        form = PaymentForm(request.POST, user=request.user, company=company, is_irregular=True)
        if form.is_valid():
            form.save(commit=True, company=company, is_irregular=True)
            return redirect('accountant_dash')  # Replace with your success URL
    else:
        form = PaymentForm(user=request.user, company=company, is_irregular=True)
    return render(request, 'accountant/create_large_payment.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.role == 'accountant', login_url='login')
def receipt_template_download(request):
    # Path to the PDF file to be downloaded
    file_path = os.path.join(settings.MEDIA_ROOT, 'receipts_template.xlsx')

    # Open the PDF file for reading
    with open(file_path, 'rb') as f:
        excel_file = f.read()

    # Set the appropriate content type for PDF
    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


    # Create an HttpResponse with the PDF content
    response = HttpResponse(excel_file, content_type=content_type)

    # Set the Content-Disposition header to prompt the user to download the file
    response['Content-Disposition'] = 'attachment; filename="receipts_template.xlsx"'

    return response

@login_required
@user_passes_test(lambda u: u.role == 'accountant', login_url='login')
def payment_template_download(request):
    # Path to the PDF file to be downloaded
    file_path = os.path.join(settings.MEDIA_ROOT, 'payments_template.xlsx')

    # Open the PDF file for reading
    with open(file_path, 'rb') as f:
        excel_file = f.read()

    # Set the appropriate content type for PDF
    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


    # Create an HttpResponse with the PDF content
    response = HttpResponse(excel_file, content_type=content_type)

    # Set the Content-Disposition header to prompt the user to download the file
    response['Content-Disposition'] = 'attachment; filename="payments_template.xlsx"'

    return response

@login_required
@user_passes_test(lambda u: u.role == 'accountant', login_url='login')
def receipt_excel_upload(request):
    if request.method == 'POST':
        form = ReceiptExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            
            # Load Excel file into pandas DataFrame
            try:
                df = pd.read_excel(excel_file, engine='openpyxl')
            except Exception as e:
                messages.error(request, 'Failed to read Excel file: ' + str(e))
                return render(request, 'accountant/receipt_excel_upload.html', {'form': form})
            
            currency_map = {
                'rupee'.lower(): 'INR',
                'dollar'.lower(): 'USD',
                'euro'.lower(): 'EUR',
                'dirham'.lower(): 'AED',
                'riyal'.lower(): 'AED'
            }

            entries = []

            for index, row in df.iterrows():
                try:
                    company_name = row['company']
                    category_name = row['category']
                    subcategory_name = row['subcategory']
                    currency_name = row['currency']

                    company_instance = Company.objects.get(name=company_name)
                    category_instance = Category.objects.get(name=category_name)
                    subcategory_instance = Subcategory.objects.get(name=subcategory_name, category=category_instance)
                    currency_code = currency_map.get(currency_name.lower())

                    entry = Entry(
                        user=request.user,  # Assign current user
                        entry_type='receipt',
                        currency=currency_code,
                        receipts=row['receipts'],
                        date=row['date'],
                        description=row['description'],
                        category=category_instance,
                        company=company_instance,
                        subcategory=subcategory_instance,
                        from_excel=True
                    )
                    entries.append(entry)

                except Company.DoesNotExist:
                    messages.error(request, f"Row {index + 1}: Company '{company_name}' does not exist.")
                except Category.DoesNotExist:
                    messages.error(request, f"Row {index + 1}: Category '{category_name}' does not exist.")
                except Subcategory.DoesNotExist:
                    messages.error(request, f"Row {index + 1}: Subcategory '{subcategory_name}' does not exist for Category '{category_name}'.")
                except KeyError as e:
                    messages.error(request, f"Row {index + 1}: Missing expected column '{e.args[0]}'.")
                except Exception as e:
                    messages.error(request, f"Row {index + 1}: {str(e)}")

            if messages.get_messages(request):
                # If there are any error messages, render the form again with errors
                return render(request, 'accountant/receipt_excel_upload.html', {'form': form})

            # Bulk create entries to improve performance
            Entry.objects.bulk_create(entries)

            messages.success(request, 'Entries successfully uploaded and created.')
            return redirect('accountant_dash')  # Redirect to entry list view
            
    else:
        form = ReceiptExcelUploadForm()
    
    return render(request, 'accountant/receipt_excel_upload.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.role == 'accountant', login_url='login')
def payment_excel_upload(request):
    if request.method == 'POST':
        form = PaymentExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            
            # Load Excel file into pandas DataFrame
            try:
                df = pd.read_excel(excel_file, engine='openpyxl')
            except Exception as e:
                messages.error(request, 'Failed to read Excel file: ' + str(e))
                return render(request, 'accountant/payment_excel_upload.html', {'form': form})

            currency_map = {
                'rupee'.lower(): 'INR',
                'dollar'.lower(): 'USD',
                'euro'.lower(): 'EUR',
                'dirham'.lower(): 'AED',
                'riyal'.lower(): 'AED'
            }

            entries = []

            for index, row in df.iterrows():
                try:
                    company_name = row['company']
                    category_name = row['category']
                    subcategory_name = row['subcategory']
                    currency_name = row['currency']

                    company_instance = Company.objects.get(name=company_name)
                    category_instance = Category.objects.get(name=category_name)
                    subcategory_instance = Subcategory.objects.get(name=subcategory_name, category=category_instance)
                    currency_code = currency_map.get(currency_name.lower())

                    entry = Entry(
                        user=request.user,  # Assign current user
                        entry_type='payment',
                        currency=currency_code,
                        payments=row['payments'],
                        date=row['date'],
                        description=row['description'],
                        category=category_instance,
                        company=company_instance,
                        subcategory=subcategory_instance,
                        from_excel=True
                    )
                    entries.append(entry)

                except Company.DoesNotExist:
                    messages.error(request, f"Row {index + 1}: Company '{company_name}' does not exist.")
                except Category.DoesNotExist:
                    messages.error(request, f"Row {index + 1}: Category '{category_name}' does not exist.")
                except Subcategory.DoesNotExist:
                    messages.error(request, f"Row {index + 1}: Subcategory '{subcategory_name}' does not exist for Category '{category_name}'.")
                except KeyError as e:
                    messages.error(request, f"Row {index + 1}: Missing expected column '{e.args[0]}'.")
                except Exception as e:
                    messages.error(request, f"Row {index + 1}: {str(e)}")

            if messages.get_messages(request):
                # If there are any error messages, render the form again with errors
                return render(request, 'accountant/payment_excel_upload.html', {'form': form})

            # Bulk create entries to improve performance
            Entry.objects.bulk_create(entries)

            messages.success(request, 'Entries successfully uploaded and created.')
            return redirect('accountant_dash')  # Redirect to entry list view
            
    else:
        form = PaymentExcelUploadForm()
    
    return render(request, 'accountant/payment_excel_upload.html', {'form': form})


@login_required
def edit_receipt(request, id):
    entry = get_object_or_404(Entry, pk=id)
    if request.method == 'POST':
        form = ReceiptForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()

            if request.user.role == 'accountant':
                return redirect('accountant_dash')  # Redirect to the list of companies or any other page
            elif request.user.role == 'admin':
                return redirect('admin_dash')
            elif request.user.role == 'manager':
                #manager modified an entry which was originally approved
                entry.entry_status = 'approved'
                entry.save()
                return redirect('manager_dash')
    else:
        form = ReceiptForm(instance=entry)
    return render(request, 'accountant/edit_receipt.html', {'form': form})

@login_required
def edit_payment(request, id):
    entry = get_object_or_404(Entry, pk=id)
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()

            if request.user.role == 'accountant':
                return redirect('accountant_dash')  # Redirect to the list of companies or any other page
            elif request.user.role == 'admin':
                return redirect('admin_dash')
            elif request.user.role == 'manager':
                #manager modified an entry which was originally approved
                entry.entry_status = 'approved'
                entry.save()
                return redirect('manager_dash')
    else:
        form = PaymentForm(instance=entry)
    return render(request, 'accountant/edit_payment.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.role == 'accountant', login_url='login')
def delete_entry(request, id):
    entry = get_object_or_404(Entry, pk=id)
    
    if entry:
        entry.delete()
    #show it in the manager dashboard
    return redirect('accountant_dash')

@login_required
@user_passes_test(lambda u: u.role == 'manager', login_url='login')
def approve_entry(request, id):
    entry = get_object_or_404(Entry, pk=id)
    #set pending entry status  to approved
    entry.entry_status = 'approved'
    entry.save()

    return redirect('manager_dash')

@login_required
@user_passes_test(lambda u: u.role == 'manager', login_url='login')
def reject_entry(request, id):
    if request.method == 'POST':
        remarks = request.POST.get('remarks', '')
        entry = get_object_or_404(Entry, pk=id)
        entry.entry_status = 'rejected'
        entry.remarks = remarks
        entry.save()
        # Add any other logic you need here
        return redirect('manager_dash')
    return HttpResponse('Invalid request', status=400)

@login_required
@user_passes_test(lambda u: u.role == 'manager', login_url='login')
def manager_request_edit(request, id):
    entry = get_object_or_404(Entry, pk=id)
    entry.entry_status = 'manager_review_requested'
    entry.save()
    return redirect('manager_dash')

@login_required
@user_passes_test(lambda u: u.role == 'accountant', login_url='login')
def resubmit_entry(request, id):
    entry = get_object_or_404(Entry, pk=id)
    #was rejected initially
    entry.entry_status = 'pending'
    entry.save()
    #show it in the manager dashboard
    return redirect('accountant_dash')

@admin_required
def approve_manager_review(request, id):
    entry = get_object_or_404(Entry, pk=id)
    entry.entry_status = 'manager_review_granted'
    entry.save()

    return redirect('admin_dash')

@admin_required
def reject_manager_review(request, id):
    entry = get_object_or_404(Entry, pk=id)
    entry.entry_status = 'approved'
    entry.save()

    return redirect('admin_dash')

@admin_required
def reject_irregular_entry(request, id):
    if request.method == 'POST':
        remarks = request.POST.get('remarks', '')
        entry = get_object_or_404(Entry, pk=id)
        entry.entry_status = 'rejected'
        entry.remarks = remarks
        entry.save()
        # Add any other logic you need here
        return redirect('admin_dash')
    return HttpResponse('Invalid request', status=400)

@admin_required
def approve_irregular_entry(request, id):
    entry = get_object_or_404(Entry, pk=id)
    entry.entry_status = 'approved'
    entry.save()
    return redirect('admin_dash')


@admin_required
def edit_company(request, id):
    company = get_object_or_404(Company, pk=id)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            return redirect('admin_dash')  # Redirect to the list of companies or any other page
    else:
        form = CompanyForm(instance=company)
    return render(request, 'admin/edit_company.html', {'form': form})

@admin_required
def delete_company(request, id):
    company = get_object_or_404(Company, pk=id)
    company.delete()
    redirect('admin_dash')

@admin_required
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dash')
    else:
        form = CategoryForm()
    return render(request, 'admin/create_category.html', {'form': form})

@admin_required
def create_subcategory(request):
    if request.method == 'POST':
        form = SubcategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dash')
    else:
        form = SubcategoryForm()
    return render(request, 'admin/create_subcategory.html', {'form': form})

@admin_required
def edit_category(request, id):
    category = get_object_or_404(Category, pk=id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('admin_dash')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'admin/edit_category.html', {'form': form})

@admin_required
def edit_subcategory(request, id):
    subcategory = get_object_or_404(Subcategory, pk=id)
    if request.method == 'POST':
        form = SubcategoryForm(request.POST, instance=subcategory)
        if form.is_valid():
            form.save()
            return redirect('admin_dash')
    else:
        form = SubcategoryForm(instance=subcategory)
    return render(request, 'admin/edit_subcategory.html', {'form': form})

@admin_required
def delete_category(request, id):
    category = get_object_or_404(Category, pk=id)
    if category:
        category.delete()

    return redirect('admin_dash')

@admin_required
def delete_subcategory(request, id):
    subcategory = get_object_or_404(Subcategory, pk=id)
    if subcategory:
        subcategory.delete()

    return redirect('admin_dash')







#AJAX
@login_required
@user_passes_test(lambda u: u.role == 'manager' or u.role == 'accountant', login_url='login')
def filter_approved_entries(request):
    date = request.GET.get('date')
    user_id = request.GET.get('user')
    type = request.GET.get('type')
    company_name = request.GET.get('company')
    page_number = int(request.GET.get('approved_page', 1))
    
    entries = Entry.objects.filter(entry_status='approved')

    print(entries)

    #to ensure entries are from the companies associated with user
    user_companies = request.user.company.all()  # Adjust this if your related manager is different
    if user_companies.exists():
        print(f'request.user.company {user_companies.first()}')
        entries = entries.filter(company__in=user_companies)
    
    if date:
        entries = entries.filter(date=date)
    
    if user_id:
        entries = entries.filter(user_id=user_id)

    if type:
        entries = entries.filter(entry_type=type)

    if company_name:
        print(company_name)
        company = Company.objects.get(name=company_name)
        if company:
            entries = entries.filter(company=company)

    entries = entries.order_by('-created_at')

    print(entries)

    receipts_over_time = entries.values('date', 'currency').annotate(total_receipts=Sum('receipts'))
    payments_over_time = entries.values('date', 'currency').annotate(total_payments=Sum('payments'))
    # Prepare data for the template
    dates = [entry['date'].strftime('%Y-%m-%d') for entry in receipts_over_time]
    receipts = [float(entry['total_receipts'] or 0) for entry in receipts_over_time]
    payments = [float(entry['total_payments'] or 0) for entry in payments_over_time]
    currencies = [entry['currency'] for entry in receipts_over_time]
    

    paginator = Paginator(entries, 10)  # Show 10 entries per page
    page_obj = paginator.get_page(page_number)
    
    entries_data = []
    for entry in page_obj:
        entries_data.append({
            'user': entry.user.first_name,
            'receipts': entry.currency + "." + str(entry.receipts),
            'payments': entry.currency + "." + str(entry.payments),
            'date': entry.date.strftime('%Y-%m-%d'),
            'company': entry.company.name,
            'description': entry.description,
            'category': entry.category.name,  # Assuming 'name' is the field you want from Category
            'subcategory': entry.subcategory.name,  # Assuming 'name' is the field you want from Subcategory
            'status': entry.get_entry_status_display(),
            'entry_type':entry.entry_type,
            'id': entry.id,
        })

    return JsonResponse({
    'entries': entries_data,
    'dates': dates,
    'receipts': receipts,
    'payments': payments,
    'currencies': currencies,
    'page_number': page_obj.number,
    'total_pages': paginator.num_pages,
    'has_previous': page_obj.has_previous(),
    'has_next': page_obj.has_next(),
    'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
    'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
})

@login_required
@user_passes_test(lambda u: u.role == 'manager', login_url='login')
def filter_pending_entries_manager(request):
    company_name = request.GET.get('company')
    page_number = request.GET.get('pending_page', 1)
    
    entries = Entry.objects.filter(entry_status='pending')

    entries = entries.filter(is_irregular=False)

    
    # filter them further if company name supplied
    if company_name:
        company = Company.objects.get(name=company_name)
        if company:
            entries = entries.filter(company=company)

    #filter pending entries for the manager
    accountants = request.user.accountants.all()
    entries = entries.filter(user__in=accountants)
    print(f'entries in manager {entries}')
    

    entries = entries.order_by('-created_at')
    

    paginator = Paginator(entries, 10)  # Show 10 entries per page
    page_obj = paginator.get_page(page_number)

    
    entries_data = []
    for entry in page_obj:
        entries_data.append({
            'user': entry.user.first_name,
            'receipts': entry.currency + "." + str(entry.receipts),
            'payments': entry.currency + "." + str(entry.payments),
            'date': entry.date.strftime('%Y-%m-%d'),
            'company': entry.company.name,
            'description': entry.description,
            'category': entry.category.name,  # Assuming 'name' is the field you want from Category
            'subcategory': entry.subcategory.name,  # Assuming 'name' is the field you want from Subcategory
            'status': entry.get_entry_status_display(),
            'entry_type':entry.entry_type,
            'id': entry.id,
        })

    return JsonResponse({
        'entries': entries_data,
        'page_number': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
    })



@login_required
@user_passes_test(lambda u: u.role == 'manager' or u.role == 'accountant', login_url='login')
def filter_pending_entries(request):
    company_name = request.GET.get('company')
    page_number = request.GET.get('pending_page', 1)
    
    entries = Entry.objects.filter(entry_status='pending')

    entries = entries.filter(is_irregular=False)

    
    # filter them further if company name supplied
    if company_name:
        company = Company.objects.get(name=company_name)
        if company:
            entries = entries.filter(company=company)
    
    #only see entries you created
    if request.user.role == 'accountant':
        entries = entries.filter(user=request.user)

    entries = entries.order_by('-created_at')


    #filter pending entries for the manager
    accountants = request.user.accountants.all()
    manager_entries = entries.filter(user__in=accountants)

    paginator = Paginator(entries, 10)  # Show 10 entries per page
    page_obj = paginator.get_page(page_number)

    paginator_manager = Paginator(manager_entries, 10)
    page_obj_manager = paginator.get_page(page_number)

    
    entries_data = []
    for entry in entries:
        entries_data.append({
            'user': entry.user.first_name,
            'receipts': entry.currency + "." + str(entry.receipts),
            'payments': entry.currency + "." + str(entry.payments),
            'date': entry.date.strftime('%Y-%m-%d'),
            'company': entry.company.name,
            'description': entry.description,
            'category': entry.category.name,  # Assuming 'name' is the field you want from Category
            'subcategory': entry.subcategory.name,  # Assuming 'name' is the field you want from Subcategory
            'status': entry.get_entry_status_display(),
            'entry_type':entry.entry_type,
            'id': entry.id,
        })

    entries_data_manager = []
    for entry in page_obj_manager:
        entries_data_manager.append({
            'user': entry.user.first_name,
            'receipts': entry.currency + "." + str(entry.receipts),
            'payments': entry.currency + "." + str(entry.payments),
            'date': entry.date.strftime('%Y-%m-%d'),
            'company': entry.company.name,
            'description': entry.description,
            'category': entry.category.name,  # Assuming 'name' is the field you want from Category
            'subcategory': entry.subcategory.name,  # Assuming 'name' is the field you want from Subcategory
            'status': entry.get_entry_status_display(),
            'entry_type':entry.entry_type,
            'id': entry.id,
        })

    return JsonResponse({
        'entries': entries_data,
        'page_number': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
    })

@login_required
@user_passes_test(lambda u: u.role == 'accountant', login_url='login')
def filter_rejected_entries(request):
    company_name = request.GET.get('company')
    page_number = request.GET.get('rejected_page', 1)
    
    entries = Entry.objects.filter(entry_status='rejected')

    if company_name:
        company = Company.objects.get(name=company_name)
        if company:
            entries = entries.filter(company=company)

    entries = entries.filter(user=request.user)

    entries = entries.order_by('-created_at')

    paginator = Paginator(entries, 10)  # Show 10 entries per page
    page_obj = paginator.get_page(page_number)
    
    entries_data = []
    for entry in entries:
        entries_data.append({
            'user': entry.user.first_name,
            'receipts': entry.currency + "." + str(entry.receipts),
            'payments': entry.currency + "." + str(entry.payments),
            'date': entry.date.strftime('%Y-%m-%d'),
            'company': entry.company.name,
            'description': entry.description,
            'category': entry.category.name,  # Assuming 'name' is the field you want from Category
            'subcategory': entry.subcategory.name,  # Assuming 'name' is the field you want from Subcategory
            'status': entry.get_entry_status_display(),
            'entry_type':entry.entry_type,
            'remarks':entry.remarks,
            'id': entry.id,
        })

    return JsonResponse({
        'entries': entries_data,
        'page_number': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
    })

@login_required
@user_passes_test(lambda u: u.role == 'accountant', login_url='login')
def filter_irregular_entries(request):
    company_name = request.GET.get('company')
    page_number = request.GET.get('irregular_page', 1)
    
    entries = Entry.objects.filter(entry_status='pending')

    if company_name:
        company = Company.objects.get(name=company_name)
        if company:
            entries = entries.filter(company=company)

    entries = entries.filter(user=request.user)

    entries = entries.filter(is_irregular=True)

    entries = entries.order_by('-created_at')

    paginator = Paginator(entries, 10)  # Show 10 entries per page
    page_obj = paginator.get_page(page_number)
    
    entries_data = []
    for entry in entries:
        entries_data.append({
            'user': entry.user.first_name,
            'receipts': entry.currency + "." + str(entry.receipts),
            'payments': entry.currency + "." + str(entry.payments),
            'date': entry.date.strftime('%Y-%m-%d'),
            'company': entry.company.name,
            'description': entry.description,
            'category': entry.category.name,  # Assuming 'name' is the field you want from Category
            'subcategory': entry.subcategory.name,  # Assuming 'name' is the field you want from Subcategory
            'status': entry.get_entry_status_display(),
            'entry_type':entry.entry_type,
            'id': entry.id,
        })

    return JsonResponse({
        'entries': entries_data,
        'page_number': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
    })

@login_required
@user_passes_test(lambda u: u.role == 'manager', login_url='login')
def filter_manager_entries(request):
    company_name = request.GET.get('company')
    page_number = request.GET.get('manager_page', 1)

    entries = Entry.objects.filter(
        Q(entry_status='manager_review_requested') |  Q(entry_status='manager_review_granted'))

    #to ensure entries are from the companies associated with user
    user_companies = request.user.company.all()  # Adjust this if your related manager is different
    if user_companies.exists():
        print(f'request.user.company {user_companies.first()}')
        entries = entries.filter(company__in=user_companies)

    if company_name:
        print(f'company_name in manager {company_name}')
        company = Company.objects.get(name=company_name)
        if company:
            entries = entries.filter(company=company)

    print(f'entries in manager {entries}')

    entries = entries.order_by('-created_at')

    print(f'entries in manager {entries}')

    paginator = Paginator(entries, 10)  # Show 10 entries per page
    page_obj = paginator.get_page(page_number)
    
    entries_data = []
    for entry in page_obj:
        entries_data.append({
            'user': entry.user.first_name,
            'receipts': entry.currency + "." + str(entry.receipts),
            'payments': entry.currency + "." + str(entry.payments),
            'date': entry.date.strftime('%Y-%m-%d'),
            'company': entry.company.name,
            'description': entry.description,
            'category': entry.category.name,  # Assuming 'name' is the field you want from Category
            'subcategory': entry.subcategory.name,  # Assuming 'name' is the field you want from Subcategory
            'status': entry.get_entry_status_display(),
            'entry_type':entry.entry_type,
            'entry_status':entry.entry_status,
            'id': entry.id,
        })

    return JsonResponse({
        'entries': entries_data,
        'page_number': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
    })

@admin_required
def filter_entries_admin(request):
    date = request.GET.get('date')
    user_id = request.GET.get('user')
    type = request.GET.get('type')
    companyId = request.GET.get('company')
    page_number = int(request.GET.get('approved_page', 1))
    
    entries = Entry.objects.filter(entry_status='approved')

    if date:
        entries = entries.filter(date=date)
    
    if user_id:
        entries = entries.filter(user_id=user_id)

    if type:
        entries = entries.filter(entry_type=type)

    if companyId:
        company = get_object_or_404(Company, pk=companyId)
        if company:
            entries = entries.filter(company=company)

    entries = entries.order_by('-created_at')

    #graph values
    receipts_over_time = entries.values('date', 'currency').annotate(total_receipts=Sum('receipts'))
    payments_over_time = entries.values('date', 'currency').annotate(total_payments=Sum('payments'))
    # Prepare data for the template
    dates = [entry['date'].strftime('%Y-%m-%d') for entry in receipts_over_time]
    receipts = [float(entry['total_receipts'] or 0) for entry in receipts_over_time]
    payments = [float(entry['total_payments'] or 0) for entry in payments_over_time]
    currencies = [entry['currency'] for entry in receipts_over_time]

    paginator = Paginator(entries, 10)  # Show 10 entries per page
    page_obj = paginator.get_page(page_number)

    entries_data = []
    for entry in page_obj:
        entries_data.append({
            'user': entry.user.first_name,
            'receipts': entry.currency + "." + str(entry.receipts),
            'payments': entry.currency + "." + str(entry.payments),
            'date': entry.date.strftime('%Y-%m-%d'),
            'company': entry.company.name,
            'description': entry.description,
            'category': entry.category.name,
            'subcategory': entry.subcategory.name,
            'status': entry.get_entry_status_display(),
            'entry_type':entry.entry_type,
            'id': entry.id,
        })

    return JsonResponse({
        'entries': entries_data,
        'dates': dates,
        'receipts': receipts,
        'payments': payments,
        'currencies': currencies,
        'page_number': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
    })


    
def load_subcategories(request):
    category_id = request.GET.get('category')
    subcategories = Subcategory.objects.filter(category_id=category_id).order_by('name')
    return JsonResponse(list(subcategories.values('id', 'name')), safe=False)


