import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
import streamlit as st
import os

# File paths
STUDENTS_FILE = "data/students.csv"
PAYMENTS_FILE = "data/payments.csv"
INTERNSHIPS_FILE = "data/internships.csv"

def load_students_data():
    """Load student data from CSV file"""
    if os.path.exists(STUDENTS_FILE):
        return pd.read_csv(STUDENTS_FILE)
    return pd.DataFrame()

def load_payments_data():
    """Load payment data from CSV file"""
    if os.path.exists(PAYMENTS_FILE):
        return pd.read_csv(PAYMENTS_FILE)
    return pd.DataFrame()

def load_internships_data():
    """Load internship data from CSV file"""
    if os.path.exists(INTERNSHIPS_FILE):
        return pd.read_csv(INTERNSHIPS_FILE)
    return pd.DataFrame()

def save_students_data(df):
    """Save student data to CSV file"""
    df.to_csv(STUDENTS_FILE, index=False)

def save_payments_data(df):
    """Save payment data to CSV file"""
    df.to_csv(PAYMENTS_FILE, index=False)

def save_internships_data(df):
    """Save internship data to CSV file"""
    df.to_csv(INTERNSHIPS_FILE, index=False)

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

def format_currency(value):
    """Format value as BRL currency"""
    return f"R$ {value:.2f}".replace('.', ',')

def format_phone(phone):
    """Format phone number to standard format"""
    if not phone or pd.isna(phone):
        return ""
    
    # Remove non-digit characters
    phone_digits = ''.join(filter(str.isdigit, str(phone)))
    
    # Check length and format accordingly
    if len(phone_digits) == 11:  # With area code
        return f"({phone_digits[:2]}) {phone_digits[2:7]}-{phone_digits[7:]}"
    elif len(phone_digits) == 9:  # Without area code
        return f"{phone_digits[:5]}-{phone_digits[5:]}"
    else:
        return phone  # Return as is if it doesn't match expected formats

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
        try:
            # Get all payments for this student
            student_payments = payments_df[payments_df['phone'] == student['phone']]
            
            if student_payments.empty:
                # If no payments at all, consider overdue from enrollment date
                try:
                    enrollment_date = pd.to_datetime(student['enrollment_date'], errors='coerce')
                    if pd.isna(enrollment_date):
                        continue
                        
                    enrollment_date = enrollment_date.date()
                    if enrollment_date < today - timedelta(days=30):
                        days_overdue = (today - enrollment_date).days - 30
                        overdue_list.append({
                            **student.to_dict(),
                            'last_due_date': enrollment_date + timedelta(days=30),
                            'days_overdue': days_overdue
                        })
                except Exception as e:
                    print(f"Error processing enrollment date for {student.get('name', 'unknown')}: {e}")
                    continue
            else:
                try:
                    # Ensure due_date is datetime type
                    student_payments['due_date'] = pd.to_datetime(student_payments['due_date'], errors='coerce')
                    
                    # Filter to only get payments with due dates in the past and not paid
                    overdue_payments = student_payments[
                        (student_payments['status'] != 'paid') & 
                        (student_payments['due_date'].dt.date < today)
                    ]
                    
                    if not overdue_payments.empty:
                        # Find the oldest overdue payment
                        oldest_overdue = overdue_payments.sort_values('due_date').iloc[0]
                        due_date = oldest_overdue['due_date'].date()
                        days_overdue = (today - due_date).days
                        
                        # Add to overdue list
                        overdue_list.append({
                            **student.to_dict(),
                            'last_due_date': due_date,
                            'days_overdue': days_overdue
                        })
                except Exception as e:
                    print(f"Error processing payments for student {student.get('name', 'unknown')}: {e}")
                    continue
        except Exception as e:
            print(f"General error processing student {student.get('name', 'unknown')}: {e}")
            continue
    
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
    
    # Calculate expected revenue from all active students
    for _, student in active_students.iterrows():
        try:
            if pd.isna(student.get('monthly_fee', None)):
                continue
                
            enrollment_date = student.get('enrollment_date', None)
            if pd.isna(enrollment_date):
                continue
                
            # If student was enrolled before or in the target month
            enrollment_date = pd.to_datetime(enrollment_date, errors='coerce')
            if pd.isna(enrollment_date):
                continue
                
            if (enrollment_date.year < year) or (enrollment_date.year == year and enrollment_date.month <= month):
                total_expected += float(student['monthly_fee'])
        except Exception as e:
            print(f"Error calculating revenue for student {student.get('name', 'unknown')}: {e}")
            continue
    
    # Calculate actual received payments for the month
    if not payments_df.empty:
        try:
            month_payments = payments_df[
                (payments_df['month_reference'] == month) & 
                (payments_df['year_reference'] == year) & 
                (payments_df['status'] == 'paid')
            ]
            
            already_paid = month_payments['amount'].sum() if not month_payments.empty else 0
            return total_expected - already_paid
        except Exception as e:
            print(f"Error calculating received payments: {e}")
    
    # Return the expected revenue
    return total_expected

