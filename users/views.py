from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import JsonResponse

from .forms import CustomAuthenticationForm, CustomUserInitialCreationForm, CustomUserCreationForm, CustomUserEditForm
from entries.models import Company, Entry, Category, Subcategory

User = get_user_model()


def initial_register(request):
    if User.objects.exists():
        return redirect('create_user')  # Redirect to login or another appropriate view

    if request.method == 'POST':
        form = CustomUserInitialCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'admin'  # Set the first user's role to admin
            user.save()
            return redirect('admin_dash')
    else:
        form = CustomUserInitialCreationForm()
    return render(request, 'auth/register_first_admin.html', {'form': form})

def admin_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'admin':
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return login_required(user_passes_test(lambda u: u.role == 'admin', login_url='login')(_wrapped_view_func))

@admin_required
def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() 
            user.save()
            return redirect('admin_dash')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            print(f'email {email}')
            password = form.cleaned_data.get('password')
            print(f'password {password}')
            user = authenticate(email=email, password=password)
            if user is not None:
                login(request, user)
                if request.user.role == 'admin':
                    return redirect('admin_dash')
                elif request.user.role == 'accountant':
                    return redirect('accountant_dash')
                elif request.user.role == 'manager':
                    return redirect('manager_dash')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

@admin_required
def admin_dash(request):
    # Get all users and companies
    users = User.objects.all()
    companies = Company.objects.all()
    entries = Entry.objects.all()
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()

    approved_entries = entries.filter(entry_status='approved')
    approved_entries = approved_entries.order_by('-created_at')

    receipts_over_time = approved_entries.values('date', 'currency').annotate(total_receipts=Sum('receipts'))
    payments_over_time = approved_entries.values('date', 'currency').annotate(total_payments=Sum('payments'))
    # Prepare data for the template
    dates = [entry['date'].strftime('%Y-%m-%d') for entry in receipts_over_time]
    receipts = [float(entry['total_receipts'] or 0) for entry in receipts_over_time]
    payments = [float(entry['total_payments'] or 0) for entry in payments_over_time]
    currencies = [entry['currency'] for entry in receipts_over_time]

    #approved entries paginator
    approved_paginator = Paginator(approved_entries, 10)  # Show 10 entries per page
    page_number = request.GET.get('approved_page')
    try:
        approved_entries = approved_paginator.page(page_number)
    except PageNotAnInteger:
        approved_entries = approved_paginator.page(1)  # If page is not an integer, deliver first page
    except EmptyPage:
        approved_entries = approved_paginator.page(approved_paginator.num_pages)

    #manager_review_entries
    manager_review_entries = entries.filter(entry_status='manager_review_requested')
    manager_review_entries = manager_review_entries.order_by('-created_at')
    #manager_review paginator
    manager_paginator = Paginator(manager_review_entries, 10)  # Show 10 entries per page
    page_number = request.GET.get('manager_page')
    try:
        manager_review_entries = manager_paginator.page(page_number)
    except PageNotAnInteger:
        manager_review_entries = manager_paginator.page(1)  # If page is not an integer, deliver first page
    except EmptyPage:
        manager_review_entries = manager_paginator.page(manager_paginator.num_pages)

    #irregular entries            
    irregular_entries = entries.filter(entry_status='pending')
    irregular_entries = irregular_entries.filter(is_irregular=True)
    irregular_entries = irregular_entries.order_by('-created_at', 'user')
    irregular_paginator = Paginator(irregular_entries, 10)  # Show 10 entries per page
    page_number = request.GET.get('irregular_page')
    try:
        irregular_entries = irregular_paginator.page(page_number)
    except PageNotAnInteger:
        irregular_entries = irregular_paginator.page(1)  # If page is not an integer, deliver first page
    except EmptyPage:
        irregular_entries = irregular_paginator.page(irregular_paginator.num_pages)

    # Pagination for users
    users = users.order_by('first_name')
    user_paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('user_page')
    try:
        users = user_paginator.page(page_number)
    except PageNotAnInteger:
        users = user_paginator.page(1)
    except EmptyPage:
        users = user_paginator.page(user_paginator.num_pages)

    

    # Pagination for companies
    companies = companies.order_by('name')
    company_paginator = Paginator(companies, 10)  # Show 10 companies per page
    page_number = request.GET.get('company_page')
    try:
        companies = company_paginator.page(page_number)
    except PageNotAnInteger:
        companies = company_paginator.page(1)
    except EmptyPage:
        companies = company_paginator.page(company_paginator.num_pages)


    # Pagination for categories
    categories = categories.order_by('name')
    category_paginator = Paginator(categories, 10)  # Show 10 categories per page
    page_number = request.GET.get('category_page')
    try:
        categories = category_paginator.page(page_number)
    except PageNotAnInteger:
        categories = category_paginator.page(1)
    except EmptyPage:
        categories = category_paginator.page(category_paginator.num_pages)


    # Pagination for subcategories
    subcategories = subcategories.order_by('name')
    subcategory_paginator = Paginator(subcategories, 10)  # Show 10 categories per page
    page_number = request.GET.get('subcategory_page')
    try:
        subcategories = subcategory_paginator.page(page_number)
    except PageNotAnInteger:
        subcategories = subcategory_paginator.page(1)
    except EmptyPage:
        subcategories = subcategory_paginator.page(subcategory_paginator.num_pages)

    return render(request, 'admin/admin_dash.html', {'users':users,
                                                     'companies':companies,
                                                     'categories':categories,
                                                     'subcategories':subcategories,
                                                     'irregular_entries':irregular_entries,
                                                     'approved_entries':approved_entries,
                                                     'manager_review_entries':manager_review_entries,
                                                     'dates':dates,
                                                     'receipts':receipts,
                                                     'payments':payments,
                                                     'currencies':currencies})

