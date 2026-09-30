"""Constantes de domínio compartilhadas por models e controllers."""

TASK_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
DEFAULT_TASK_STATUS = 'pending'
DONE_STATUS = 'done'
CLOSED_STATUSES = ('done', 'cancelled')

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2  # prioridades <= 2 contam como alta prioridade
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200

USER_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'
ADMIN_ROLE = 'admin'
MIN_PASSWORD_LENGTH = 4

DEFAULT_CATEGORY_COLOR = '#000000'

RECENT_ACTIVITY_DAYS = 7
DATE_FORMAT = '%Y-%m-%d'
