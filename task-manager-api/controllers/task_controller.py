import logging

from config.constants import (
    DEFAULT_PRIORITY, DEFAULT_TASK_STATUS, DONE_STATUS, MAX_PRIORITY,
    MAX_TITLE_LENGTH, MIN_PRIORITY, MIN_TITLE_LENGTH, TASK_STATUSES,
)
from middlewares.error_handler import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage, parse_date, parse_int, utcnow

logger = logging.getLogger(__name__)


def validate_title(title):
    if not title:
        raise ValidationError('Título é obrigatório')
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def validate_status(status):
    if status not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return status


def validate_priority(priority):
    value = parse_int(priority)
    if value is None:
        raise ValidationError('Prioridade inválida')
    if not MIN_PRIORITY <= value <= MAX_PRIORITY:
        raise ValidationError(f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}')
    return value


def validate_due_date(due_date):
    if not due_date:
        return None
    parsed = parse_date(due_date)
    if parsed is None:
        raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')
    return parsed


def validate_tags(tags):
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise ValidationError('Tags inválidas')
        return ','.join(tags)
    if tags is None or isinstance(tags, str):
        return tags
    raise ValidationError('Tags inválidas')


def ensure_user_exists(user_id):
    if not user_id:
        return None
    user_pk = parse_int(user_id)
    if user_pk is None:
        raise ValidationError('Usuário inválido')
    user = User.get_by_id(user_pk)
    if user is None:
        raise NotFoundError('Usuário não encontrado')
    return user


def ensure_category_exists(category_id):
    if not category_id:
        return None
    category_pk = parse_int(category_id)
    if category_pk is None:
        raise ValidationError('Categoria inválida')
    category = Category.get_by_id(category_pk)
    if category is None:
        raise NotFoundError('Categoria não encontrada')
    return category


def task_stats(tasks_by_status, total, overdue):
    done = tasks_by_status.get(DONE_STATUS, 0)
    return {
        'total': total,
        **{status: tasks_by_status.get(status, 0) for status in TASK_STATUSES},
        'overdue': overdue,
        'completion_rate': calculate_percentage(done, total),
    }


class TaskController:
    def __init__(self, notification_service):
        self.notification_service = notification_service

    def list_tasks(self):
        now = utcnow()
        result = []
        for task in Task.list_with_relations():
            data = task.to_dict()
            data['overdue'] = task.is_overdue(now)
            data['user_name'] = task.user.name if task.user else None
            data['category_name'] = task.category.name if task.category else None
            result.append(data)
        return result

    def get_task(self, task_id):
        task = self._get_or_404(task_id)
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return data

    def create_task(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        title = validate_title(data.get('title'))
        status = validate_status(data.get('status', DEFAULT_TASK_STATUS))
        priority = validate_priority(data.get('priority', DEFAULT_PRIORITY))
        user = ensure_user_exists(data.get('user_id'))
        category = ensure_category_exists(data.get('category_id'))
        due_date = validate_due_date(data.get('due_date'))
        tags = validate_tags(data.get('tags'))

        task = Task(
            title=title,
            description=data.get('description', ''),
            status=status,
            priority=priority,
            user_id=user.id if user else None,
            category_id=category.id if category else None,
            due_date=due_date,
            tags=tags or None,
        )
        task.save()
        logger.info('Task criada id=%s', task.id)
        if user:
            self.notification_service.notify_task_assigned(user, task)
        return task.to_dict()

    def update_task(self, task_id, data):
        task = self._get_or_404(task_id)
        if not data:
            raise ValidationError('Dados inválidos')

        if 'title' in data:
            task.title = validate_title(data['title'])
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = validate_status(data['status'])
        if 'priority' in data:
            task.priority = validate_priority(data['priority'])

        new_assignee = None
        if 'user_id' in data:
            user = ensure_user_exists(data['user_id'])
            if user and user.id != task.user_id:
                new_assignee = user
            task.user_id = user.id if user else None
        if 'category_id' in data:
            category = ensure_category_exists(data['category_id'])
            task.category_id = category.id if category else None
        if 'due_date' in data:
            task.due_date = validate_due_date(data['due_date'])
        if 'tags' in data:
            task.tags = validate_tags(data['tags'])

        task.touch()
        task.save()
        logger.info('Task atualizada id=%s', task.id)
        if new_assignee:
            self.notification_service.notify_task_assigned(new_assignee, task)
        return task.to_dict()

    def delete_task(self, task_id):
        task = self._get_or_404(task_id)
        task.delete()
        logger.info('Task deletada id=%s', task_id)

    def search_tasks(self, text, status, priority, user_id):
        priority_value = self._optional_int(priority, 'Prioridade inválida')
        user_value = self._optional_int(user_id, 'Usuário inválido')
        tasks = Task.search(text=text, status=status, priority=priority_value, user_id=user_value)
        return [task.to_dict() for task in tasks]

    def stats(self):
        overdue = len(Task.list_overdue(utcnow()))
        return task_stats(Task.count_by_status(), Task.count(), overdue)

    @staticmethod
    def _optional_int(value, message):
        if not value:
            return None
        parsed = parse_int(value)
        if parsed is None:
            raise ValidationError(message)
        return parsed

    @staticmethod
    def _get_or_404(task_id):
        task = Task.get_by_id(task_id)
        if task is None:
            raise NotFoundError('Task não encontrada')
        return task
