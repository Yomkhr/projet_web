from flask import current_app
from flask_mail import Message
from twilio.rest import Client
from app import db, mail
from app.models.task import Task, Reminder
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
flask_app = None

def send_email_reminder(task, user):
    msg = Message(
        subject=f'Reminder: {task.titre}',
        recipients=[user.email],
        body=f'''Hi {user.prenom},

This is a reminder for your task:
{task.titre}

Due: {task.date_echeance.strftime('%Y-%m-%d %H:%M')}
Category: {task.categorie}

Description:
{task.description}

Best regards,
Work Reminder''')
    mail.send(msg)

def send_sms_reminder(task, user):
    if not user.telephone:
        return
        
    client = Client(current_app.config['TWILIO_ACCOUNT_SID'],
                   current_app.config['TWILIO_AUTH_TOKEN'])
    
    message = client.messages.create(
        body=f'Reminder: {task.titre} is due on {task.date_echeance.strftime("%Y-%m-%d %H:%M")}',
        from_=current_app.config['TWILIO_PHONE_NUMBER'],
        to=user.telephone
    )

def check_reminders():
    """Check for pending reminders and send them"""
    global flask_app
    if not flask_app:
        return
        
    with flask_app.app_context():
        now = datetime.utcnow()
        pending_reminders = Reminder.query.filter(
            Reminder.date_rappel <= now,
            Reminder.sent == False
        ).all()
        
        for reminder in pending_reminders:
            task = reminder.task
            user = task.user
            
            if task.mode_rappel in ['email', 'both']:
                try:
                    send_email_reminder(task, user)
                except Exception as e:
                    current_app.logger.error(f'Failed to send email reminder: {str(e)}')
            
            if task.mode_rappel in ['sms', 'both']:
                try:
                    send_sms_reminder(task, user)
                except Exception as e:
                    current_app.logger.error(f'Failed to send SMS reminder: {str(e)}')
            
            reminder.sent = True
            db.session.commit()

def schedule_recurring_tasks():
    """Create new instances of recurring tasks"""
    global flask_app
    if not flask_app:
        return
        
    with flask_app.app_context():
        now = datetime.utcnow()
        tasks = Task.query.filter(Task.recurrence.isnot(None)).all()
        
        for task in tasks:
            if task.date_echeance < now:
                # Calculate next occurrence
                if task.recurrence == 'daily':
                    next_date = task.date_echeance + timedelta(days=1)
                elif task.recurrence == 'weekly':
                    next_date = task.date_echeance + timedelta(weeks=1)
                elif task.recurrence == 'monthly':
                    # Add one month (approximately)
                    next_date = task.date_echeance + timedelta(days=30)
                
                # Create new task instance
                new_task = Task(
                    user_id=task.user_id,
                    titre=task.titre,
                    description=task.description,
                    categorie=task.categorie,
                    date_echeance=next_date,
                    mode_rappel=task.mode_rappel,
                    recurrence=task.recurrence
                )
                
                # Create reminder if needed
                if task.reminders:
                    time_before = task.date_echeance - task.reminders[0].date_rappel
                    reminder = Reminder(
                        date_rappel=next_date - time_before
                    )
                    new_task.reminders.append(reminder)
                
                db.session.add(new_task)
                db.session.commit()

def start_scheduler(app):
    """Start the background scheduler for reminders and recurring tasks"""
    global flask_app
    flask_app = app
    
    if not scheduler.running:
        scheduler.add_job(check_reminders, 'interval', minutes=1)
        scheduler.add_job(schedule_recurring_tasks, 'interval', hours=1)
        scheduler.start()