import hypixel
import time
import clipboard
import CONSTANTS
import pickle
import nbt
import base64
import io
from nbt import NBTFile, TAG_Long, TAG_Int, TAG_String, TAG_List, TAG_Compound

API_KEYS = ['8092b8cd-80e7-46a0-93dc-a3ac754f7c48']
hypixel.setKeys(API_KEYS)

BAD_ITEM_REFORGES = CONSTANTS.TOOL_REFORGES
ITEM_ITEM_REFORGES = CONSTANTS.TOOL_ITEM_REFORGES
NORMAL_ENCHANTS = CONSTANTS.NORMAL_ENCHANTS
SPECIAL_ENCHANTS = CONSTANTS.SPECIAL_ENCHANTS

filename = 'auctiondata'
pastAuctionsFILE = []
try:
    pastAuctionsFILE = pickle.load(open(filename, "rb"))
except (OSError, IOError) as e:
    print("Error, couldn't load auction data")

class Auction:
    def __init__(self):
        pass   
    def getLiveAuctions(self, PageNumber):
        return hypixel.getJSON("skyblock/auctions", page = str(PageNumber))
    def getPastAuctions(self, PageNumber):
        return hypixel.getJSON("skyblock/auctions_ended", page = str(PageNumber))

def checkID(listIn, ID):
    for x in listIn:
        if ID in x.values():
            return True
    return False

def checkEnchant(enchant, enchTier):
    if enchant in NORMAL_ENCHANTS:
        if len(NORMAL_ENCHANTS[enchant]) > 1:
            for y in NORMAL_ENCHANTS[enchant]:
                if enchTier == y:
                    return True
        else:
            if enchTier == NORMAL_ENCHANTS[enchant][0]:
                return True
    if enchant in SPECIAL_ENCHANTS:
        return True
    return False

liveAuctionListing = Auction()
pages = liveAuctionListing.getLiveAuctions(1)["totalPages"]

minmargin = 1.2
minprice = 1000000
pastAuctionsUnorganized = []
pastAuctions = []
pastAuctionsReforges = []
pastAuctionsEnchants = []
auctions = []
flipList = []
checkedAuctions = []

def unpack_nbt(tag):
    if isinstance(tag, TAG_List):
        return [unpack_nbt(i) for i in tag.tags]
    elif isinstance(tag, TAG_Compound):
        return dict((i.name, unpack_nbt(i)) for i in tag.tags)
    else:
        return tag.value

def decode_inventory_data(raw):
    data = nbt.nbt.NBTFile(fileobj = io.BytesIO(base64.b64decode(raw)))
    unpackNBT = unpack_nbt(data.tags[0])
    itemDict = dict(unpackNBT[0])
    return itemDict

def flip(auctions):
    for i in auctions:
        if i['uuid'] in checkedAuctions:
            continue
        price = i['price']
        if price < minprice:
            continue
        name = i['item_name']
        if name == 'PET':
            continue
        avgprice = 0.0
        avgpriceconst = 0.0
        margin = 0.0
        profit = 0
        uuid = i['uuid']
        reforge = i['reforge'].lower()
        reforgePrice = 0.0
        reforgeItem = ''
        potatobooks = i['potatoes']
        recombobulated = i['recomb']
        enchants = i['enchants']
        pricedenchants = []
        checkedAuctions.append(uuid)
        #get average price for item
        for x in pastAuctions:
            if x['name'] == name:
                volume = x['count']
                avgprice = x['average']
                avgpriceconst = x['average']
                break
        if avgprice <= 0:
            continue
        #gather enchant price
        if len(enchants) > 0:
            for x in enchants:
                enchant = x
                enchTier = enchants[x]
                if checkEnchant(enchant, enchTier):
                    for y in pastAuctionsEnchants:
                        if y['name'] == enchant + ' ' + str(enchTier):
                            pricedenchants.append(y['name'])
                            avgprice += y['average']

        #gather reforge price
        if reforge != '' and reforge in ITEM_ITEM_REFORGES:
            for x in ITEM_ITEM_REFORGES:
                if reforge == x:
                    reforgeItem = ITEM_ITEM_REFORGES[x]
                    for y in pastAuctionsReforges:
                        if y['name'] == reforgeItem:
                            reforgePrice = y['average']
                            avgprice += y['average']

        #potatobook value
        if potatobooks > 10:
            avgprice += (((potatobooks - 10) * 500000) + 0)
        else:
            avgprice += (potatobooks * 0)

        #recombvalue
        if recombobulated:
            avgprice += 5000000

        if (avgprice / avgpriceconst) > 1.8:
            continue
        margin = avgprice / price
        profit = avgprice - price
        if (margin >= minmargin) or (profit >= minprice * 10):
            if (uuid not in flipList) and (volume > 20):
                flipList.append(uuid)
                print("\nItem name: " + str(name) +
                    "\nItem reforge: " + str(reforge) +
                    "\nEstimated reforge price: " + f'{int(reforgePrice):,}' +
                    "\nItem price: " + f'{int(price):,}' +
                    "\nAverage clean item price: " + f'{int(avgpriceconst):,}' +
                    "\nEstimated value: " + f'{int(avgprice):,}' +
                    "\nEstimated profit: " + f'{int(profit):,}' +
                    "\nPotato books: " + str(potatobooks) +
                    "\nRecomb status: " + str(recombobulated) +
                    "\nAuction volume: " + str(volume) +
                    "\nAUCTION COMMAND\n/viewauction " + str(uuid))
                print("\nPriced enchants: ")
                print(pricedenchants)
                clipboard.copy("/viewauction " + str(uuid))












