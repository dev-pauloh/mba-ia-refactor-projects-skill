from config.constants import DEFAULT_CATEGORY_COLOR
from middlewares.error_handler import NotFoundError, ValidationError
from models.category import Category
from utils.helpers import is_valid_color


def validate_name(name):
    if not name or not isinstance(name, str):
        raise ValidationError('Nome é obrigatório')
    return name


def validate_color(color):
    if not is_valid_color(color):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
    return color


class CategoryController:
    def list_categories(self):
        result = []
        for category, task_count in Category.list_with_task_counts():
            data = category.to_dict()
            data['task_count'] = task_count
            result.append(data)
        return result

    def create_category(self, data):
        if not data:
            raise ValidationError('Dados inválidos')
        category = Category(
            name=validate_name(data.get('name')),
            description=data.get('description', ''),
            color=validate_color(data.get('color', DEFAULT_CATEGORY_COLOR)),
        )
        category.save()
        return category.to_dict()

    def update_category(self, category_id, data):
        category = self._get_or_404(category_id)
        if not data:
            raise ValidationError('Dados inválidos')
        if 'name' in data:
            category.name = validate_name(data['name'])
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = validate_color(data['color'])
        category.save()
        return category.to_dict()

    def delete_category(self, category_id):
        self._get_or_404(category_id).delete()

    @staticmethod
    def _get_or_404(category_id):
        category = Category.get_by_id(category_id)
        if category is None:
            raise NotFoundError('Categoria não encontrada')
        return category
