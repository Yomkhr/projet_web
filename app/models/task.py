from app import db
from datetime import datetime

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    categorie = db.Column(db.String(50), nullable=False)  # 'rendez-vous', 'faculte', 'vie_quotidienne', 'custom'
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_echeance = db.Column(db.DateTime, nullable=False)
    mode_rappel = db.Column(db.String(20))  # 'email', 'sms', 'both'
    statut = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'cancelled'
    recurrence = db.Column(db.String(20))  # 'daily', 'weekly', 'monthly'
    reminders = db.relationship('Reminder', backref='task', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Task {self.titre}>'

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    date_rappel = db.Column(db.DateTime, nullable=False)
    sent = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Reminder for Task {self.task_id} at {self.date_rappel}>'