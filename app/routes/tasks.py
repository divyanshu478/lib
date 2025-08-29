from flask import Flask, Blueprint, redirect, Request, render_template, session, url_for, flash, request
from app import db
from app.models import FeesRecord
from app.models import Registration
from datetime import datetime, date, timedelta
import smtplib
from app.routes.email_pass import email_, pass_
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

task_bp = Blueprint('tasks',__name__)

@task_bp.route("/")
def students_list():

    if not session.get('admin'):
        flash("Please login as admin first", "error")
        return redirect(url_for('auth.login'))

    students = Registration.query.all()
    return render_template("student_list.html", students=students)




@task_bp.route("/toggle/<int:student_id>")
def toggle_status(student_id):
    student = Registration.query.get_or_404(student_id)
    # student.status = "Inactive" if student.status == "Active" else "Active"
    if student.status == "Active" :
        student.status = "Inactive"
        FeesRecord.query.filter_by(student_id=student.id).delete()
    else :
        student.status = "Active"
        student.joining_date = date.today()
        FeesRecord.query.filter_by(student_id=student.id).update({"fees_due_date": date.today()})

        fees_record = FeesRecord(
            student_id=student.id,
            fees_due_date=student.joining_date, 
            amount=student.fees,
            is_paid=False
        )
        db.session.add(fees_record)

    db.session.commit()
    return redirect(url_for('tasks.students_list'))


@task_bp.route("/registration", methods=['GET','POST'])
def registration():
    if request.method == 'POST':
        name = request.form.get('name')
        fathers_name = request.form.get('fathers_name')
        joining_date_str = request.form.get('joining_date')
        fees = request.form.get('fees')
        if not fees.isdigit():
            flash("Fees must be a number", "error")
            return render_template("registration.html")
        type_ = request.form.get('type')
        mobile_number = request.form.get('mobile_number')
        gmail = request.form.get('gmail')

        # Date convert
        try:
            joining_date = datetime.strptime(joining_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format", "error")
            return render_template("registration.html")

        new_student = Registration(
            name=name,
            fathers_name=fathers_name,
            joining_date=joining_date,
            fees=int(fees),
            type=type_,
            mobile_number=mobile_number,
            gmail=gmail,
            status='Active'
        )
        db.session.add(new_student)
        db.session.commit()

        # Create initial FeesRecord
    
        fees_record = FeesRecord(
            student_id=new_student.id,
            fees_due_date=joining_date,  # first due = joining date (example)
            amount=int(fees),
        )
        db.session.add(fees_record)
        db.session.commit()

        flash("Registered Successfully", "success")
        return redirect(url_for('tasks.thankyou'))

    return render_template("registration.html")



@task_bp.route("/delete_students", methods=['POST'])
def delete_students():
    if not session.get('admin'):
        flash("Please login as admin first", "error")
        return redirect(url_for('auth.login'))

    student_ids = request.form.getlist('student_ids')  # List of selected student IDs

    if student_ids:
        for sid in student_ids:
            student = Registration.query.get(int(sid))
            if student:
                # Also delete associated fees records
                FeesRecord.query.filter_by(student_id=student.id).delete()
                db.session.delete(student)
        db.session.commit()
        flash(f"{len(student_ids)} student(s) deleted successfully", "success")
    else:
        flash("No student selected", "error")

    return redirect(url_for('tasks.students_list'))


# -------------------------
# Fees Due List
# -------------------------
@task_bp.route("/fees_due")
def fees_due():
    if not session.get('admin'):
        flash("Please login as admin first", "error")
        return redirect(url_for('auth.login'))

    
    due_records = FeesRecord.query.join(Registration)\
                    .filter(FeesRecord.is_paid == 0)\
                    .filter(Registration.status == "Active")\
                    .all()
    return render_template("fees_due.html", records=due_records)


# -------------------------
# Mark Fees Paid
# -------------------------

@task_bp.route("/pay/<int:record_id>")
def pay_fees(record_id):
    record = FeesRecord.query.get_or_404(record_id)
    record.last_payment_date = date.today()
    record.is_paid = True   # Payment done

    # Next month due date
    try:
        next_due = record.fees_due_date.replace(month=record.fees_due_date.month + 1)
    except ValueError:
        next_due = record.fees_due_date.replace(year=record.fees_due_date.year + 1, month=1)
    record.fees_due_date = next_due

    db.session.commit()
    flash("Fees marked as paid", "success")
    return redirect(url_for('tasks.fees_due'))

@task_bp.route("/thankyou")
def thankyou() :

    return render_template("thankyou.html")

def update_due_status():
    today = date.today()
    records = FeesRecord.query.filter(
        FeesRecord.is_paid == True
    ).all()

    for r in records:
        if r.fees_due_date - timedelta(days=3) <= today:
            r.is_paid = False  # Automatically mark False

    db.session.commit()


def send_email() :
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
            server.starttls()
            server.login(email_, pass_)

            # ====fetch email Id=====
            unpaid_gmails = (
                        db.session.query(Registration.name, Registration.fees, Registration.gmail, FeesRecord.fees_due_date)
                        .join(FeesRecord, Registration.id == FeesRecord.student_id)
                        .filter(FeesRecord.is_paid == False)
                        .all()
                    )
            for student_details in unpaid_gmails :
                # print(student_details)
                formatted_date = student_details[3].strftime("%d-%m-%Y")
                # Message sender
                subject = "LIBRARY FEE REMINDER"
                body = f"""
Dear {student_details[0]},

This is a gentle reminder that your fee of Rs.{student_details[1]}/- is due on {formatted_date}.
Kindly ensure that you deposit the fee on or before the due date.

Please note that timely fee payment helps in the smooth functioning of the institution. 
We request you to deposit your fee on time to avoid any inconvenience.

Thank you,  
- Institution
    """
                
                # Create MIME message
                msg = MIMEMultipart()
                msg['From'] = f"Divyanshu Kumawat <{email_}>"  # <-- Display name here
                msg['To'] = student_details[2]
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))

                # msg = f"Subject: {subject}\n\n{body}"
                check = server.ehlo()
                if check[0] == 250 :
                    server.send_message(msg)
                    print("Send")
                else :
                    pass

        except Exception as e:
            print(e)
            # messagebox.showerror("Email not found", "Your email is not valid", parent= self.root)





