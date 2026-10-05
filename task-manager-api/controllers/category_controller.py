from config.constants import DEFAULT_COLOR
from controllers.validation import require_body, require_name
from database import db
from middlewares.error_handler import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from utils.helpers import is_valid_color


def _validate_color(color):
    if not is_valid_color(color):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
    return color


class CategoryController:
    def list_categories(self):
        task_counts = Task.count_by('category_id')
        result = []
        for category in Category.list_all():
            data = category.to_dict()
            data['task_count'] = task_counts.get(category.id, 0)
            result.append(data)
        return result

    def create_category(self, data):
        require_body(data)
        if not data.get('name'):
            raise ValidationError('Nome é obrigatório')
        category = Category(
            name=require_name(data['name']),
            description=data.get('description', ''),
            color=_validate_color(data.get('color', DEFAULT_COLOR)),
        )
        db.session.add(category)
        db.session.commit()
        return category.to_dict()

    def update_category(self, category_id, data):
        category = self._get_or_404(category_id)
        require_body(data)
        if 'name' in data:
            category.name = require_name(data['name'])
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = _validate_color(data['color'])
        db.session.commit()
        return category.to_dict()

    def delete_category(self, category_id):
        category = self._get_or_404(category_id)
        Task.detach_category(category_id)
        db.session.delete(category)
        db.session.commit()

    @staticmethod
    def _get_or_404(category_id):
        category = Category.get(category_id)
        if category is None:
            raise NotFoundError('Categoria não encontrada')
        return category
