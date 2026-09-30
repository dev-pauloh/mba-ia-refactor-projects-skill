from collections import Counter
from datetime import timedelta

from config.constants import (
    DONE_STATUS, HIGH_PRIORITY_THRESHOLD, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, TASK_STATUSES,
)
from middlewares.error_handler import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage, utcnow


class ReportController:
    def summary(self):
        now = utcnow()
        by_status = Task.count_by_status()
        by_priority = Task.count_by_priority()
        overdue_tasks = Task.list_overdue(now)
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': Task.count(),
                'total_users': User.count(),
                'total_categories': Category.count(),
            },
            'tasks_by_status': {status: by_status.get(status, 0) for status in TASK_STATUSES},
            'tasks_by_priority': {
                label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()
            },
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': [
                    {
                        'id': task.id,
                        'title': task.title,
                        'due_date': str(task.due_date),
                        'days_overdue': (now - task.due_date).days,
                    }
                    for task in overdue_tasks
                ],
            },
            'recent_activity': {
                'tasks_created_last_7_days': Task.count_created_since(since),
                'tasks_completed_last_7_days': Task.count_done_since(since),
            },
            'user_productivity': [
                {
                    'user_id': user.id,
                    'user_name': user.name,
                    'total_tasks': total,
                    'completed_tasks': completed,
                    'completion_rate': calculate_percentage(completed, total),
                }
                for user, total, completed in User.list_with_task_stats()
            ],
        }

    def user_report(self, user_id):
        user = User.get_by_id(user_id)
        if user is None:
            raise NotFoundError('Usuário não encontrado')

        tasks = Task.list_by_user(user.id)
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
                'completion_rate': calculate_percentage(by_status[DONE_STATUS], total),
            },
        }
