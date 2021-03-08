import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler, Filters, Handler, MessageHandler, Updater
from navitia_wrapper import get_journeys, auto_complete_places
from utils import get_tokens

#mise en place d'un logger afin de gérer l'affichage des erreurs sur la console
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

#création des variables retournées au ConversationHandler
DESTINATION, AUTOCOMPLETE_DEP, DEPARTURE, DATETIME, RESULT, AUTOCOMPLETE_DEST = range(6)

#création de la liste dans laquelle les résultats intermédiaires (point de départ, point d'arrivé, heure de départ) seront stockés
list_result = []

#fonction callback de la commande /recherche
def recherche(update, context):

    update.message.reply_text('Point de départ :')

    return DEPARTURE

#fonction callback qui va renvoyer un tableau de boutons résultant d'une recherche de type "autocomplete" vers l'api navitia
def auto_complete_dep(update: Update, context: CallbackContext):
    #la fonction auto_complete_places renvoi un dictionnaire qui a pour forme {key="NomDeLArret", value="IDNavitiadeLArret"}
    dict = auto_complete_places(update.effective_message.text, 'fr-se')

    list_buttons = []

    if not dict:
        context.bot.sendMessage(chat_id=update.effective_chat.id, text='Désolé je ne comprend pas')
        return DEPARTURE

    #remplissage de la liste de bouttons avec une instance de la classe InlineKeyboardButton pour chaque item du dictionnaire
    for key, value in dict.items():
        list_buttons.append([InlineKeyboardButton(text=key, callback_data=key+'/'+value)])

    #création du clavier à partir de la liste de bouttons
    reply_keyboard = InlineKeyboardMarkup(list_buttons)

    #envoi d'une réponse à l'utilisateur, avec pour clavier notre liste de bouttons
    context.bot.sendMessage(chat_id=update.effective_chat.id, text='Laquelle de ces propositions est la bonne ?', reply_markup=reply_keyboard)
    
    return AUTOCOMPLETE_DEP


#deuxième fonction callback d'auto-completion (une pour le point de départ et une pour la destination)
def auto_complete_dest(update: Update, context: CallbackContext):
    dict = auto_complete_places(update.effective_message.text, 'fr-se')
    list_buttons = []

    if not dict:
        context.bot.sendMessage(chat_id=update.effective_chat.id, text='Désolé je ne comprend pas')
        return DESTINATION

    for key, value in dict.items():
        list_buttons.append([InlineKeyboardButton(text=key, callback_data=key+'/'+value)])

    reply_keyboard = InlineKeyboardMarkup(list_buttons)

    context.bot.sendMessage(chat_id=update.effective_chat.id, text='Laquelle de ces propositions est la bonne ?', reply_markup=reply_keyboard)
    
    return AUTOCOMPLETE_DEST


def destination(update, context):
    #récupération de la query courante
    query = update.callback_query

    #cette ligne est obligatoire dans le processus de récupération/traîtement d'une callbackquerry
    query.answer()

    temp_list = query.data.split('/')

    #ajout de la donnée du bouton (IDdeLArret) à la liste de de résultat 
    list_result.append(temp_list[1])

    print(list_result)

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=f'Ok pour {temp_list[0]}!\nPoint d\'arrivée :')

    return DESTINATION


def datetime(update, context):
    #récupération de la query courante
    query = update.callback_query

    #cette ligne est obligatoire dans le processus de récupération/traîtement d'une callbackquerry
    query.answer()

    temp_list = query.data.split('/')

    #ajout de la donnée du bouton (IDdeLArret) à la liste de de résultat 
    list_result.append(temp_list[1])

    

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=f'Ok pour {temp_list[0]}!\nQuelle heure?')

    return DATETIME


#une des deux commandes callback qui met fin au ConversationHandler
def result(update, context):
    #stocke le résultat de la réponse précédente dans la liste de résultat
    list_result.append(update.effective_message.text)

    print(list_result)

    #get_journey retoune un objet journey, résultat d'une requête à l'API Navitia, elle prend en paramètre les items de la liste de résultats ainsi que la région de recherche
    journey = get_journeys(list_result[0], list_result[1], list_result[2], 'fr-se/')

    #formatage de la string qui va être renvoyé à l'utilisateur avec les différentes propriétés de l'objet journey
    reply = f"""Vers = {journey.arrival_point}
    Depuis = {journey.departure_point}
    Date départ = {journey.human_readable_date(journey.departure_time)}
    Date arrivée = {journey.human_readable_date(journey.arrival_time)}
    Durée = {journey.duration/60}
    Mode = {journey.pysical_mode}
    Réseau = {journey.network}
    Nom du Trajet = {journey.name}
    Trajet ID = {journey.trip_short_name}"""
    #envoi de la réponse à l'utilisateur et suppression des éventuels claviers restants des autre fonctions
    update.message.reply_text(reply, reply_markup=ReplyKeyboardRemove())

    #on vide la liste de résultats pour que la liste soit prète pour la prochaine requette
    list_result.clear()

    #on met fin à la conversation
    return ConversationHandler.END

#deuxième fonction qui met fin à la conversation, callback de la commande /cancel, elle permet de sortir du processus de recherche de voyages en transport en commun
def cancel(update, context) :

    update.message.reply_text("Annulation réussie!")

    list_result.clear()

    return ConversationHandler.END

def main():
    #créer l'updater en lui passant le token de l'API telegram
    updater = Updater(get_tokens('telegram'))

    #stoker le dispatcher pour y ajouter les handlers
    dispatcher = updater.dispatcher

    #ajout du conversation handler avec les états DESTINATION, AUTOCOMPLETE 1, DEPARTURE, AUTOCOMPLETE 2 , et DATETIME
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('r', recherche)],
        states={
            DEPARTURE: [MessageHandler(Filters.text & ~Filters.command, auto_complete_dep),],
            AUTOCOMPLETE_DEP: [CallbackQueryHandler(destination)],
            DESTINATION: [MessageHandler(Filters.text & ~Filters.command, auto_complete_dest)],
            AUTOCOMPLETE_DEST: [CallbackQueryHandler(datetime)],
            DATETIME: [MessageHandler(Filters.text & ~Filters.command, result)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    #ajout du conversation handler au dispatcher (tous les autres handlers sont ajouter implicitement)
    dispatcher.add_handler(conv_handler)

    #démare le bot
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()