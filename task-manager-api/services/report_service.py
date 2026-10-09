from collections import Counter
from datetime import timedelta

from sqlalchemy import case, func, select

from config.constants import (
    HIGH_PRIORITY_THRESHOLD, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, STATUS_DONE, TASK_STATUSES,
)
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from services import task_service, user_service
from utils.helpers import calculate_percentage, utcnow


def _count(model):
    return db.session.scalar(select(func.count(model.id)))


def _count_by_priority():
    rows = dict(db.session.execute(select(Task.priority, func.count()).group_by(Task.priority)).all())
    return {label: rows.get(priority, 0) for priority, label in PRIORITY_LABELS.items()}


def _overdue_tasks(now):
    tasks = db.session.scalars(
        select(Task).where(*task_service.overdue_filter(now)).order_by(Task.id)
    ).all()
    return [
        {
            'id': task.id,
            'title': task.title,
            'due_date': str(task.due_date),
            'days_overdue': (now - task.due_date).days,
        }
        for task in tasks
    ]


def _user_productivity():
    completed = func.coalesce(func.sum(case((Task.status == STATUS_DONE, 1), else_=0)), 0)
    stmt = (
        select(User.id, User.name, func.count(Task.id), completed)
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id)
    )
    return [
        {
            'user_id': user_id,
            'user_name': name,
            'total_tasks': total,
            'completed_tasks': done,
            'completion_rate': calculate_percentage(done, total),
        }
        for user_id, name, total, done in db.session.execute(stmt).all()
    ]


def summary():
    now = utcnow()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    overdue = _overdue_tasks(now)
    recent_created = db.session.scalar(select(func.count(Task.id)).where(Task.created_at >= since))
    recent_done = db.session.scalar(
        select(func.count(Task.id)).where(Task.status == STATUS_DONE, Task.updated_at >= since)
    )
    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': _count(Task),
            'total_users': _count(User),
            'total_categories': _count(Category),
        },
        'tasks_by_status': task_service.count_by_status(),
        'tasks_by_priority': _count_by_priority(),
        'overdue': {'count': len(overdue), 'tasks': overdue},
        'recent_activity': {
            'tasks_created_last_7_days': recent_created,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': _user_productivity(),
    }


def user_report(user_id):
    user = user_service.get_user(user_id)
    tasks = user_service.list_tasks_of(user_id)
    now = utcnow()
    by_status = Counter(task.status for task in tasks)
    total = len(tasks)
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            **{status: by_status[status] for status in TASK_STATUSES},
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_THRESHOLD),
            'completion_rate': calculate_percentage(by_status[STATUS_DONE], total),
        },
    }
