import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from io import BytesIO
from apps.candidates.models import Candidate
from apps.agents.models import Agent
from apps.documents.models import DocumentStatus
from apps.visa_process.models import VisaProcess
from apps.accounts.decorators import permission_required
from apps.accounts.models import log_activity

@login_required
@permission_required('import_data')
def download_template(request):
    """Download an Excel template matching the expected format"""
    
    # Create template data matching your Excel structure
    template_data = {
        'SN': [1, 2, 3],
        "CANDIDATE'S NAME": ['OKIPANGORI DICK BALAKI', 'WAAKO CHRIS', 'TIGA IYAN'],
        'PASSPORT NO': ['', '', ''],
        'PASSPORT EXPIRY DATE': ['', '', ''],
        'POSITION': ['Helper', 'Cable Pulling', ''],
        'MEDICAL REPORT': ['Yes', 'No', 'No'],
        'BLOOD GROUP': ['O', '', ''],
        'CONTACT NUMBER': ['704112338', '777301174', '744127356'],
        "MOTHER'S NAME": ['Akello Patricia', 'Takali Mangadalema', 'Nakabiri Babra'],
        "FATHER'S NAME": ['Opidi George', 'Taliwaku Samuel', 'Seguya Vicent'],
        'SALARY': ['900', '900', ''],
        'OFFER LETTER': ['Yes', 'yes', ''],
        'SIGNED OL': ['Yes', 'yes', ''],
        'AGENT NAME': ['Moses Julius Mbale', 'Moses Julius Mbale', ''],
        'AGENT NO.': ['0757115308', '0757115308', '0707218909'],
        'REMARKS': ['Done', 'Done', ''],
        'Medical': ['', '', ''],
        'Interpal': ['', '', ''],
        'Passport copy': ['', '', ''],
        'Passport size photo': ['', '', ''],
    }
    
    df = pd.DataFrame(template_data)
    
    # Create response
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="candidate_import_template.xlsx"'
    
    # Save to BytesIO and write to response
    with BytesIO() as b:
        with pd.ExcelWriter(b, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='MASTER LIST', index=False)
            
            # Auto-adjust columns width
            worksheet = writer.sheets['MASTER LIST']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_width + 2, 30)
        
        response.write(b.getvalue())
    
    return response


