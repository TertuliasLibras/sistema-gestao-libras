import pandas as pd
import os
from datetime import datetime, timedelta
import re
import locale
from dateutil.relativedelta import relativedelta

# Try to set locale to Brazilian Portuguese for currency formatting
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        pass

# Data loading functions
def load_students_data():
    """Load student data from CSV file"""
    try:
        if os.path.exists("data/students.csv"):
            df = pd.read_csv("data/students.csv")
            # Ensure date columns are datetime objects
            for col in ['enrollment_date', 'cancellation_date']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading students data: {e}")
        return pd.DataFrame()

def load_payments_data():
    """Load payment data from CSV file"""
    try:
        if os.path.exists("data/payments.csv"):
            df = pd.read_csv("data/payments.csv")
            # Ensure date columns are datetime objects
            for col in ['payment_date', 'due_date']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading payments data: {e}")
        return pd.DataFrame()

def load_internships_data():
    """Load internship data from CSV file"""
    try:
        if os.path.exists("data/internships.csv"):
            df = pd.read_csv("data/internships.csv")
            # Ensure date column is datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading internships data: {e}")
        return pd.DataFrame()

# Data saving functions
def save_students_data(df):
    """Save student data to CSV file"""
    try:
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/students.csv", index=False)
        return True
    except Exception as e:
        print(f"Error saving students data: {e}")
        return False

def save_payments_data(df):
    """Save payment data to CSV file"""
    try:
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/payments.csv", index=False)
        return True
    except Exception as e:
        print(f"Error saving payments data: {e}")
        return False

def save_internships_data(df):
    """Save internship data to CSV file"""
    try:
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/internships.csv", index=False)
        return True
    except Exception as e:
        print(f"Error saving internships data: {e}")
        return False

# Data filtering functions
def get_active_students(students_df):
    """Get active students"""
    if students_df.empty:
        return pd.DataFrame()
    return students_df[students_df['status'] == 'active']

def get_canceled_students(students_df):
    """Get canceled students"""
    if students_df.empty:
        return pd.DataFrame()
    return students_df[students_df['status'] == 'canceled']

# Formatting functions
def format_currency(value):
    """Format value as BRL currency"""
    try:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"R$ {value}"

def format_phone(phone):
    """Format phone number to standard format"""
    if not phone:
        return ""
        
    # Remove non-digit characters
    digits = re.sub(r'\D', '', str(phone))
    
    # Format according to Brazilian phone number standards
    if len(digits) == 11:
        return f"({digits[0:2]}) {digits[2:7]}-{digits[7:11]}"
    elif len(digits) == 10:
        return f"({digits[0:2]}) {digits[2:6]}-{digits[6:10]}"
    else:
        return phone

# Business logic functions
def get_overdue_payments(students_df, payments_df):
    """Get students with overdue payments"""
    if students_df.empty or payments_df.empty:
        return pd.DataFrame()
    
    # Get active students
    active_students = get_active_students(students_df)
    if active_students.empty:
        return pd.DataFrame()
    
    # Create a dataframe to store overdue information
    overdue_list = []
    today = datetime.now().date()
    
    # Loop through active students
    for _, student in active_students.iterrows():
        # Get all payments for this student
        student_payments = payments_df[payments_df['phone'] == student['phone']]
        
        # Check for overdue payments
        if not student_payments.empty:
            # Filter to only get payments with due dates in the past
            overdue_payments = student_payments[
                (student_payments['status'] != 'paid') & 
                (student_payments['due_date'] < today)
            ]
            
            if not overdue_payments.empty:
                # Find the oldest overdue payment
                oldest_overdue = overdue_payments.sort_values('due_date').iloc[0]
                days_overdue = (today - oldest_overdue['due_date'].date()).days
                
                # Add to overdue list
                overdue_list.append({
                    'name': student['name'],
                    'phone': student['phone'],
                    'email': student['email'],
                    'monthly_fee': student['monthly_fee'],
                    'last_due_date': oldest_overdue['due_date'],
                    'days_overdue': days_overdue
                })
    
    # Create dataframe from overdue list
    if overdue_list:
        overdue_df = pd.DataFrame(overdue_list)
        return overdue_df.sort_values('days_overdue', ascending=False)
    
    return pd.DataFrame()

