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
