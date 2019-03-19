import rules

from crm.rules import is_logged_manager

rules.add_perm('message.ignorance', is_logged_manager)
rules.add_perm('message.template', is_logged_manager)
