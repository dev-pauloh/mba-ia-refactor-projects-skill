from controllers import validation
from services import task_service
from utils.helpers import utcnow


def _with_overdue(task, now):
    return {**task.to_dict(), 'overdue': task.is_overdue(now)}


def list_tasks():
    now = utcnow()
    return [
        {
            **_with_overdue(task, now),
            'user_name': task.user.name if task.user else None,
            'category_name': task.category.name if task.category else None,
        }
        for task in task_service.list_tasks_with_relations()
    ]


def get_task(task_id):
    return _with_overdue(task_service.get_task(task_id), utcnow())


def create_task(data):
    fields = validation.validate_task(data)
    return task_service.create_task(fields).to_dict()


def update_task(task_id, data):
    task_service.get_task(task_id)
    fields = validation.validate_task(data, partial=True)
    return task_service.update_task(task_id, fields).to_dict()


def delete_task(task_id):
    task_service.delete_task(task_id)
    return {'message': 'Task deletada com sucesso'}


def search_tasks(args):
    filters = validation.validate_search(args)
    return [task.to_dict() for task in task_service.search_tasks(**filters)]


def task_stats():
    return task_service.stats()
