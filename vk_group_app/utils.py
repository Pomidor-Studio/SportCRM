from contrib.text_utils import pluralize


def signed_clients_display(amount):
    prefix = pluralize('Записался', 'Записалось', 'Записалось', amount)
    postfix = pluralize('человек', 'человека', 'человек', amount)
    return f'{prefix} {amount} {postfix}'
