from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from .models import CandidatePayment, PaymentHistory
from apps.candidates.models import Candidate
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

@login_required
def payment_list(request):
    payments = CandidatePayment.objects.select_related('candidate', 'received_by').all()
    total = payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        payments = payments.filter(
            Q(candidate__full_name__icontains=search_query) |
            Q(candidate__passport_no__icontains=search_query) |
            Q(receipt_number__icontains=search_query) |
            Q(remarks__icontains=search_query)
        )
    
    # Filters
    payment_type = request.GET.get('payment_type', '')
    if payment_type:
        payments = payments.filter(payment_type=payment_type)
    
    payment_method = request.GET.get('payment_method', '')
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        payments = payments.filter(date__gte=date_from)
    if date_to:
        payments = payments.filter(date__lte=date_to)
    
    context = {
        'payments': payments,
        'total': total,
        'search_query': search_query,
        'payment_type': payment_type,
        'payment_method': payment_method,
        'date_from': date_from,
        'date_to': date_to,
        'payment_types': CandidatePayment.PAYMENT_TYPES,
        'payment_methods': CandidatePayment.PAYMENT_METHODS,
    }
    return render(request, 'payments/list.html', context)

@login_required
@transaction.atomic
def payment_add(request):
    # Check if candidate is preselected from URL
    preselected_candidate_id = request.GET.get('candidate')
    selected_candidate = None
    
    if preselected_candidate_id:
        try:
            selected_candidate = Candidate.objects.get(id=preselected_candidate_id)
        except Candidate.DoesNotExist:
            pass
    
    if request.method == 'POST':
        try:
            candidate_id = request.POST.get('candidate')
            candidate = Candidate.objects.get(id=candidate_id)
            amount = Decimal(request.POST.get('amount'))
            payment_type = request.POST.get('payment_type')
            payment_method = request.POST.get('payment_method')
            payment_date = request.POST.get('date')
            remarks = request.POST.get('remarks', '')
            
            # Validate payment doesn't exceed balance
            if amount > candidate.remaining_balance:
                messages.error(request, f'Payment amount (UGX {amount:,.0f}) exceeds remaining balance (UGX {candidate.remaining_balance:,.0f})')
                return redirect('payment_add')
            
            # Calculate new balance
            previous_balance = candidate.remaining_balance
            new_balance = previous_balance - amount
            
            # Create payment record
            payment = CandidatePayment.objects.create(
                candidate=candidate,
                payment_type=payment_type,
                amount=amount,
                date=payment_date,
                payment_method=payment_method,
                received_by=request.user,
                receipt_number=str(uuid.uuid4())[:8].upper(),
                previous_balance=previous_balance,
                new_balance=new_balance,
                remarks=remarks
            )
            
            # Update payment history for installment plans
            if candidate.payment_plan == 'installment':
                # Find the oldest pending installment
                pending = PaymentHistory.objects.filter(
                    candidate=candidate,
                    status='pending'
                ).order_by('due_date').first()
                
                if pending:
                    pending.payment = payment
                    pending.amount_paid = amount
                    pending.status = 'paid'
                    pending.paid_date = payment_date
                    pending.save()
            
            # Update candidate's balance
            candidate.update_balance()
            
            messages.success(
                request, 
                f'Payment of UGX {amount:,.0f} recorded successfully! '
                f'Receipt: {payment.receipt_number}. '
                f'Remaining balance: UGX {new_balance:,.0f}'
            )
            
            return redirect('payment_list')
            
        except Candidate.DoesNotExist:
            messages.error(request, 'Selected candidate not found.')
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
    
    # GET request - show form
    candidates = Candidate.objects.all().order_by('full_name')
    
    return render(request, 'payments/form.html', {
        'candidates': candidates,
        'selected_candidate': selected_candidate,
    })

@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(CandidatePayment, pk=pk)
    candidate = payment.candidate
    payment.delete()
    candidate.update_balance()
    messages.success(request, 'Payment deleted successfully.')
    return redirect('payment_list')

@login_required
def payment_receipt(request, pk):
    payment = get_object_or_404(CandidatePayment, pk=pk)
    return render(request, 'payments/receipt.html', {'payment': payment})

