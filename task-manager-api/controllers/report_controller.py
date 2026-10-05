from collections import Counter
from datetime import timedelta

from config.constants import DONE_STATUS, HIGH_PRIORITY_MAX, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, TASK_STATUSES
from controllers.validation import ensure_self_or_admin
from middlewares.error_handler import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import percentage, utcnow


class ReportController:
    def summary(self):
        now = utcnow()
        by_status = Task.count_by('status')
        by_priority = Task.count_by('priority')
        by_user_status = Task.count_by_user_and_status()
        overdue_tasks = Task.list_open_with_due_date_before(now)
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

        user_productivity = []
        for user in User.list_all():
            total = sum(count for (user_id, _), count in by_user_status.items() if user_id == user.id)
            completed = by_user_status.get((user.id, DONE_STATUS), 0)
            user_productivity.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': percentage(completed, total),
            })

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': Task.count(),
                'total_users': User.count(),
                'total_categories': Category.count(),
            },
            'tasks_by_status': {status: by_status.get(status, 0) for status in TASK_STATUSES},
            'tasks_by_priority': {label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS.items()},
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
                'tasks_completed_last_7_days': Task.count_completed_since(since),
            },
            'user_productivity': user_productivity,
        }

    def user_report(self, user_id, current_user):
        ensure_self_or_admin(user_id, current_user)
        user = User.get(user_id)
        if user is None:
            raise NotFoundError('Usuário não encontrado')

        tasks = Task.list_by_user(user_id)
        now = utcnow()
        by_status = Counter(task.status for task in tasks)
        total = len(tasks)
        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                **{status: by_status[status] for status in TASK_STATUSES},
                'overdue': sum(1 for task in tasks if task.is_overdue(now)),
                'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
                'completion_rate': percentage(by_status[DONE_STATUS], total),
            },
        }
