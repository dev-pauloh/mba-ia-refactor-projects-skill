TASK_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
CLOSED_STATUSES = ('done', 'cancelled')
DEFAULT_STATUS = 'pending'
DONE_STATUS = 'done'

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200
DATE_FORMAT = '%Y-%m-%d'

USER_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'
ADMIN_ROLE = 'admin'
MIN_PASSWORD_LENGTH = 4
EMAIL_PATTERN = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'

DEFAULT_COLOR = '#000000'
RECENT_ACTIVITY_DAYS = 7
