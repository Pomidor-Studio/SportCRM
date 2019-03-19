import rules

# Detail about rule system: https://github.com/dfunckt/django-rules


@rules.predicate
def is_manager(user) -> bool:
    return user.is_manager


@rules.predicate
def is_coach(user) -> bool:
    return user.is_coach


# Generic permission, can be used, until detailed are needed
rules.add_perm('is_manager', rules.is_authenticated & is_manager)
rules.add_perm('is_coach', rules.is_authenticated & is_coach)


rules.add_perm('client', rules.is_authenticated & (is_manager | is_coach))
rules.add_perm('client.add', rules.is_authenticated & is_manager)
rules.add_perm('client.edit', rules.is_authenticated & is_manager)
rules.add_perm('client.delete', rules.is_authenticated & is_manager)

rules.add_perm('coach', rules.is_authenticated & (is_manager | is_coach))
rules.add_perm('coach.add', rules.is_authenticated & is_manager)
rules.add_perm('coach.edit', rules.is_authenticated & is_manager)
rules.add_perm('coach.delete', rules.is_authenticated & is_manager)

rules.add_perm('location', is_logged_manager)
rules.add_perm('location.add', is_logged_manager)
rules.add_perm('location.edit', is_logged_manager)
rules.add_perm('location.delete', is_logged_manager)
rules.add_perm('location.undelete', is_logged_manager)
rules.add_perm('location.view_archive', is_logged_manager)

rules.add_perm('location', rules.is_authenticated & (is_manager | is_coach))
rules.add_perm('location.add', rules.is_authenticated & is_manager)
rules.add_perm('location.edit', rules.is_authenticated & is_manager)
rules.add_perm('location.delete', rules.is_authenticated & is_manager)

rules.add_perm('subscription', rules.is_authenticated & is_manager)
rules.add_perm('subscription.add', rules.is_authenticated & is_manager)
rules.add_perm('subscription.edit', rules.is_authenticated & is_manager)
rules.add_perm('subscription.delete', rules.is_authenticated & is_manager)