def get_student_internship_hours(internships_df, phone):
    """Calculate total internship hours for a student"""
    if internships_df.empty:
        return 0
    
    total_hours = 0
    
    for _, internship in internships_df.iterrows():
        try:
            # Students are stored as a comma-separated list of phone numbers
            students_str = str(internship.get('students', ''))
            if not students_str or pd.isna(students_str):
                continue
                
            students_in_internship = students_str.split(',')
            students_in_internship = [s.strip() for s in students_in_internship]
            
            if phone in students_in_internship:
                duration = internship.get('duration_hours', 0)
                if not pd.isna(duration):
                    total_hours += float(duration)
        except Exception as e:
            print(f"Error calculating internship hours: {e}")
            continue
    
    return total_hours

def get_student_internship_topics(internships_df, phone):
    """Get all internship topics for a student"""
    if internships_df.empty:
        return []
    
    topics = []
    
    for _, internship in internships_df.iterrows():
        try:
            # Students are stored as a comma-separated list of phone numbers
            students_str = str(internship.get('students', ''))
            if not students_str or pd.isna(students_str):
                continue
                
            students_in_internship = students_str.split(',')
            students_in_internship = [s.strip() for s in students_in_internship]
            
            if phone in students_in_internship:
                topic = internship.get('topic', '')
                if topic and not pd.isna(topic):
                    topics.append(topic)
        except Exception as e:
            print(f"Error getting internship topics: {e}")
            continue
    
    return list(set(topics))  # Remove duplicates

def validate_phone(phone):
    """Validate if phone number is in correct format"""
    if not phone:
        return False
    
    # Remove non-digit characters
    phone_digits = ''.join(filter(str.isdigit, str(phone)))
    
    # Check if it has at least 8 digits (minimum for a phone number)
    return len(phone_digits) >= 8

def get_months_between_dates(start_date, end_date):
    """Get list of months between two dates"""
    if not start_date or not end_date:
        return []
    
    try:
        start_date = pd.to_datetime(start_date, errors='coerce')
        end_date = pd.to_datetime(end_date, errors='coerce')
        
        if pd.isna(start_date) or pd.isna(end_date):
            return []
        
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
    except Exception as e:
        print(f"Error getting months between dates: {e}")
        return []

def generate_monthly_payments(student_phone, monthly_fee, enrollment_date, payment_plan=12, end_date=None, due_day=10):
    """Generate monthly payment records for a student based on payment plan
    
    Args:
        student_phone: Phone number of student
        monthly_fee: Monthly fee amount
        enrollment_date: Date of enrollment
        payment_plan: Number of installments (default: 12)
        end_date: Optional end date (if not provided, will calculate based on payment_plan)
        due_day: Day of the month for payment due date (default: 10)
    """
    try:
        # Convert payment_plan to int if it's not already
        payment_plan = int(payment_plan) if payment_plan else 12
        
        # If no end_date provided, calculate it based on payment_plan
        if not end_date:
            enrollment_date_dt = pd.to_datetime(enrollment_date, errors='coerce')
            if pd.isna(enrollment_date_dt):
                return []
                
            # Calculate end date based on payment plan (number of months)
            end_date = enrollment_date_dt.date() + pd.DateOffset(months=payment_plan)
        else:
            end_date = pd.to_datetime(end_date, errors='coerce')
            if pd.isna(end_date):
                enrollment_date_dt = pd.to_datetime(enrollment_date, errors='coerce')
                if pd.isna(enrollment_date_dt):
                    return []
                end_date = enrollment_date_dt.date() + pd.DateOffset(months=payment_plan)
            else:
                end_date = end_date.date()
            
        enrollment_date = pd.to_datetime(enrollment_date, errors='coerce')
        if pd.isna(enrollment_date):
            return []
            
        enrollment_date = enrollment_date.date()
        
        # Get list of months
        months = get_months_between_dates(enrollment_date, end_date)
        
        # Limit to the number of installments in payment_plan
        months = months[:payment_plan]
        
        payments = []
        
        # Ensure due_day is an integer between 1 and 28
        try:
            due_day = int(due_day)
            if due_day < 1 or due_day > 28:
                due_day = 10  # Default to 10th if invalid
        except (TypeError, ValueError):
            due_day = 10  # Default to 10th if not a number
                
        for month, year in months:
            # Due date is the specified day of each month
            due_date = datetime(year, month, due_day).date()
            
            # If enrollment date is after the due day, the first payment due date is next month
            if month == enrollment_date.month and year == enrollment_date.year and enrollment_date.day > due_day:
                continue
                
            payment = {
                'phone': student_phone,
                'payment_date': None,
                'due_date': due_date.strftime('%Y-%m-%d'),
                'amount': monthly_fee,
                'month_reference': month,
                'year_reference': year,
                'status': 'pending',
                'notes': f'Mensalidade {calendar.month_name[month]}/{year}'
            }
            
            payments.append(payment)
        
        return payments
    except Exception as e:
        print(f"Error generating monthly payments: {e}")
        return []