@login_required
@permission_required('import_data')
def import_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        
        try:
            # Read Excel file
            df = pd.read_excel(excel_file, sheet_name=0, header=0)  # Read first sheet with header
            
            # Store original columns for debugging
            original_columns = df.columns.tolist()
            
            # Clean column names for processing
            df.columns = df.columns.str.strip().str.upper().str.replace(' ', '_').str.replace("'", '').str.replace('.', '')
            
            print("Original columns:", original_columns)
            print("Cleaned columns:", df.columns.tolist())
            
            stats = {
                'total': 0,
                'success': 0,
                'skipped': 0,
                'errors': 0,
                'agents_created': 0,
                'error_details': []
            }
            
            # Process each row
            for index, row in df.iterrows():
                stats['total'] += 1
                
                try:
                    # Skip completely empty rows (checking first few columns)
                    if index < 2:  # Skip header rows if they exist
                        continue
                    
                    # Extract candidate name - try different possible column names
                    candidate_name = None
                    for col in ['CANDIDATES_NAME', 'CANDIDATE_NAME', 'CANDIDATESNAME', 'CANDIDATENAME']:
                        if col in row and pd.notna(row[col]):
                            candidate_name = str(row[col]).strip()
                            break
                    
                    # If no name found, try the original column name
                    if not candidate_name and 'CANDIDATE\'S_NAME' in original_columns:
                        col_idx = original_columns.index('CANDIDATE\'S_NAME')
                        if col_idx < len(row) and pd.notna(row.iloc[col_idx]):
                            candidate_name = str(row.iloc[col_idx]).strip()
                    
                    # If still no name, skip this row
                    if not candidate_name or candidate_name.lower() == 'nan' or candidate_name == '':
                        stats['skipped'] += 1
                        continue
                    
                    with transaction.atomic():
                        # Extract passport number
                        passport_no = ''
                        for col in ['PASSPORT_NO', 'PASSPORTNUMBER', 'PASSPORT']:
                            if col in row and pd.notna(row[col]):
                                passport_no = str(row[col]).strip()
                                break
                        
                        # Generate a temporary passport if empty
                        if not passport_no:
                            passport_no = f"TEMP{datetime.now().strftime('%y%m')}{index+1:04d}"
                        
                        # Check if candidate already exists
                        existing = Candidate.objects.filter(
                            Q(passport_no=passport_no) | 
                            (Q(full_name__iexact=candidate_name) & Q(passport_no__startswith='TEMP'))
                        ).first()
                        
                        if existing:
                            stats['skipped'] += 1
                            stats['error_details'].append(f"Row {index+2}: Candidate {candidate_name} already exists")
                            continue
                        
                        # Extract position
                        position = 'Not Specified'
                        for col in ['POSITION', 'JOB_TITLE', 'ROLE']:
                            if col in row and pd.notna(row[col]):
                                position = str(row[col]).strip()
                                break
                        
                        # Extract contact number
                        contact = ''
                        for col in ['CONTACT_NUMBER', 'PHONE', 'CONTACT', 'MOBILE']:
                            if col in row and pd.notna(row[col]):
                                contact = str(row[col]).strip()
                                # Clean phone number (remove non-digits but keep +)
                                contact = ''.join(c for c in contact if c.isdigit() or c == '+')
                                break
                        
                        if not contact:
                            contact = '0000000000'
                        
                        # Extract medical report status
                        medical = False
                        for col in ['MEDICAL_REPORT', 'MEDICAL', 'MEDICAL_STATUS']:
                            if col in row and pd.notna(row[col]):
                                val = str(row[col]).strip().upper()
                                medical = val in ['YES', 'TRUE', 'Y', '1', 'DONE', 'COMPLETED', 'POSITIVE']
                                break
                        
                        # Extract interpol status
                        interpol = False
                        for col in ['INTERPAL', 'INTERPOL', 'INTERPOL_STATUS']:
                            if col in row and pd.notna(row[col]):
                                val = str(row[col]).strip().upper()
                                interpol = val in ['YES', 'TRUE', 'Y', '1', 'DONE', 'COMPLETED', 'POSITIVE']
                                break
                        
                        # Extract offer letter
                        offer_letter = False
                        for col in ['OFFER_LETTER', 'OFFER', 'LETTER']:
                            if col in row and pd.notna(row[col]):
                                val = str(row[col]).strip().upper()
                                offer_letter = val in ['YES', 'TRUE', 'Y', '1', 'DONE']
                                break
                        
                        # Extract signed OL (MOL approval)
                        signed_ol = False
                        for col in ['SIGNED_OL', 'MOL_APPROVAL', 'SIGNED_OFFER']:
                            if col in row and pd.notna(row[col]):
                                val = str(row[col]).strip().upper()
                                signed_ol = val in ['YES', 'TRUE', 'Y', '1', 'DONE']
                                break
                        
                        # Extract passport copy
                        passport_copy = False
                        for col in ['PASSPORT_COPY', 'COPY_PASSPORT']:
                            if col in row and pd.notna(row[col]):
                                val = str(row[col]).strip().upper()
                                passport_copy = val in ['YES', 'TRUE', 'Y', '1', 'DONE']
                                break
                        
                        # Extract passport photo
                        passport_photo = False
                        for col in ['PASSPORT_SIZE_PHOTO', 'PHOTO', 'PASSPORT_PHOTO']:
                            if col in row and pd.notna(row[col]):
                                val = str(row[col]).strip().upper()
                                passport_photo = val in ['YES', 'TRUE', 'Y', '1', 'DONE']
                                break
                        
                        # Extract blood group
                        blood_group = ''
                        for col in ['BLOOD_GROUP', 'BLOOD']:
                            if col in row and pd.notna(row[col]):
                                blood_group = str(row[col]).strip().upper()
                                # Validate blood group
                                valid_groups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-', 'A', 'B', 'O', 'AB']
                                if blood_group not in valid_groups:
                                    blood_group = ''
                                break
                        
                        # Extract mother's name
                        mother_name = ''
                        for col in ["MOTHER'S_NAME", "MOTHER_NAME", "MOTHER"]:
                            if col in row and pd.notna(row[col]):
                                mother_name = str(row[col]).strip()
                                break
                        
                        # Extract father's name
                        father_name = ''
                        for col in ["FATHER'S_NAME", "FATHER_NAME", "FATHER"]:
                            if col in row and pd.notna(row[col]):
                                father_name = str(row[col]).strip()
                                break
                        
                        # Extract salary
                        salary = 0
                        for col in ['SALARY', 'PAY', 'WAGE']:
                            if col in row and pd.notna(row[col]):
                                try:
                                    # Handle both string and numeric values
                                    val = row[col]
                                    if isinstance(val, (int, float)):
                                        salary = float(val)
                                    else:
                                        # Remove commas and convert
                                        salary_str = str(val).replace(',', '').strip()
                                        if salary_str and salary_str.lower() != 'nan':
                                            salary = float(salary_str)
                                except:
                                    salary = 0
                                break
                        
                        # Extract agent name
                        agent_name = ''
                        agent_phone = ''
                        
                        for col in ['AGENT_NAME', 'AGENT']:
                            if col in row and pd.notna(row[col]):
                                agent_name = str(row[col]).strip()
                                # Split if multiple agents (e.g., "Safiina/Kavuma")
                                if '/' in agent_name:
                                    agent_name = agent_name.split('/')[0].strip()
                                break
                        
                        for col in ['AGENT_NO', 'AGENT_PHONE']:
                            if col in row and pd.notna(row[col]):
                                agent_phone = str(row[col]).strip()
                                break
                        
                        # Get or create agent
                        agent = None
                        if agent_name and agent_name.lower() != 'nan':
                            # Clean agent name
                            agent_name = agent_name.strip()
                            
                            # Try to find existing agent
                            agent = Agent.objects.filter(name__iexact=agent_name).first()
                            
                            if not agent:
                                # Create new agent
                                agent = Agent.objects.create(
                                    name=agent_name,
                                    email=f"{agent_name.lower().replace(' ', '')}@example.com",
                                    phone=agent_phone or '0000000000',
                                    commission_rate=0
                                )
                                stats['agents_created'] += 1
                                print(f"Created new agent: {agent_name}")
                        
                        # Extract remarks
                        remarks = ''
                        for col in ['REMARKS', 'NOTES', 'COMMENTS']:
                            if col in row and pd.notna(row[col]):
                                remarks = str(row[col]).strip()
                                break
                        
                        # Create candidate
                        candidate = Candidate.objects.create(
                            full_name=candidate_name,
                            passport_no=passport_no,
                            passport_expiry=datetime.now().date() + timedelta(days=365*5),  # Default 5 years
                            position=position,
                            contact_number=contact,
                            mother_name=mother_name,
                            father_name=father_name,
                            blood_group=blood_group,
                            salary=salary,
                            agent=agent,
                            remarks=remarks,
                            initial_amount=0,
                            remaining_balance=0,
                            payment_plan='cash'
                        )
                        
                        # Create document status
                        DocumentStatus.objects.create(
                            candidate=candidate,
                            medical_report=medical,
                            interpol=interpol,
                            passport_copy=passport_copy,
                            passport_photo=passport_photo,
                            offer_letter=offer_letter,
                            mol_approval=signed_ol
                        )
                        
                        # Create visa process
                        VisaProcess.objects.create(candidate=candidate)
                        
                        stats['success'] += 1
                        print(f"Imported: {candidate_name} - Passport: {passport_no}")
                        
                except Exception as e:
                    stats['errors'] += 1
                    error_msg = f"Row {index+2}: Error - {str(e)}"
                    stats['error_details'].append(error_msg)
                    print(error_msg)
                    continue
            
            # Log the import activity
            log_activity(
                user=request.user,
                action='IMPORT',
                model_type='Candidate',
                details=f"Imported {stats['success']} candidates from Excel. {stats['errors']} errors, {stats['skipped']} skipped.",
                request=request
            )
            
            # Show success message with stats
            success_msg = f"✅ Import completed!\n"
            success_msg += f"📊 Total rows processed: {stats['total']}\n"
            success_msg += f"✅ Successfully imported: {stats['success']} candidates\n"
            
            if stats['agents_created'] > 0:
                success_msg += f"👤 New agents created: {stats['agents_created']}\n"
            if stats['errors'] > 0:
                success_msg += f"❌ Errors: {stats['errors']}\n"
            if stats['skipped'] > 0:
                success_msg += f"⚠️ Skipped: {stats['skipped']} (duplicates or empty rows)"
            
            messages.success(request, success_msg)
            
            # Show error details if any
            if stats['error_details']:
                messages.warning(request, "First few errors:")
                for error in stats['error_details'][:5]:
                    messages.warning(request, error)
                if len(stats['error_details']) > 5:
                    messages.warning(request, f"... and {len(stats['error_details'])-5} more errors")
            
        except Exception as e:
            messages.error(request, f'Error reading file: {str(e)}')
            print(f"Import error: {str(e)}")
        
        return redirect('import_excel')
    
    return render(request, 'imports/import.html')