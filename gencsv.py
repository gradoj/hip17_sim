import requests
import json
import csv
import sys
from datetime import datetime, timedelta
import h3
import time

headers = {
    'User-Agent': 'INSERT_VALID_HEADER_HERE',
    'From': 'your@email.com'  # This is another valid field
}

def get_total(addr,days):
    now = datetime.now()# - timedelta(days=7)
    yesterday = now - timedelta(days=days)
    #print(my_date.isoformat())
    nowstr=str(now.isoformat())
    yesterdaystr=str(yesterday.isoformat())
    url = "https://api.helium.io/v1/hotspots/" +str(addr)+ "/rewards/sum" + "?min_time="+yesterdaystr+"&max_time="+nowstr
    #print(url)
    data=requests.get(url=url, headers=headers)
    data=data.json()
    data=data['data']
    total=data['sum']
    try:
        #print(total)
        return str(float(total)/1E8)
    except:
        #print(total)
        return str(0)
    #print(url)
    #print(data)


def download_hotspots(getDateAdded=False,getEarnings=False,days=7):
    url = "https://api.helium.io/v1/hotspots"
    data=requests.get(url=url, headers=headers)
    data=data.json()
    cursor = data['cursor']
    data = data['data']
    jsondata=data

    hs_count=0
    print('Getting hotspots from api')
    while(cursor):
        hs_count+=1000
        print(hs_count)
        data=requests.get(url=url+'?cursor='+cursor, headers=headers)
        data=data.json()
        try:
            cursor = data['cursor']
        except:
            cursor=None
        data = data['data']
        jsondata=jsondata+data
        #print(len(jsondata))
        #print(cursor)

    filename="hotspots.csv"#+str(days)+'days_'+str(int(time.time()))+".csv"
    fout=open(filename,"w+")

    fout.write('Name, Latitude, Longitude, Altitude, Address, Earnings, Country, Location, Online, BlockAdded, DateAdded, Scaling, Height, last_poc_challenge, hex4, hex5, hex6, hex7, hex8, hex9, hex10, hex11, hex12\n')
    count=0
    noloccount=0
    print('Processing hotspot data')
    for hotspot in jsondata:
        try:
            #print(hotspot['name'], hotspot['lat'], hotspot['lng'])
            #print(hotspot)
            if count%1000 == 0:
                print(count)
            addr=str(hotspot['address'])

            #need to add scaling factor to csv

            block_added=str(hotspot['block_added'])
            date_added=''
            if getDateAdded:
                
                date_added=requests.get(url='https://api.helium.io/v1/blocks/'+block_added).json()['data']['time']
                date_added=datetime.fromtimestamp(date_added)
                date_added=date_added.strftime('%Y-%m-%d %H:%M:%S')


            location = str(hotspot['location'])
            country = str(hotspot['geocode']['short_country'])
            elevation=str(hotspot['elevation'])
            online=str(hotspot['status']['online'])
            total=str(0)
            if getEarnings:
                total=get_total(addr,days)
            
            if hotspot['reward_scale'] == None:
                scaling=str(0)
            else:
                scaling=str(hotspot['reward_scale'])


            if hotspot['status']['height'] == None:
                height=str(0)
            else:
                height=str(hotspot['status']['height'])

            if hotspot['last_poc_challenge'] == None:
                last_poc_challenge=str(0)
            else:
                last_poc_challenge=str(hotspot['last_poc_challenge'])
                
            home_hex={}
            for i in range(4,13,1):
                home_hex[i]=str(h3.geo_to_h3(hotspot['lat'],hotspot['lng'],i))
            a=str(hotspot['name']) +','+ str(hotspot['lat']) +','+ str(hotspot['lng'])+','+elevation+','  + addr+ \
                ','+total+','+country+','+location+','+online+','+block_added+','+date_added+','+scaling+','+height+','+last_poc_challenge+','+ \
                home_hex[4]+','+home_hex[5]+','+home_hex[6]+','+home_hex[7]+','+home_hex[8]+','+home_hex[9]+','+home_hex[10]+','+home_hex[11]+','+home_hex[12]+'\n'
            fout.write(a)
            count=count+1
        except KeyError:
            noloccount=noloccount+1
            #print(hotspot)
            #pass
        except Exception as e:
            print(e.__class__, "Exception occurred.")
            print(e)
            #print(hotspot)
            #pass
    
    print('Number of Hotspots with lat,lon: ',count)
    print('Number of Hotspots without lat,lon: ',noloccount)

    fout.close()

if __name__ == '__main__':
    download_hotspots(getDateAdded=False,getEarnings=False,days=7)
