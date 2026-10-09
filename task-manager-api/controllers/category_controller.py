from controllers import validation
from services import category_service


def list_categories():
    return [
        {**category.to_dict(), 'task_count': task_count}
        for category, task_count in category_service.list_with_task_count()
    ]


def create_category(data):
    fields = validation.validate_category(data)
    return category_service.create_category(fields).to_dict()


def update_category(category_id, data):
    category_service.get_category(category_id)
    fields = validation.validate_category(data, partial=True)
    return category_service.update_category(category_id, fields).to_dict()


def delete_category(category_id):
    category_service.delete_category(category_id)
    return {'message': 'Categoria deletada'}
