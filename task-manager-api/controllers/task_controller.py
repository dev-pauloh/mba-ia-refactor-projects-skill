import logging
from datetime import datetime

from config.constants import (
    DATE_FORMAT, DEFAULT_PRIORITY, DEFAULT_STATUS, DONE_STATUS, PRIORITY_MAX, PRIORITY_MIN,
    TASK_STATUSES, TITLE_MAX_LENGTH, TITLE_MIN_LENGTH,
)
from controllers.validation import parse_int, require_body
from database import db
from middlewares.error_handler import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import percentage, utcnow

logger = logging.getLogger(__name__)


def _validate_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def _validate_priority(priority):
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise ValidationError('Prioridade inválida')
    if priority < PRIORITY_MIN or priority > PRIORITY_MAX:
        raise ValidationError(f'Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}')
    return priority


def _validate_reference(model, ref_id, message):
    """Confere se o id referenciado existe; None/0/'' desassocia."""
    if not ref_id:
        return None
    ref_id = parse_int(ref_id, 'Identificador inválido')
    if model.get(ref_id) is None:
        raise NotFoundError(message)
    return ref_id


def _validate_due_date(value):
    if not value:
        return None
    if not isinstance(value, str):
        raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        raise ValidationError('Formato de data inválido. Use YYYY-MM-DD') from None


def _validate_tags(tags):
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise ValidationError('Tags inválidas')
        return ','.join(tags)
    if tags is None or isinstance(tags, str):
        return tags or None
    raise ValidationError('Tags inválidas')


def validate_task_payload(data, partial):
    """Valida o corpo de criação (partial=False) ou atualização (partial=True).

    Retorna apenas os campos presentes, já normalizados para o model.
    """
    require_body(data)

    if not partial:
        if not data.get('title'):
            raise ValidationError('Título é obrigatório')
        data = {'description': '', 'status': DEFAULT_STATUS, 'priority': DEFAULT_PRIORITY, **data}

    fields = {}
    if 'title' in data:
        fields['title'] = _validate_title(data['title'])
    if 'description' in data:
        fields['description'] = data['description']
    if 'status' in data:
        if data['status'] not in TASK_STATUSES:
            raise ValidationError('Status inválido')
        fields['status'] = data['status']
    if 'priority' in data:
        fields['priority'] = _validate_priority(data['priority'])
    if 'user_id' in data:
        fields['user_id'] = _validate_reference(User, data['user_id'], 'Usuário não encontrado')
    if 'category_id' in data:
        fields['category_id'] = _validate_reference(Category, data['category_id'], 'Categoria não encontrada')
    if 'due_date' in data:
        fields['due_date'] = _validate_due_date(data['due_date'])
    if 'tags' in data:
        fields['tags'] = _validate_tags(data['tags'])
    return fields


class TaskController:
    def __init__(self, notification_service):
        self.notification_service = notification_service

    def list_tasks(self):
        now = utcnow()
        result = []
        for task in Task.list_all(with_relations=True):
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
        fields = validate_task_payload(data, partial=False)
        task = Task(**fields)
        db.session.add(task)
        db.session.commit()
        logger.info('Task criada: id=%s', task.id)
        self._notify_assignment(task)
        return task.to_dict()

    def update_task(self, task_id, data):
        task = self._get_or_404(task_id)
        fields = validate_task_payload(data, partial=True)
        previous_user_id = task.user_id
        for name, value in fields.items():
            setattr(task, name, value)
        task.updated_at = utcnow()
        db.session.commit()
        logger.info('Task atualizada: id=%s', task.id)
        if task.user_id != previous_user_id:
            self._notify_assignment(task)
        return task.to_dict()

    def delete_task(self, task_id):
        task = self._get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        logger.info('Task deletada: id=%s', task_id)

    def search_tasks(self, text, status, priority, user_id):
        priority = parse_int(priority, 'Prioridade inválida') if priority else None
        user_id = parse_int(user_id, 'user_id inválido') if user_id else None
        tasks = Task.search(text=text, status=status, priority=priority, user_id=user_id)
        return [task.to_dict() for task in tasks]

    def stats(self):
        total = Task.count()
        by_status = Task.count_by('status')
        done = by_status.get(DONE_STATUS, 0)
        stats = {status: by_status.get(status, 0) for status in TASK_STATUSES}
        stats.update({
            'total': total,
            'overdue': len(Task.list_open_with_due_date_before(utcnow())),
            'completion_rate': percentage(done, total),
        })
        return stats

    def _get_or_404(self, task_id):
        task = Task.get(task_id)
        if task is None:
            raise NotFoundError('Task não encontrada')
        return task

    def _notify_assignment(self, task):
        if task.user is not None:
            self.notification_service.notify_task_assigned(task.user, task)
