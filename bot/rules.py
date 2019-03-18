import rules

from crm.rules import is_logged_manager

rules.add_perm('message_ignorance', is_logged_manager)
