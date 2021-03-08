import json
import requests
from requests.api import get
from Journey import Journey
from utils import get_tokens

#l'URL de base à toutes les requête à l'API avec le principe de recherche par région 
ROOT_URL = 'https://api.navitia.io/v1/coverage/'

def get_journeys(departure_point, arrival_point, departure_date, region):
    
    mode = 'journeys?'
    starting_from = 'from='+departure_point
    going_to = 'to='+arrival_point
    at_time = 'datetime='+departure_date

    url_final = ROOT_URL+region+mode+starting_from+'&'+going_to+'&'+at_time

    data = requests.get(url=url_final, auth=(get_tokens('navitia'), ''))

    print(url_final)



    data = data.json()["journeys"][0]

    journey = Journey(
        data["sections"][1]["from"]["name"], 
        data["sections"][1]["to"]["name"], 
        data["requested_date_time"], 
        data["departure_date_time"], 
        data["arrival_date_time"], 
        data["duration"], 
        data["sections"][1]["display_informations"]["physical_mode"],
        data["sections"][1]["display_informations"]["name"],
        data["sections"][1]["display_informations"]["network"],
        data["sections"][1]["display_informations"]["trip_short_name"],
        data["sections"][1]["stop_date_times"])

    return journey

#fonction à laquelle on peut passer un objet place de type string afin de tenter de voir s'il existe des arrêts qui matchent avec le string de recherche
def auto_complete_places(place, region):

    #récupération des variables et mise en place de l'URL de requête
    #pt_objects fait référence à des objets de transport en commun
    looking_for = 'pt_objects?'
    #q= est la commande qui me permet de faire appel à l'autocomplétion
    query = 'q='+''.join(place.split())
    #type[]=stop_area permet de dire qu'on ne veut que des arrêt de transports en commun
    object_type = 'type[]=stop_area'
    #Concaténation de l'URL final avec le ROOT_URL définit plus haut et la région passée en paramètre
    url_final = ROOT_URL+region+'/'+looking_for+query+'&'+object_type
    
    print("Requesting @ "+url_final)
    #requète sur l'API grâce à la librairie requests avec l'ajout du token de manière dynamique
    data = requests.get(url=url_final, auth=(get_tokens('navitia'), ''))
    #on stocke le tableau de résultats dans data
    dict_results = {}
    
    if 'pt_objects' not in data.json():
        return dict_results

    data = data.json()['pt_objects']
    
    #on fait une boucle qui va stocker dans un dictionnaire sous forme de key:value le nom commercial de l'arrêt et son ID unique 
    for result in data:
        dict_results.update({result['stop_area']['name']:result['stop_area']['id']})

    return dict_results