#process pastAuctionsFile to be easily accessible using data that matters for comparisons
print("Creating past auction list, this may take a while...")
start_time_auction = time.time()
for x in pastAuctionsFILE:
    enchants = {}
    valuableEnch = False
    itemid = x['item_data']['id']
    price = x['price']
    matchFound = False
    #filters entries that have enchants and arent enchanted books
    if 'enchantments' in x['item_data'] and itemid != 'ENCHANTED_BOOK':
        continue
    #filters enchanted books that have more than one enchant
    if itemid == 'ENCHANTED_BOOK' and len(x['item_data']['enchantments']) > 1:
        continue
    #if itemid is enchanted book and it survived above filter it must have 1 enchant, if that enchant is not valuable then continue
    elif itemid == 'ENCHANTED_BOOK':
        enchants = x['item_data']['enchantments']
        enchant = list(enchants.keys())[0]
        enchTier = enchants[enchant]
        if checkEnchant(enchant, enchTier):
            for y in pastAuctionsUnorganized:
                if y['name'] == enchant + ' ' + str(enchTier):
                    y['count'] += 1
                    y['average'].append(price)
                    matchFound = True
            if not matchFound:
                pastAuctionsUnorganized.append({'name': enchant + ' ' + str(enchTier), 'count': 1, 'average': [price], 'hasEnchants': True, 'enchants': enchants})
        else:
            continue
    #if pastAuctions not empty
    for y in pastAuctionsUnorganized:
        #for each element in pastAuctions, if there if a matching name
        if y['name'] == itemid:
            y['count'] += 1
            y['average'].append(price)
            matchFound = True
    #if id not found in auction list, or enchant not found in auction list
    if not matchFound:
        pastAuctionsUnorganized.append({'name': itemid, 'count': 1, 'average': [price], 'hasEnchants': False, 'enchants': {}})



print("Auction list created.")
print("--- %s seconds ---" % (time.time() - start_time_auction))

print("Organizing past auction list, this may take a while...")
start_time_org = time.time()
for x in pastAuctionsUnorganized:
    x['average'].sort()
    if x['count'] < 30:
        x['average'] = sum(x['average'][:x['count']]) / x['count']
    else:
        x['average'] = sum(x['average'][:30]) / 30

    if x['name'] in list(ITEM_ITEM_REFORGES.values()):
        pastAuctionsReforges.append(x)
    if x['hasEnchants']:
        pastAuctionsEnchants.append(x)
    elif x['average'] > 0:
        pastAuctions.append(x)
print("Auction list organized.")
print("--- %s seconds ---" % (time.time() - start_time_org))

pastAuctionsReforges = sorted(pastAuctionsReforges, key = lambda i: i['name'])
pastAuctionsEnchants = sorted(pastAuctionsEnchants, key = lambda i: i['name'])

print("~\n~~~\n~~~~~\nReforge prices:\n~~~~~\n~~~\n~")
for x in pastAuctionsReforges:
    print(x)
