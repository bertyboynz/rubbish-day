import logging
from flask import Flask, request, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
import json
#import sys
import requests
import ssl
import urllib3
from datetime import datetime
from bs4 import BeautifulSoup

app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)
app.logger.setLevel(logging.DEBUG)

@app.route("/", methods=['GET'])
def root():
    return redirect("/status", code=302)

@app.route("/status", methods=['GET'])
def status():
    scriptName = '/status'
    app.logger.debug(scriptName+': testing debug log')
    app.logger.warning(scriptName+': testing warning log')
    app.logger.error(scriptName+': testing error log')
    app.logger.info(scriptName+': testing info log')
    output = {}
    output['value'] = 'flask is running'
    return json.dumps(output)

@app.route("/rubbish-day", methods=['GET'])
def rubbish_day():
    scriptName = '/rubbish-day'
    # class CustomHttpAdapter (requests.adapters.HTTPAdapter):
    #     # "Transport adapter" that allows us to use custom ssl_context.

    #     def __init__(self, ssl_context=None, **kwargs):
    #         self.ssl_context = ssl_context
    #         super().__init__(**kwargs)

    #     def init_poolmanager(self, connections, maxsize, block=False):
    #         self.poolmanager = urllib3.poolmanager.PoolManager(
    #             num_pools=connections, maxsize=maxsize,
    #             block=block, ssl_context=self.ssl_context)

    # def get_legacy_session():
    #     ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    #     ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    #     session = requests.session()
    #     session.mount('https://', CustomHttpAdapter(ctx))
    #     return session

    # Suppress only the single warning from urllib3 needed.
    from urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    # For debug output
    # Add '&debug' to url to log richer info in Flask logs
    debugmode = request.args.get('debug')
    if debugmode is None :
        debugmode = True ######## change this guy right here
    else :
        debugmode = True

    # Initialise strings to prevent errors later
    output = {}
    output['value'] = 'invalid addressid specified'
    addressId = request.args.get('addressid')

    # Sanity check the addressid parameter
    if addressId is None or len(addressId) != 11 :
        return json.dumps(output)
    httpheaders = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
    }
    baseUrl = 'https://new.aucklandcouncil.govt.nz'
    thisUrl = '/en/rubbish-recycling/rubbish-recycling-collections/rubbish-recycling-collection-days/'+addressId+'.html'
    url = baseUrl+thisUrl
    app.logger.debug(scriptName+': Scraping page from '+thisUrl)
    try:
        response = requests.get(url, headers=httpheaders) #, verify=False)
        # response = get_legacy_session().get(url)
        if debugmode :
            app.logger.debug(scriptName+': > GET response code is '+str(response.status_code))
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        app.logger.error(scriptName+': > Page GET says '+str(err))
        app.logger.error(scriptName+': > Error is fatal, exiting with no output')
        return json.dumps(output)

    soup = BeautifulSoup(response.content, 'html.parser')
    # addressBlock = soup.find_all(attrs={'class': 'm-b-2'})
    address_block = soup.find("h2")
    if not address_block:
        return "Unknown address"
    else: 
       street = address_block.find("span", class_="heading")
       suburb = address_block.find("span", class_="subheading")
       if street and suburb:
           addressBlock = f"{street.get_text(strip=True)}, {suburb.get_text(strip=True)}"
       elif street:
           addressBlock = street.get_text(strip=True)
       elif suburb:
           addressBlock = suburb.get_text(strip=True)
       else:
           addressBlock = address_block.get_text(strip=True)

    # collectionInfo  = soup.find_all(attrs={'class': 'collectionDayDate'})
    
    # rubbishInfo = collectionInfo[0]
    # foodscrapsInfo = collectionInfo[1]
    # recycleInfo = collectionInfo[2]
    
    # # RUBBISH INFO
    # rubbishDate = rubbishInfo.find("strong").get_text()
    # if debugmode :
    #     app.logger.debug(scriptName+": > INFO: Rubbish Collection info: "+str(rubbishInfo)+'\n')
    #     app.logger.debug(scriptName+": > INFO: Next rubbish collection date is -  "+str(rubbishDate)+'\n')
    
    # # FOODSCRAPS INFO
    # foodscrapsDate = foodscrapsInfo.find("strong").get_text()
    # if debugmode :
    #     app.logger.debug(scriptName+": > INFO: Foodscraps Collection info: "+str(foodscrapsInfo)+'\n')
    #     app.logger.debug(scriptName+": > INFO: Next foodscraps collection date is -  "+str(foodscrapsDate)+'\n')
    
    # # RECYCLE INFO
    # recycleDate = recycleInfo.find("strong").get_text()
    # if debugmode :
    #     app.logger.debug(scriptName+": > INFO: Recycle Collection info: "+str(recycleInfo)+'\n')
    #     app.logger.debug(scriptName+": > INFO: Next recycle collection date is "+str(recycleDate)+'\n')
    
    # # ADDRESS INFO
    # if debugmode :
    #     app.logger.debug(scriptName+": > INFO: Address is "+str(addressBlock[0].string)+'\n')


    rubbishDate, recycleDate = None, None

    collection_cards = soup.find_all("div", class_="acpl-schedule-card")
    collection_info = []
    for card in collection_cards:
        bin_entries = card.find_all("p", class_="mb-0 lead")
        for entry in bin_entries:
            collection_info.append(entry)

    # Parse each collection entry and assign to the correct type based on keywords
    for entry in collection_info:
        text = entry.get_text(strip=True)
        if "rubbish" in text.lower():
            rubbishDate = text.split(":", 1)[-1].strip() if ":" in text else text
            # raw_date = text.split(":", 1)[-1].strip() if ":" in text else text
            # rubbish = self.parse_collection_date(raw_date)
        elif "recycling" in text.lower():
            recycleDate = text.split(":", 1)[-1].strip() if ":" in text else text
            # raw_date = text.split(":", 1)[-1].strip() if ":" in text else text
            # recycling = self.parse_collection_date(raw_date)
        # elif "food scraps" in text.lower():
            # raw_date = text.split(":", 1)[-1].strip() if ":" in text else text
            # food_scraps = self.parse_collection_date(raw_date)

    # Determine next collection type
    try:
        if rubbishDate and recycleDate:
            if rubbishDate == recycleDate:
                next_collection_type = "Rubbish & Recycling"
            else:
                next_collection_type = "Rubbish"
        elif rubbishDate:
                next_collection_type = "Rubbish"
        else:
            next_collection_type = None
    except Exception:
        next_collection_type = None

    output = {}
    output['address'] = addressBlock
    output['data_retrieved_datetime'] = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")

    if rubbishDate:
        output['rubbish_date'] = rubbishDate
        output['rubbish_datetime'] = datetime.strptime(rubbishDate.replace(',', '')+datetime.now().astimezone().strftime(' 07 %Y %z'), '%A %d %B %H %Y %z').strftime('%Y-%m-%dT%H:%M:%S%z')
    
    if recycleDate:
        output['recycle_date'] = recycleDate
        output['recycle_datetime'] = datetime.strptime(recycleDate.replace(',', '')+datetime.now().astimezone().strftime(' 07 %Y %z'), '%A %d %B %H %Y %z').strftime('%Y-%m-%dT%H:%M:%S%z')

    # Keep legacy fields for backwards compatibility
    activeDateStr = recycleDate if rubbishDate == recycleDate else rubbishDate
    output['datetime'] = datetime.strptime(activeDateStr.replace(',', '')+datetime.now().astimezone().strftime(' 07 %Y %z'), '%A %d %B %H %Y %z').strftime('%Y-%m-%dT%H:%M:%S%z')
    output['value'] = activeDateStr
    if rubbishDate == recycleDate:
        output['collection_type'] = 'Recycle'
        output['icon'] = 'mdi:recycle'
    else:
        output['collection_type'] = 'Rubbish'
        output['icon'] = 'mdi:trash-can'

    app.logger.debug(scriptName+': Rubbish collection information successfully fetched\n')
    return json.dumps(output)