def calculate_monthly_revenue(students_df, payments_df, month, year):
    """Calculate projected monthly revenue"""
    if students_df.empty:
        return 0
    
    # Get active students
    active_students = get_active_students(students_df)
    if active_students.empty:
        return 0
    
    total_expected = 0
    total_received = 0
    
    # Calculate expected revenue from all active students
    for _, student in active_students.iterrows():
        enrollment_date = student['enrollment_date']
        if pd.isna(enrollment_date):
            continue
            
        # If student was enrolled before or in the target month
        enrollment_date = pd.to_datetime(enrollment_date)
        if (enrollment_date.year < year) or (enrollment_date.year == year and enrollment_date.month <= month):
            total_expected += float(student['monthly_fee'])
    
    # Calculate actual received payments for the month
    if not payments_df.empty:
        month_payments = payments_df[
            (payments_df['month_reference'] == month) & 
            (payments_df['year_reference'] == year) & 
            (payments_df['status'] == 'paid')
        ]
        
        if not month_payments.empty:
            total_received = month_payments['amount'].sum()
    
    # Return the expected revenue (what should be received)
    return total_expected

def get_student_internship_hours(internships_df, phone):
    """Calculate total internship hours for a student"""
    if internships_df.empty:
        return 0
    
    total_hours = 0
    
    for _, internship in internships_df.iterrows():
        # Check if student participated in this internship
        if phone in str(internship['students']).split(','):
            total_hours += float(internship['duration_hours'])
    
    return total_hours

def get_student_internship_topics(internships_df, phone):
    """Get all internship topics for a student"""
    if internships_df.empty:
        return []
    
    topics = []
    
    for _, internship in internships_df.iterrows():
        # Check if student participated in this internship
        if phone in str(internship['students']).split(','):
            topics.append(internship['topic'])
    
    return topics

def validate_phone(phone):
    """Validate if phone number is in correct format"""
    if not phone:
        return False
        
    # Remove non-digit characters
    digits = re.sub(r'\D', '', str(phone))
    
    # Check if it has 10 or 11 digits (Brazilian phone numbers)
    return len(digits) in [10, 11]

def get_months_between_dates(start_date, end_date=None):
    """Get list of months between two dates"""
    if not end_date:
        end_date = datetime.now().date()
    
    start_date = pd.to_datetime(start_date).date()
    end_date = pd.to_datetime(end_date).date()
    
    months = []
    current_date = start_date
    
    while current_date <= end_date:
        months.append((current_date.month, current_date.year))
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return months

def generate_monthly_payments(student_phone, monthly_fee, enrollment_date, end_date=None):
    """Generate monthly payment records for a student"""
    enrollment_date = pd.to_datetime(enrollment_date).date()
    
    if not end_date:
        end_date = datetime.now().date() + relativedelta(months=6)
    else:
        end_date = pd.to_datetime(end_date).date()
    
    # Get list of months between enrollment date and end date
    months = get_months_between_dates(enrollment_date, end_date)
    
    # Create payment records for each month
    payment_records = []
    
    for month, year in months:
        # Set due date to 10th of each month
        due_date = datetime(year, month, 10).date()
        
        # Skip if due date is in the past (for new students)
        if enrollment_date.day > 10 and month == enrollment_date.month and year == enrollment_date.year:
            # For new enrollments after the 10th, set due date to next month
            continue
        
        # Create payment record
        payment_record = {
            'phone': student_phone,
            'payment_date': None,
            'due_date': due_date,
            'amount': monthly_fee,
            'month_reference': month,
            'year_reference': year,
            'status': 'pending',
            'notes': ''
        }
        
        payment_records.append(payment_record)
    
    return payment_records