print("~\n~~~\n~~~~~\nEnchant prices:\n~~~~~\n~~~\n~")
for x in pastAuctionsEnchants:
    print(x)
print("~\n~~~\n~~~~~\nAuction prices:\n~~~~~\n~~~\n~")
for x in pastAuctions:
    print(x)













print("Creating live auction list, this may take a while...")
start_time_live = time.time()
for x in range(1, pages):
    print("Gathering page " + str(x) + "/" + str(pages))
    try:
        for y in liveAuctionListing.getLiveAuctions(x)["auctions"]: 
            modifier = ''
            gemstones = ''
            stars = 0
            potatobooks = 0
            enchants = {}
            recombobulated = False
            if y['bin'] == True:
                item_data = decode_inventory_data(y['item_bytes'])
                item_data = item_data['tag']['ExtraAttributes']
                itemid = item_data['id']
                if 'FINAL_DESTINATION' in itemid or 'ASPECT_OF' in itemid or 'DUNGEON_STONE' in itemid or 'CAKE' in itemid or 'STARRED' in itemid:
                    continue
                if 'dungeon_item_level' in item_data:
                    stars = item_data['dungeon_item_level']

                if 'modifier' in item_data:
                    modifier = item_data['modifier']

                if 'gems' in item_data:
                    gemstones = item_data['gems']

                if 'hot_potato_count' in item_data:
                    potatobooks = item_data['hot_potato_count']
                
                if 'enchantments' in item_data:
                    enchants = item_data['enchantments']

                if 'rarity_upgrades' in item_data:
                    recombobulated = True
                auctions.append({'item_name': itemid, 'uuid': y['uuid'], 'type': y['category'], 'price': y['starting_bid'], 'stars': stars, 'reforge': modifier, 'gems': gemstones, 'potatoes': potatobooks, 'enchants': enchants, 'recomb': recombobulated})
    except:
        print('Page load failed, error caught')
print("--- %s seconds ---" % (time.time() - start_time_live))

flip(auctions)









while True:
    auctions = []
    liveauctions = liveAuctionListing.getLiveAuctions(1)["auctions"]
    liveauctions.reverse()
    for y in liveauctions: 
        modifier = ''
        gemstones = ''
        stars = 0
        potatobooks = 0
        enchants = {}
        recombobulated = False
        if y['bin'] == True:
            item_data = decode_inventory_data(y['item_bytes'])
            item_data = item_data['tag']['ExtraAttributes']
            itemid = item_data['id']
            if 'FINAL_DESTINATION' in itemid or 'ASPECT_OF' in itemid or 'DUNGEON_STONE' in itemid or 'CAKE' in itemid or 'STARRED' in itemid:
                continue
            if 'dungeon_item_level' in item_data:
                stars = item_data['dungeon_item_level']

            if 'modifier' in item_data:
                modifier = item_data['modifier']

            if 'gems' in item_data:
                gemstones = item_data['gems']

            if 'hot_potato_count' in item_data:
                potatobooks = item_data['hot_potato_count']
                
            if 'enchantments' in item_data:
                enchants = item_data['enchantments']

            if 'rarity_upgrades' in item_data:
                recombobulated = True
            auctions.append({'item_name': itemid, 'uuid': y['uuid'], 'type': y['category'], 'price': y['starting_bid'], 'stars': stars, 'reforge': modifier, 'gems': gemstones, 'potatoes': potatobooks, 'enchants': enchants, 'recomb': recombobulated})
    flip(auctions)

"""
current auction element
dictionary defined as 'id' = str
{
'stars' = int               'item_data' > 'dungeon_item_level'
'modifier' = str            'item_data' > 'modifier'
'gemstones' = dict          'item_data' > 'gems'
'price' = int               'price'
'potatobooks' = int         'item_data' > 'hot_potato_count'
'enchants' = dict           'item_data' > 'enchantments'
'recombobulated' = bool     'item_data' > 'rarity_upgrades'
}

past auction element
dictionary defined
{
'name' = str                item name
'count' = int               running count of item
'average' = list            total of all prices
'hasEnchants' = bool        only books can have this as true, used to easily sort unorganized ah list into sections
'enchants' = dict           this will never have more than one, since it is only used for books
}
"""