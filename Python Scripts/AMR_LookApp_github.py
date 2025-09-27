ver = "v.2.025.06 [GitHub]"
# Python 3.12 & Pandas 2.2 ready
# New TG group
# comment will mark the specific code for GitHub
# GitHub version will always run complete list of artists

import requests
import os
import pandas as pd
import csv
import time
import json
import datetime
import numpy as np

# Инициализация переменных================================================

userDataFolder = '' # root is root
dbFolder = 'Databases/'
releasesDB = userDataFolder + dbFolder + 'AMR_releases_DB.csv'
artistIDDB = userDataFolder + dbFolder + 'AMR_artisitIDs.csv'
field_names = ['dateUpdate', 'downloadedRelease', 'mainArtist', 'artistName', 'collectionName', 
               'trackCount', 'releaseDate', 'releaseYear', 'mainId', 'artistId', 'collectionId', 
               'country', 'artworkUrlD', 'downloadedCover', 'updReason']
#---------------------v  отрезал JP
lCountry = ['nz', 'us', 'ru'] # 新西兰优先，然后美国和俄罗斯
emojis = {'us': '\U0001F1FA\U0001F1F8', 'ru': '\U0001F1F7\U0001F1FA', 'jp': '\U0001F1EF\U0001F1F5', 'nz': '\U0001F1F3\U0001F1FF', 'no': '\U0001F3F3\U0000FE0F', 'wtf': '\U0001F914', 
          'album': '\U0001F4BF', 'cover': '\U0001F3DE\U0000FE0F', 'error': '\U00002757\U0000FE0F', 'empty': '\U0001F6AB', 'badid': '\U0000274C'}
logFile = userDataFolder + 'status.log' # path to log file
# Telegram disabled - core functionality only
#-----------------------------------------

