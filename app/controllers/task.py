from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.task import Task, Reminder
from app import db
from datetime import datetime

task_bp = Blueprint('task', __name__)

@task_bp.route('/')
@login_required
def calendar():
    return render_template('calendar.html')

@task_bp.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    events = []
    for task in tasks:
        events.append({
            'id': task.id,
            'title': task.titre,
            'start': task.date_echeance.isoformat(),
            'category': task.categorie,
            'status': task.statut
        })
    return jsonify(events)

@task_bp.route('/task/new', methods=['GET', 'POST'])
@login_required
def new_task():
    if request.method == 'POST':
        task = Task(
            user_id=current_user.id,
            titre=request.form['titre'],
            description=request.form['description'],
            categorie=request.form['categorie'],
            date_echeance=datetime.strptime(request.form['date_echeance'], '%Y-%m-%dT%H:%M'),
            mode_rappel=request.form['mode_rappel'],
            recurrence=request.form.get('recurrence')
        )
        
        if request.form.get('reminder_date'):
            reminder = Reminder(
                date_rappel=datetime.strptime(request.form['reminder_date'], '%Y-%m-%dT%H:%M')
            )
            task.reminders.append(reminder)
        
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully', 'success')
        return redirect(url_for('task.calendar'))
        
    return render_template('task/new.html')

@task_bp.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('task.calendar'))
        
    if request.method == 'POST':
        task.titre = request.form['titre']
        task.description = request.form['description']
        task.categorie = request.form['categorie']
        task.date_echeance = datetime.strptime(request.form['date_echeance'], '%Y-%m-%dT%H:%M')
        task.mode_rappel = request.form['mode_rappel']
        task.recurrence = request.form.get('recurrence')
        
        db.session.commit()
        flash('Task updated successfully', 'success')
        return redirect(url_for('task.calendar'))
        
    return render_template('task/edit.html', task=task)

@task_bp.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('task.calendar'))
        
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully', 'success')
    return redirect(url_for('task.calendar'))

@task_bp.route('/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    task.statut = 'completed' if task.statut == 'pending' else 'pending'
    db.session.commit()
    return jsonify({'status': task.statut})