@login_required
@user_passes_test(lambda u: u.role == 'manager', login_url='login')
def manager_dash(request):
    date = request.GET.get('date')
    user_id = request.GET.get('user')


    entries = Entry.objects.all()

    users = User.objects.all()
    if request.user.company:
        for company in request.user.company.all():
            users = users.filter(company=company)

    #only load entries in the same company as user.
    if request.user.company:
        for company in request.user.company.all():
            entries = entries.filter(company=company)

    #pending entries
    pending_entries = entries.filter(entry_status='pending')
    print(f'before {pending_entries}')
    accountants = request.user.accountants.all()
    pending_entries = pending_entries.filter(user__in=accountants)
    print(f'after {pending_entries}')
    # pending_entries = pending_entries.filter(user__managers=request.user)

    pending_entries = pending_entries.order_by('-created_at')
    paginator = Paginator(pending_entries, 10)  # Show 10 entries per page
    print(f' dont know {pending_entries}')
    page_number = request.GET.get('page')
    try:
        pending_entries = paginator.page(page_number)
    except PageNotAnInteger:
        pending_entries = paginator.page(1)  # If page is not an integer, deliver first page
    except EmptyPage:
        pending_entries = paginator.page(paginator.num_pages) 
    print(f' dont know {pending_entries}')


     #approved entries            
    approved_entries = entries.filter(entry_status='approved')
    approved_entries = approved_entries.order_by('-created_at')

    #search here to reflect changes in graph
    if date:
        approved_entries = approved_entries.filter(date=date)

    if user_id:
        approved_entries = approved_entries.filter(user__id=user_id)

    receipts_over_time = approved_entries.values('date', 'currency').annotate(total_receipts=Sum('receipts'))
    payments_over_time = approved_entries.values('date', 'currency').annotate(total_payments=Sum('payments'))
    # Prepare data for the template
    dates = [entry['date'].strftime('%Y-%m-%d') for entry in receipts_over_time]
    receipts = [float(entry['total_receipts'] or 0) for entry in receipts_over_time]
    payments = [float(entry['total_payments'] or 0) for entry in payments_over_time]
    currencies = [entry['currency'] for entry in receipts_over_time]


    #approved entries paginator
    paginator = Paginator(approved_entries, 10)  # Show 10 entries per page
    page_number = request.GET.get('page')
    try:
        approved_entries = paginator.page(page_number)
    except PageNotAnInteger:
        approved_entries = paginator.page(1)  # If page is not an integer, deliver first page
    except EmptyPage:
        approved_entries = paginator.page(paginator.num_pages)  # If page is out of range, deliver last page


    #manager edit entries            
    manager_edit_entries = entries.filter(
        Q(entry_status='manager_review_requested') |  Q(entry_status='manager_review_granted'))
    manager_edit_entries = manager_edit_entries.order_by('-created_at')

    #edit_requested_entries paginator
    paginator = Paginator(manager_edit_entries, 10)  # Show 10 entries per page
    page_number = request.GET.get('page')
    try:
        manager_edit_entries = paginator.page(page_number)
    except PageNotAnInteger:
        manager_edit_entries = paginator.page(1)  # If page is not an integer, deliver first page
    except EmptyPage:
        manager_edit_entries = paginator.page(paginator.num_pages)  # If page is out of range, deliver last page



    return render(request, 'manager/manager_dash.html', {'pending_entries': pending_entries,
                                                         'approved_entries': approved_entries,
                                                         'manager_edit_entries': manager_edit_entries,
                                                         'users':users,
                                                         'dates':dates,
                                                         'receipts':receipts,
                                                         'payments':payments,
                                                         'currencies':currencies})