# establishing session
ses = requests.Session() 
ses.headers.update({'Referer': 'https://itunes.apple.com', 
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'})

# Инициализация функций===================================================

# This logger is only for GitHub --------------------------------------------------------------------
def amnr_logger(pyScript, logLine):
    with open(logFile, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        # GitHub server time is UTC (-3 from Moscow), so i add +3 hours to log actions in Moscow time. Only where time matters
        f.write(str(datetime.datetime.now() + datetime.timedelta(hours=3)) + ' - ' + pyScript + ' - ' + logLine.rstrip('\r\n') + '\n' + content)
#----------------------------------------------------------------------------------------------------

# Процедура Замены символов для Markdown v2
def ReplaceSymbols(rsTxt):
    rsTmplt = """'_*[]",()~`>#+-=|{}.!"""
    for rsf in range(len(rsTmplt)):
        rsTxt = rsTxt.replace(rsTmplt[rsf], '\\' + rsTmplt[rsf])
    return rsTxt

# Telegram functionality disabled

# Процедура Загрузки библиотеки
def CreateDB():
    if not os.path.exists(releasesDB):
        with open(releasesDB, 'a+', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, delimiter=';', fieldnames=field_names)
            writer.writeheader()

# Процедура Поиска релизов исполнителя в базе iTunes  
def FindReleases(artistID, cRow, artistPrintName):
    allDataFrame = pd.DataFrame()
    dfExport = pd.DataFrame()
    for country in lCountry:
        url = 'https://itunes.apple.com/lookup?id=' + str(artistID) + '&country=' + country + '&entity=album&limit=200'
        try:
            request = ses.get(url, timeout=30)
        except Exception as e:
            amnr_logger('[Apple Music Releases LookApp]', artistPrintName + ' - ' + str(artistID) + ' - ' + country + ' - CONNECTION ERROR: ' + str(e))
            continue
        if request.status_code == 200:     
            dJSON = json.loads(request.text)
            if dJSON['resultCount'] > 1:
                dfTemp = pd.DataFrame(dJSON['results'])
                allDataFrame = pd.concat([allDataFrame, dfTemp[['artistName', 'artistId', 'collectionId', 'collectionName', 'artworkUrl100', 'trackCount', 'country', 'releaseDate']]], ignore_index=True)
            else:
                amnr_logger('[Apple Music Releases LookApp]', artistPrintName + ' - ' + str(artistID) + ' - ' + country + ' - EMPTY')
        else:
            amnr_logger('[Apple Music Releases LookApp]', artistPrintName + ' - ' + str(artistID) + ' - ' + country + ' - ERROR (' + str(request.status_code) + ')')
        time.sleep(1) # обход блокировки
    allDataFrame.drop_duplicates(subset='artworkUrl100', keep='first', inplace=True, ignore_index=True)
    if len(allDataFrame) > 0:
        dfExport = allDataFrame.loc[allDataFrame['collectionName'].notna()]
    else:
        amnr_logger('[Apple Music Releases LookApp]', artistPrintName + ' - ' + str(artistID) + ' - Bad ID')

    if len(dfExport) > 0:
        pdiTunesDB = pd.read_csv(releasesDB, sep=";")
        #Открываем файл лога для проверки скаченных файлов и записи новых скачиваний
        csvfile = open(releasesDB, 'a+', newline='')
        writer = csv.DictWriter(csvfile, delimiter=';', fieldnames=field_names)

        dateUpdate = str(datetime.datetime.now() + datetime.timedelta(hours=3))[0:19] # GitHub server time is UTC (-3 from Moscow), so i add +3 hours to log actions in Moscow time. Only where time matters
        # mainArtist = allDataFrame['artistName'].loc[0]
        mainArtist = artistPrintName
        mainId = artistID
        updReason = ''
        newRelCounter = 0
        newCovCounter = 0
        #Cкачиваем обложки
        for index, row in dfExport.iterrows():
            artistName = row.iloc[0]
            artistId = row.iloc[1]
            collectionId = row.iloc[2]
            collectionName = row.iloc[3]
            artworkUrl100 = row.iloc[4]
            trackCount = row.iloc[5]
            country = row.iloc[6]
            releaseDate = row.iloc[7][:10]
            releaseYear = row.iloc[7][:4]
            artworkUrlD = row.iloc[4].replace('100x100bb', '100000x100000-999')
            downloadedCover = ''
            downloadedRelease = ''
            updReason = ''
            if len(pdiTunesDB.loc[pdiTunesDB['collectionId']  == dfExport.iloc[index - 1]['collectionId']])  == 0:
                updReason = 'New release'
                newRelCounter += 1
            elif len(pdiTunesDB[pdiTunesDB['artworkUrlD'].str[40:] == dfExport.iloc[index-1]['artworkUrl100'].replace('100x100bb', '100000x100000-999')[40:]]) == 0:
                updReason = 'New cover'
                newCovCounter += 1
                #.str[40] -------------------------------V
                #https://is2-ssl.mzstatic.com/image/thumb/Music/v4/b2/cc/64/b2cc645c-9f18-db02-d0ab-69e296ea4d70/source/100000x100000-999.jpg

            #Это проверка - нужно ли сверяться с логом
            if updReason != '':
                writer.writerow({
                    'dateUpdate': dateUpdate[:10], 'downloadedRelease': downloadedRelease, 
                    'mainArtist': mainArtist,
                    'artistName': artistName, 'collectionName': collectionName, 
                    'trackCount': trackCount, 'releaseDate': releaseDate, 
                    'releaseYear': releaseYear, 'mainId': mainId, 'artistId': artistId, 
                    'collectionId': collectionId, 'country': country, 'artworkUrlD': artworkUrlD, 
                    'downloadedCover': downloadedCover, 'updReason': updReason
                    })
                
        csvfile.close()

        artistIDlist.iloc[cRow, 2] = str(dateUpdate)
        artistIDlist.to_csv(artistIDDB, sep=';', index=False)

        pdiTunesDB = pd.DataFrame() 
        if (newRelCounter + newCovCounter) > 0:
            amnr_logger('[Apple Music Releases LookApp]', 
                        artistPrintName + ' - ' + str(artistID) + ' - ' + str(newRelCounter + newCovCounter) + ' new records: ' + str(newRelCounter) + ' releases, ' + str(newCovCounter) + ' covers')
    
    else:
        artistIDlist.iloc[cRow, 2] = str(datetime.datetime.now() + datetime.timedelta(hours=3))[0:19] # GitHub server time is UTC (-3 from Moscow), so i add +3 hours to log actions in Moscow time. Only where time matters
        artistIDlist.to_csv(artistIDDB, sep=';', index=False)
# Инициализация функций===================================================

amnr_logger('[Apple Music Releases LookApp]', ver + " (c)&(p) 2022-" + str(datetime.datetime.now())[0:4] + " by Viktor 'MushroomOFF' Gribov")

CreateDB()

pd.set_option('display.max_rows', None)

artistIDlist = pd.read_csv(artistIDDB, sep=';')
artistIDlist.drop('downloaded', axis=1, inplace=True)
artistIDlist.insert(2, "downloaded", "")  # Use empty string instead of nan
artistIDlist.to_csv(artistIDDB, sep=';', index=False)

returner = ''
processed_count = 0
max_artists = 50  # 限制处理的艺术家数量，避免在GitHub Actions中运行太久
start_time = datetime.datetime.now()
max_runtime = 900  # 最大运行时间15分钟

while returner == '' and processed_count < max_artists:
    artID = artistIDlist['mainId'].loc[artistIDlist['downloaded'] == ""].head(1)
    if len(artID) == 0:
        returner = 'x'
        print(f"All artists processed!")
    else:
        curRow = artID.index[0]
        artID.reset_index(drop=True, inplace=True)
        curArt = artID[0]

        printArtID = artistIDlist['mainArtist'].loc[artistIDlist['downloaded'] == ""].head(1)
        printArtID.reset_index(drop=True, inplace=True)
        printArtist = printArtID[0]
        print(f'{processed_count + 1}/{max_artists}: {(printArtist + " - " + str(curArt)):40}', end='\r')

        FindReleases(curArt, curRow, printArtist)
        processed_count += 1

        # 检查运行时间，防止GitHub Actions超时
        current_time = datetime.datetime.now()
        if (current_time - start_time).seconds > max_runtime:
            print(f"Timeout reached after {processed_count} artists. Stopping to avoid GitHub Actions timeout.")
            returner = 'timeout'
            break

        time.sleep(1.5) # 避免被API限制

if processed_count >= max_artists:
    print(f"Processed {max_artists} artists. Remaining will be processed in next run.")

pd.set_option('display.max_rows', 10)
print(f'{'':50}')

amnr_logger('[Apple Music Releases LookApp]', '[V] Done!')