@login_required
def loan_payment_history(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    payment_history = PaymentHistory.objects.filter(candidate=candidate).select_related('payment').order_by('due_date')
    
    # Calculate total paid
    total_paid = candidate.initial_amount - candidate.remaining_balance
    
    # Calculate counts
    paid_count = payment_history.filter(status='paid').count()
    pending_count = payment_history.filter(status='pending').count()
    overdue_count = payment_history.filter(status='overdue').count()
    
    return render(request, 'payments/loan_history.html', {
        'candidate': candidate,
        'payment_history': payment_history,
        'total_paid': total_paid,  # Add this
        'paid_count': paid_count,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
    })

@login_required
def create_payment_schedule(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    if request.method == 'POST':
        try:
            from decimal import Decimal
            total_amount = Decimal(request.POST.get('total_amount'))
            num_installments = int(request.POST.get('num_installments'))
            start_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').date()
            
            # Update candidate
            candidate.initial_amount = total_amount
            candidate.remaining_balance = total_amount
            candidate.payment_plan = 'installment'
            candidate.save()
            
            # Create payment schedule (without linking to a payment yet)
            amount_per_installment = total_amount / Decimal(num_installments)
            for i in range(num_installments):
                due_date = start_date + timedelta(days=30 * i)
                PaymentHistory.objects.create(
                    candidate=candidate,
                    payment=None,  # No payment yet
                    due_date=due_date,
                    amount_due=amount_per_installment,
                    amount_paid=0,
                    status='pending'
                )
            
            messages.success(request, f'Payment schedule created with {num_installments} installments of UGX {amount_per_installment:,.0f} each')
            return redirect('candidate_detail', pk=candidate_id)
            
        except Exception as e:
            messages.error(request, f'Error creating payment schedule: {str(e)}')
    
    return render(request, 'payments/create_schedule.html', {'candidate': candidate})

@login_required
@transaction.atomic
def payment_edit(request, pk):
    payment = get_object_or_404(CandidatePayment, pk=pk)
    candidate = payment.candidate
    
    if request.method == 'POST':
        try:
            # Store old values for logging
            old_amount = payment.amount
            old_type = payment.payment_type
            old_method = payment.payment_method
            
            # Update payment details
            amount = Decimal(request.POST.get('amount'))
            payment_type = request.POST.get('payment_type')
            payment_method = request.POST.get('payment_method')
            payment_date = request.POST.get('date')
            remarks = request.POST.get('remarks', '')
            
            # Validate amount doesn't exceed candidate's total required amount
            if amount > candidate.initial_amount:
                messages.error(request, f'Payment amount (UGX {amount:,.0f}) exceeds required amount (UGX {candidate.initial_amount:,.0f})')
                return redirect('payment_edit', pk=pk)
            
            # Calculate new balances
            previous_balance = candidate.remaining_balance + old_amount - amount
            
            # Update payment
            payment.amount = amount
            payment.payment_type = payment_type
            payment.payment_method = payment_method
            payment.date = payment_date
            payment.remarks = remarks
            payment.previous_balance = previous_balance
            payment.new_balance = previous_balance - amount
            payment.save()
            
            # Update candidate's balance
            candidate.update_balance()
            
            messages.success(
                request, 
                f'Payment updated successfully! New amount: UGX {amount:,.0f}'
            )
            
            return redirect('payment_list')
            
        except Exception as e:
            messages.error(request, f'Error updating payment: {str(e)}')
    
    # GET request - show form with existing data
    candidates = Candidate.objects.all().order_by('full_name')
    
    return render(request, 'payments/form.html', {
        'payment': payment,
        'candidates': candidates,
        'selected_candidate': candidate,
        'is_edit': True
    })

@login_required
@transaction.atomic
def payment_receipt_upload(request, pk):
    payment = get_object_or_404(CandidatePayment, pk=pk)
    
    if request.method == 'POST' and request.FILES.get('receipt_file'):
        try:
            receipt_file = request.FILES['receipt_file']
            
            # Validate file size (2MB max)
            if receipt_file.size > 2 * 1024 * 1024:
                messages.error(request, 'File size exceeds 2MB limit.')
                return redirect('payment_list')
            
            # Validate file type
            allowed_types = ['pdf', 'jpg', 'jpeg', 'png']
            file_ext = receipt_file.name.split('.')[-1].lower()
            if file_ext not in allowed_types:
                messages.error(request, 'Only PDF, JPG, and PNG files are allowed.')
                return redirect('payment_list')
            
            # Delete old receipt file if exists
            if payment.receipt_file:
                if default_storage.exists(payment.receipt_file.name):
                    default_storage.delete(payment.receipt_file.name)
            
            # Save new receipt
            filename = f"receipt_{payment.receipt_number}_{payment.candidate.passport_no}.{file_ext}"
            payment.receipt_file.save(filename, receipt_file)
            payment.receipt_uploaded_at = timezone.now()
            payment.save()
            
            messages.success(request, f'Receipt uploaded successfully for {payment.receipt_number}')
            
        except Exception as e:
            messages.error(request, f'Error uploading receipt: {str(e)}')
    
    return redirect('payment_list')

@login_required
def payment_receipt_download(request, pk):
    payment = get_object_or_404(CandidatePayment, pk=pk)
    
    if not payment.receipt_file:
        messages.error(request, 'No receipt file found.')
        return redirect('payment_list')
    
    try:
        file_path = payment.receipt_file.path
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                filename = f"receipt_{payment.receipt_number}_{payment.candidate.passport_no}.pdf"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        else:
            messages.error(request, 'Receipt file not found on server.')
    except Exception as e:
        messages.error(request, f'Error downloading receipt: {str(e)}')
    
    return redirect('payment_list')