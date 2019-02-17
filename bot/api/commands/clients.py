from crm.models import Client
from bot.api.command_system import Command
from datetime import datetime, timezone


def get_info_subscription(user_id):

    messages = []
    current_date = datetime.now(timezone.utc)

    vk_user_id = user_id

    client = Client.objects.filter(vk_user_id=vk_user_id)
    check_cl = client.count()

    if not check_cl:
        messages.append('Вас нет в базе!')
        return ''.join(messages), ''

    if check_cl > 1:
        messages.append('На ваш аккаунт зарегистрировано несколько учеников!\n')        

    for cl in client:      
        messages.append('\n')        
        name = cl.name
        balance = cl.balance

        messages.extend([name, '!\n'])
        if balance:
            messages.extend(['Ваш баланс: ', str(balance), '\n'])            
        
        messages.append('Информация о ваших абонементах:\n')            

        subscriptions = cl.clientsubscriptions_set.filter(
            end_date__gte=current_date, 
            visits_left__gt=0)
        check_sub = subscriptions.exists()

        if not check_sub and check_cl == 1:            
            messages = [name, '!\nВы еще не приобрели абонемент!']
            #return ''.join(message), ''
            # Строго говоря тут return не нужен, ибо и так из цикла вывалимся.
        elif not check_sub:
            messages.append('\nВы еще не приобрели абонемент!\n')                        

        for idx, sub in enumerate(subscriptions, start=1):
            messages.extend([
                str(idx), ') ', sub.subscription.name,
                '\nОстаток посещений: ', str(sub.visits_left),
                '\nДействующий до: ', 
                '{:%d-%m-%Y}'.format(sub.end_date), '\n'
            ])
            
    return ''.join(messages), ''


clients_command = Command()

clients_command.keys = ['абонементы', 'мои абонементы', 'информация о моих абонементах']
clients_command.description = 'Информация о Ваших абонементах'
clients_command.process = get_info_subscription