@login_required
@user_passes_test(lambda u: u.role == 'accountant', login_url='login')
def accountant_dash(request):
    entries = Entry.objects.all()

    users = User.objects.all()
    if request.user.company:
        for company in request.user.company.all():
            users = users.filter(company=company)

    users = users.filter(role='accountant')

    #pending entries
    pending_entries = entries.filter(entry_status='pending')
    pending_entries = pending_entries.filter(is_irregular=False)
    pending_entries = pending_entries.filter(user = request.user)
    pending_entries = pending_entries.order_by('-created_at')
    paginator = Paginator(pending_entries, 10)  # Show 10 entries per page
    page_number = request.GET.get('pending_page')
    try:
        pending_entries = paginator.page(page_number)
    except PageNotAnInteger:
        pending_entries = paginator.page(1)  # If page is not an integer, deliver first page
    except EmptyPage:
        pending_entries = paginator.page(paginator.num_pages) 

    #rejected entries
    rejected_entries = entries.filter(entry_status='rejected')
    rejected_entries = rejected_entries.filter(user=request.user)
    rejected_entries = rejected_entries.order_by('-created_at')
    paginator = Paginator(rejected_entries, 10)  # Show 10 entries per page
    page_number = request.GET.get('rejected_page')
    try:
        rejected_entries = paginator.page(page_number)
    except PageNotAnInteger:
        rejected_entries = paginator.page(1)  # If page is not an integer, deliver first page
    except EmptyPage:
        rejected_entries = paginator.page(paginator.num_pages) 

    #approved entries
    #only load entries in the same company as user.
    if request.user.company:
        for company in request.user.company.all():
            entries = entries.filter(company=company)          
    approved_entries = entries.filter(entry_status='approved')
    approved_entries = approved_entries.order_by('-created_at')

    #graph values
    receipts_over_time = approved_entries.values('date', 'currency').annotate(total_receipts=Sum('receipts'))
    payments_over_time = approved_entries.values('date', 'currency').annotate(total_payments=Sum('payments'))
    # Prepare data for the template
    dates = [entry['date'].strftime('%Y-%m-%d') for entry in receipts_over_time]
    receipts = [float(entry['total_receipts'] or 0) for entry in receipts_over_time]
    payments = [float(entry['total_payments'] or 0) for entry in payments_over_time]
    currencies = [entry['currency'] for entry in receipts_over_time]


    #approved entries paginator
    paginator = Paginator(approved_entries, 10)  # Show 10 entries per page
    page_number = request.GET.get('approved_page')
    try:
        approved_entries = paginator.page(page_number)
    except PageNotAnInteger:
        approved_entries = paginator.page(1)  # If page is not an integer, deliver first page
    except EmptyPage:
        approved_entries = paginator.page(paginator.num_pages)  # If page is out of range, deliver last page

    #excel entries            
    irregular_entries = entries.filter(entry_status='pending')
    irregular_entries = irregular_entries.filter(is_irregular=True)
    irregular_entries = irregular_entries.order_by('-created_at')
    paginator = Paginator(irregular_entries, 10)  # Show 10 entries per page
    page_number = request.GET.get('irregular_page')
    try:
        irregular_entries = paginator.page(page_number)
    except PageNotAnInteger:
        irregular_entries = paginator.page(1)  # If page is not an integer, deliver first page
    except EmptyPage:
        irregular_entries = paginator.page(paginator.num_pages)



    return render(request, 'accountant/accountant_dash.html', {'entries': approved_entries,
                                                               'pending_entries': pending_entries,
                                                               'rejected_entries': rejected_entries,
                                                               'irregular_entries': irregular_entries,
                                                               'users':users,
                                                               'dates':dates,
                                                               'receipts':receipts,
                                                               'payments':payments,
                                                               "currencies":currencies})


@admin_required
def edit_user(request, id):
    user = get_object_or_404(User, pk=id)
    if request.method == 'POST':
        form = CustomUserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User details were successfully updated!')
            return redirect('admin_dash')  # Redirect to the user's detail page or any other page
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomUserEditForm(instance=user)
    return render(request, 'auth/edit_user.html', {'form': form})

@admin_required
def delete_user(request, id):
    user = get_object_or_404(User, id=id)
    user.delete()
    return redirect('admin_dash')


def logout_view(request):
    logout(request)
    return redirect('login')




#AJAX
@admin_required
def filter_accountants(request, id):
    company = get_object_or_404(Company, pk=id)

    users = User.objects.filter(company__id=company.id)

    users = users.filter(role='accountant')

    user_data = [{'id': user.id, 'email': user.email} for user in users]

    return JsonResponse({
        'users':user_data
    })

@admin_required
def all_accountants(request):
    users = User.objects.filter(role='accountant')

    user_data = [{'id': user.id, 'email': user.email} for user in users]

    return JsonResponse({
        'users':user_data
    })




