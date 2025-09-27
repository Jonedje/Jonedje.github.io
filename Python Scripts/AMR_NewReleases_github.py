ver = "v.2.025.09 [GitHub]"
# Python 3.12 & Pandas 2.2 ready
# NEW: Zvuk & Yandex.Music search engine
# comment will mark the specific code for GitHub

import os
import json
import datetime
import requests
import pandas as pd
import csv
import sys # for Zvuk
# External services disabled - Only Apple Music core functionality

rootFolder = '' # root is root
amrsFolder = rootFolder + 'AMRs/'
dbFolder = rootFolder + 'Databases/'
newReleasesDB = dbFolder + 'AMR_newReleases_DB.csv'
csReleasesDB = dbFolder + 'AMR_csReleases_DB.csv'
artistIDsDB = dbFolder + 'AMR_artisitIDs.csv'
ReleasesDB = dbFolder + 'AMR_releases_DB.csv'
logFile = rootFolder + 'status.log' # path to log file
# All external services disabled - Apple Music only
# Establishing session -------------------
s = requests.Session() 
s.headers.update({'Referer':'https://music.apple.com', 'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'})
#-----------------------------------------

# This logger is only for GitHub --------------------------------------------------------------------
def amnr_logger(pyScript, logLine):
    with open(logFile, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        # GitHub server time is UTC (-3 from Moscow), so i add +3 hours to log actions in Moscow time. Only where time matters
        f.write(str(datetime.datetime.now() + datetime.timedelta(hours=3)) + ' - ' + pyScript + ' - ' + logLine.rstrip('\r\n') + '\n' + content)
#----------------------------------------------------------------------------------------------------

# All external music services disabled - Apple Music only
#-----------------------------------------

# No external services - only core functionality

# Процедура поиска актуальной ссылки на раздел (с защитой от ошибок)
def find_link(catLink, catName):
    try:
        request = s.get(catLink, timeout=30)
        request.encoding = 'UTF-8'
        res = request.text
        strt = res.find('{"title":"' + catName + '"')
        if strt == -1:
            print(f"Could not find section '{catName}' in Apple Music page")
            return catLink  # Return original link as fallback
        pos_id_0 = res.find('"id":"', strt) + len('"id":"')
        pos_id_1 = res.find('"', pos_id_0)
        catID = res[pos_id_0:pos_id_1].strip()
        roomLink = catLink[:catLink.find('/curator')] + '/room/' + str(catID)
        return roomLink
    except Exception as e:
        print(f"Error finding Apple Music link: {e}")
        return catLink  # Return original link as fallback

def collect_albums(caLink, caText, caGrad):
    global message2send
    try:
        request = s.get(caLink, timeout=30)
        request.encoding = 'UTF-8'
    except Exception as e:
        print(f"Error accessing Apple Music page: {e}")
        return  # Skip this category if failed

    if caText == 'ANIME':
        dldCategory = 'A'
    elif caText == 'METAL':
        dldCategory = 'M'
    elif caText == 'HARD ROCK':
        dldCategory = 'HR'
    elif caText == 'METAL - RU':
        dldCategory = 'MRU'
    elif caText == 'HARD ROCK - RU':
        dldCategory = 'HRRU'
    
    dldDate = str(datetime.datetime.now())[0:10]
    htmlHead = """<head>
  <meta charset="utf-8">
  <title>Apple Music Releases</title>
  <link rel="stylesheet" type="text/css" href="../Resources/styles.css" />
  <SCRIPT language=JavaScript type=text/JavaScript>
    <!--
    function show(id) {
      if(document.getElementById("show" + id).style.display == 'none') {
        document.getElementById("show" + id).style.display = '';
      }else{
        document.getElementById("show" + id).style.display = 'none';
      }
    }

    function show_tr(id) {
      var elms;
      if (id=="v") {
        elms = document.querySelectorAll("[id='v']");
      } else if (id=="x") {
        elms = document.querySelectorAll("[id='x']");
      } else if (id=="d") {
        elms = document.querySelectorAll("[id='d']");
      } else if (id=="o") {
        elms = document.querySelectorAll("[id='o']");
      } else if (id=="") {
        elms = document.querySelectorAll("[id='']");
      }
      for (var i = 0; i < elms.length; i++) {
        if (elms[i].style.display == 'none') {
          elms[i].style.display = '';
        } else {
          elms[i].style.display = 'none';
        }
      }
    }
    //-->
  </SCRIPT>
</head>

<body>
  <input id="bV" type="button" value="V" onclick="show_tr('v');" class="bV" />
  <input id="bD" type="button" value="D" onclick="show_tr('d');" class="bD" />
  <input id="bX" type="button" value="O" onclick="show_tr('o');" class="bO" />
  <input id="bX" type="button" value="X" onclick="show_tr('x');" class="bX" />
  <input id="bE" type="button" value="  " onclick="show_tr('');" class="bE" />
  <input type="button" onclick="location.href='../index.html';" value="Index"  class="bI"/>
  <hr>
"""

    htmlStart = """  <table border="1">
    <tr id=""" + ('\"' + dldDate + '_' + caText + '\"').lower().replace(' ','_') +  """><th colspan="2" style="background: linear-gradient(to right, """ + caGrad + """);">""" + dldDate + """ | """ + caText + """</th></tr>
    <tr><th width="100px">Cover</th><th width="600px">Album</th></tr>
"""

    htmlText = ''

    htmlEnd = """  </table>
  <hr>
"""

    htmlFinal = """  <!-- End of File -->
  <script id="rendered-js" >
    [...document.querySelectorAll('[data-frame-load]')].forEach(button => {
      button.addEventListener('click', () => {
        const group = button.getAttribute('data-frame-load');
        [...document.querySelectorAll(`[data-frame-group="${group}"]`)].forEach(frame => {
          javascript:show(frame.getAttribute('data-frame-group') + '_');
          frame.setAttribute('src', frame.getAttribute('data-frame-src'));
        });
      });
    });
  </script>
</body>
"""

    fieldNames = ['date', 'category', 'artist', 'album', 'Best_Fav_New_OK', 'rec_send2TG', 'link', 'link_ym', 'link_zv', 'imga', 'send2TG', 'TGmsgID']
    pdDB = pd.read_csv(newReleasesDB, sep=";")
    pdAIDDB = pd.read_csv(artistIDsDB, sep=";")
    csvfile = open(newReleasesDB, 'a+', newline='')
    writer = csv.DictWriter(csvfile, delimiter=';', fieldnames=fieldNames)

    res = request.text
    i = res.find('<div class="content-container ')
    pos = res.find('<footer ')

    fullCard0 = '<li class="grid-item '
    fullCard1 = '</li>'
    while i < pos:
        if res.find(fullCard0, i) > -1:
            posCard0 = res.find(fullCard0, i) + len(fullCard0)
            posCard1 = res.find(fullCard1, posCard0) 
            i = posCard0
            while i < posCard1:
                sstr = '<picture '
                if res[i:i + len(sstr)] == sstr:
                    posPic0 = res.find('srcset="', i) + len('srcset="')
                    posPic1 = res.find(' ', posPic0)
                    imga = res[posPic0:posPic1].strip()    
                    i = res.find('</picture>', i)
                sstr = '<div class="product-lockup__title-link '
                if res[i:i + len(sstr)] == sstr:
                    posLink0 = res.find('<a href="', i) + len('<a href="')
                    posLink1 = res.find('"', posLink0)
                    link = res[posLink0:posLink1].strip()    
                    i = posLink1
                    posAlbum0 = res.find('>', i) + len('>')
                    posAlbum1 = res.find('<', posAlbum0)
                    album = res[posAlbum0:posAlbum1].strip()
                    i = posAlbum1           
                    sstr = '<p data-testid="product-lockup-subtitles" '
                    i = res.find(sstr, i) + len(sstr)
                    pEnd = res.find('</p>', i) 
                    artist = ''
                    artistID = ''
                    isMyArtist = 0 # Check Artist ID
                    while i < pEnd:
                        posArtID1 = res.find('" class="product-lockup__subtitle link', i)
                        if posArtID1 < pEnd and posArtID1 > -1:
                            posArtID0 = res.rfind('/', i, posArtID1) + len('/')
                            artistID = res[posArtID0:posArtID1].strip()
                            if float(artistID) in pdAIDDB['mainId'].values:
                                isMyArtist += 1
                        posArtist0 = res.find('>', i) + len('>')
                        posArtist1 = res.find('<', posArtist0)
                        if res[posArtist0:posArtist1].strip() == ',':
                            artist += ';'
                        else:
                            artist += res[posArtist0:posArtist1].strip()
                        i = posArtist1
                        i += 1
                    artist = artist.replace('&amp;','_&_')
                    artist = artist.replace(';','; ')
                    artist = artist.replace('_&_', '&amp;')
                    check = 0
                    for index, row in pdDB.iterrows():
                        if row.iloc[6][row.iloc[6].rfind('/') + 1:] == link[link.rfind('/') + 1:]:
                            check = 1
                    if check == 0:
                        if artist != '':
                            aralname = artist + ' - ' + album
                            aralinsert = aralname.replace(artist, artist + '</b>') if len(aralname) < 80 else aralname[:aralname[:80].rfind(' ') + 1].replace(artist, artist + '</b>') + '<br>' + aralname[aralname[:80].rfind(' ') + 1:]

                            writer.writerow({'date': dldDate, 
                                             'category': dldCategory, 
                                             'artist': artist.replace('&amp;','&'), 
                                             'album': album.replace('&amp;','&'), 
                                             'Best_Fav_New_OK': '', 
                                             'rec_send2TG': '', 
                                             'link': link, 
                                             'link_ym': '', # External services disabled
                                             'link_zv': '', # External services disabled
                                             'imga': imga, 
                                             'send2TG': '', 
                                             'TGmsgID': ''})

                            htmlText += f"""  <!-- {artist.replace('&amp;','&')} - {album.replace('&amp;','&')} -->
    <tr style="display:;" id=''>
      <td><a href="{imga.replace('296x296bb.webp', '100000x100000-999.jpg').replace('296x296bf.webp', '100000x100000-999.jpg')}" target="_blank"><img src="{imga}" height="100px"></a></td>
      <td class="album_name"><a href="{link}" target="_blank"><b>{aralinsert}</a><br><br><button data-frame-load="{link[link.rfind('/') + 1:]}">Preview</button></td>
    </tr> 
    <tr style="display:none;" id="show{link[link.rfind('/') + 1:]}_"><td colspan="2"><iframe id="embedPlayer" data-frame-group="{link[link.rfind('/') + 1:]}" data-frame-src="{link.replace('://', '://embed.')}?app=music&amp;itsct=music_box_player&amp;itscg=30200&amp;ls=1&amp;theme=light" height="450px" frameborder="0" sandbox="allow-forms allow-popups allow-same-origin allow-scripts allow-top-navigation-by-user-activation" allow="autoplay *; encrypted-media *; clipboard-write" style="width: 100%; overflow: hidden; border-radius: 10px; transform: translateZ(0px); animation: 2s ease 0s 6 normal none running loading-indicator; background-color: rgb(228, 228, 228);"></iframe></td></tr>
"""
                    i += 1
                i += 1
        i += 1

    csvfile.close()

    yearNOW = dldDate[0:4]
    monthNOW = dldDate[0:7]
    monthTextNOW = datetime.datetime.strptime(dldDate, '%Y-%m-%d').strftime('%B')    
    HTMLFile = open(rootFolder + "index.html", "r")
    index = HTMLFile.read()
    monthDB = index[index.find('<a href="AMRs/AMR ') + len('<a href="AMRs/AMR '):index.find('.html">')]
    HTMLFile.close()
    monthTextDB = datetime.datetime.strptime(monthDB, '%Y-%m').strftime('%B')
    yearDB = monthDB[0:4]
    newMonth = 0
    newYear = 0

    if yearNOW != yearDB:
        newYear = 1
        with open(rootFolder + 'index.html', 'r+') as idx:
            idxContent = idx.read()
            idxContent = idxContent.replace('\n    <h2 class="title svelte-hprj71" data-testid="header-title">' + yearDB + ':</h2>',
                                            '\n    <h2 class="title svelte-hprj71" data-testid="header-title">' + yearNOW + ':</h2>\n        <a href="AMRs/AMR ' + monthNOW + '.html">' + monthTextNOW + '</a><br>\n    <h2 class="title svelte-hprj71" data-testid="header-title">' + yearDB + ':</h2>')
            idx.seek(0, 0)
            idx.write(idxContent)
        idx.close()
    else:
        if monthNOW != monthDB:
            newMonth = 1
            with open(rootFolder + 'index.html', 'r+') as idx:
                idxContent = idx.read()
                idxContent = idxContent.replace('\n        <a href="AMRs/AMR ' + monthDB + '.html">' + monthTextDB + '</a>',
                                                '\n        <a href="AMRs/AMR ' + monthNOW + '.html">' + monthTextNOW + '</a> | \n        <a href="AMRs/AMR ' + monthDB + '.html">' + monthTextDB + '</a>')
                idx.seek(0, 0)
                idx.write(idxContent)
            idx.close()

    if htmlText != '':
        if newMonth == 1 or newYear == 1:
            with open(amrsFolder + 'AMR ' + monthNOW + '.html', 'w') as h2r:
                h2r.write(htmlHead + '\n' + htmlStart + htmlText + htmlEnd + '\n' + htmlFinal)
            h2r.close()            
        else:
            with open(amrsFolder + 'AMR '+monthNOW + '.html', 'r+') as h2r:
                h2rContent = h2r.read()
                h2rContent = h2rContent.replace(htmlHead, '')
                h2r.seek(0, 0)
                h2r.write(htmlHead + '\n' + htmlStart + htmlText + htmlEnd + '\n' + h2rContent)
            h2r.close()
#----------------------------------------------------------------------------------------------------

def coming_soon(caLink):
    global messageCS
    try:
        CS_request = s.get(caLink, timeout=30)
        CS_request.encoding = 'UTF-8'
        CS_res = CS_request.text
    except Exception as e:
        print(f"Error accessing Apple Music Coming Soon page: {e}")
        return  # Skip coming soon if failed

    ul_r = CS_res.find('<ul class="grid')
    ul_p = CS_res.find('</ul>', ul_r)
    ul_string = CS_res[ul_r:ul_p + len('</ul>')]

    product_lockup_aria_label = ''
    artwork_component_artwork_bg_color = ''
    artwork_component_artwork_placeholder_bg_color = ''
    picture_srcset_webp = ''
    picture_srcset_jpeg = ''
    picture_img_alt = ''
    a_product_lockup__title_href = ''
    a_product_lockup__title = ''
    a_product_lockup__subtitle_href = ''
    a_product_lockup__subtitle = ''
    
    pdNR = pd.DataFrame(columns=['amSort',
                                 'product_lockup_aria_label',
                                 'artwork_component_artwork_bg_color',
                                 'artwork_component_artwork_placeholder_bg_color',
                                 'picture_srcset_webp',
                                 'picture_srcset_jpeg',
                                 'picture_img_alt',
                                 'a_product_lockup__title_href',
                                 'a_product_lockup__title',
                                 'a_product_lockup__subtitle_href',
                                 'a_product_lockup__subtitle',
                                 'amReleaseDate',
                                 'amReleaseDateText',
                                 'newOnThisWeek'])
    amSort = 0

    html_li = ''''''

    i = 0
    pos = len(ul_string) - 1

    fullCard0 = '<li class="grid-item '
    fullCard1 = '</li>'
    while i < pos:
        if ul_string.find(fullCard0, i) > -1:
            posCard0 = ul_string.find(fullCard0, i) + len(fullCard0)
            posCard1 = ul_string.find(fullCard1, posCard0) 
            i = posCard0
            while i < posCard1:
                pos_a = '<div class="product-lockup '
                pos_z = '" data-testid="product-lockup">'
                pos_i = 'aria-label="'
                if ul_string[i:i + len(pos_a)] == pos_a:
                    posStr0 = ul_string.find(pos_i, i) + len(pos_i)
                    posStr1 = ul_string.find(pos_z, posStr0)
                    product_lockup_aria_label = ul_string[posStr0:posStr1].strip() #--- ! ----
                    i = ul_string.find(pos_z, i)

                pos_a = '<div data-testid="artwork-component"'
                pos_z = '<picture'
                pos_i = 'artwork-bg-color: '
                pos_j = ';'
                if ul_string[i:i + len(pos_a)] == pos_a:
                    posStr0 = ul_string.find(pos_i, i) + len(pos_i)
                    posStr1 = ul_string.find(pos_j, posStr0)
                    artwork_component_artwork_bg_color = ul_string[posStr0:posStr1].strip() #--- ! ----
                    i = ul_string.find(pos_z, i)

                pos_a = '<picture '
                pos_z = '</picture>'
                pos_i = 'srcset="'
                pos_j = '" type'
                if ul_string[i:i + len(pos_a)] == pos_a:
                    posStr0 = ul_string.find(pos_i, i) + len(pos_i)
                    posStr1 = ul_string.find(pos_j, posStr0)
                    picture_srcset_webp = ul_string[posStr0:posStr1].strip() #--- ! ----
                    i = posStr1

                    posStr0 = ul_string.find(pos_i, i) + len(pos_i)
                    posStr1 = ul_string.find(pos_j, posStr0)
                    picture_srcset_jpeg = ul_string[posStr0:posStr1].strip() #--- ! ----
                    i = ul_string.find(pos_z, i)

                pos_a = '<div class="product-lockup__content '
                pos_z = posCard1 - 1
                if ul_string[i:i + len(pos_a)] == pos_a:
                    pos_i = 'a href="'
                    pos_j = '"'
                    posStr0 = ul_string.find(pos_i, i) + len(pos_i)
                    posStr1 = ul_string.find(pos_j, posStr0)
                    a_product_lockup__title_href = ul_string[posStr0:posStr1].strip() #--- ! ----
                    i = posStr1

                    pos_i = '>'
                    pos_j = '</a'
                    posStr0 = ul_string.find(pos_i, i) + len(pos_i)
                    posStr1 = ul_string.find(pos_j, posStr0)
                    a_product_lockup__title = ul_string[posStr0:posStr1].strip() #--- ! ----
                    i = posStr1

                    pos_i = 'a href="'
                    pos_j = '"'
                    posStr0 = ul_string.find(pos_i, i) + len(pos_i)
                    posStr1 = ul_string.find(pos_j, posStr0)
                    a_product_lockup__subtitle_href = ul_string[posStr0:posStr1].strip() #--- ! ----
                    i = posStr1

                    pos_i = '>'
                    pos_j = '<'
                    posStr0 = ul_string.find(pos_i, i) + len(pos_i)
                    posStr1 = ul_string.find(pos_j, posStr0)
                    a_product_lockup__subtitle = ul_string[posStr0:posStr1].strip() #--- ! ----
                    i = pos_z

                i += 1

            try:
                CS2_request = s.get(a_product_lockup__title_href, timeout=30)
                CS2_request.encoding = 'UTF-8'
                CS2_res = CS2_request.text
            except Exception as e:
                print(f"Error accessing album page: {e}")
                continue  # Skip this album

            bigstring = 'data-testid="tracklist-footer-description">'
            ul2_r = CS2_res.find(bigstring)
            ul2_p = CS2_res.find('\n', ul2_r)
            ul2_string = CS2_res[ul2_r + len(bigstring):ul2_p]
            date_time2 = datetime.datetime.strptime(ul2_string, '%B %d, %Y')

            amSort += 1
            serTemp = pd.Series(data=[amSort,
                                      product_lockup_aria_label,
                                      artwork_component_artwork_bg_color,
                                      artwork_component_artwork_placeholder_bg_color,
                                      picture_srcset_webp,
                                      picture_srcset_jpeg,
                                      picture_img_alt,
                                      a_product_lockup__title_href,
                                      a_product_lockup__title,
                                      a_product_lockup__subtitle_href,
                                      a_product_lockup__subtitle,
                                      date_time2, 
                                      ul2_string, 
                                      ''], index=pdNR.columns)

            pdNR.loc[len(pdNR.index)] = serTemp

            # No need in GitHub run
            # print('Comming Soon [' + str(amSort) + ']', end='\r')
        i += 1
    
    AMRelDate = 'Date 0, 9999'
    for index, row in pdNR.sort_values(by=['amReleaseDate', 'amSort'], ascending=[True, True]).iterrows():
        #here must be <li> building construction!
        if row.iloc[11] <= datetime.datetime.now() + datetime.timedelta(hours=3): # GitHub server time is UTC (-3 from Moscow), so i add +3 hours to log actions in Moscow time. Only where time matters
            row.iloc[12] = 'Delayed'
        if AMRelDate != row.iloc[12]:
            if AMRelDate != 'Date 0, 9999':
                html_li += '''
      </ul>
'''         
            html_li += '''      <div class="main-date">
        <h2 class="title svelte-hprj71" data-testid="header-title">''' + row.iloc[12] + '''</h2>
      </div>    
      <ul class="grid svelte-1p1n7nd grid--flow-row" data-testid="grid">
'''
            AMRelDate = row.iloc[12]

        pdCS = pd.read_csv(csReleasesDB, sep=";")
        pdAIDDB = pd.read_csv(artistIDsDB, sep=";")
        if len(pdCS.loc[pdCS['album__href'] == row.iloc[7]]) == 0:
            row.iloc[13] = 1

            fieldNamesCS = ['update__date', 'album_cover__jpeg', 'album__href', 'album__name', 'artist__href', 'artist__name', 'release__date', 'release__date_text']
            csvCS = open(csReleasesDB, 'a+', newline='') 
            writerCS = csv.DictWriter(csvCS, delimiter=';', fieldnames=fieldNamesCS)

            writerCS.writerow({'update__date': str(datetime.datetime.now())[0:10],
                               'album_cover__jpeg': row.iloc[5][0:row.iloc[5].find(' ')],
                               'album__href': row.iloc[7],
                               'album__name': row.iloc[8].replace('&amp;','&'), 
                               'artist__href': row.iloc[9],
                               'artist__name': row.iloc[10].replace('&amp;','&'), 
                               'release__date': row.iloc[11],
                               'release__date_text': row.iloc[12]})

            # Telegram notifications disabled

        css_newRelease = '<a class="product-lockup__title svelte-21e67y"'
        if row.iloc[13] == 1:
            css_newRelease = '<a class="product-lockup__title svelte-21e67y new-release"'

        html_li += '''
       <li class="grid-item svelte-1p1n7nd" data-testid="grid-item">
        <div aria-label="''' + row.iloc[1] + '''" class="product-lockup svelte-21e67y" data-testid="product-lockup">
         <div aria-hidden="false" class="product-lockup__artwork svelte-21e67y has-controls">
          <div class="artwork-component artwork-component--aspect-ratio artwork-component--orientation-square svelte-e284u3 artwork-component--fullwidth artwork-component--has-borders" data-testid="artwork-component" style="
                  --artwork-bg-color: ''' + row.iloc[2] + ''';
                  --aspect-ratio: 1;
                  --placeholder-bg-color: ''' + row.iloc[2] + ''';
             ">
           <picture class="svelte-e284u3">
            <source sizes=" (max-width:1319px) 296px,(min-width:1320px) and (max-width:1679px) 316px,316px" srcset="''' + row.iloc[4] + '''" type="image/webp"/>
            <source sizes=" (max-width:1319px) 296px,(min-width:1320px) and (max-width:1679px) 316px,316px" srcset="''' + row.iloc[5] + '''" type="image/jpeg"/>
            <img alt="''' + row.iloc[6] + '''" class="artwork-component__contents artwork-component__image svelte-e284u3" decoding="async" height="316" loading="lazy" role="presentation" src="/assets/artwork/1x1.gif" style="opacity: 1;" width="316"/>
           </picture>
          </div>
         </div>
         <div class="product-lockup__content svelte-21e67y">
          <div class="product-lockup__content-details svelte-21e67y">
           <p class="product-lockup__subtitle-links svelte-21e67y product-lockup__subtitle-links--singlet" data-testid="product-lockup-subtitles">
            <div class="multiline-clamp svelte-1qrlry multiline-clamp--overflow" style="--lineClamp: 1;">
             <a class="product-lockup__subtitle svelte-21e67y link" data-testid="product-lockup-subtitle" href="''' + row.iloc[9] + '''">
              ''' + row.iloc[10] + '''
             </a>
            </div>
           </p>           
           <div class="product-lockup__title-link svelte-21e67y product-lockup__title-link--multiline">
            <div class="multiline-clamp svelte-1qrlry multiline-clamp--overflow" style="--lineClamp: 2;">
             ''' + css_newRelease + ''' data-testid="product-lockup-title" href="''' + row.iloc[7] + '''">
              ''' + row.iloc[8] + '''
             </a>
            </div>
           </div>
          </div>
         </div>
        </div>
       </li>
'''

# GitHub server time is UTC (-3 from Moscow), so i add +3 hours to log actions in Moscow time. Only where time matters
    html_li += '''
      </ul>
    </div> 
  </div>   
</div>
<div class="main">
  <i>Updated: ''' + str(datetime.datetime.now() + datetime.timedelta(hours=3)) + '''</i>
</div>
</body>
'''

    with open(rootFolder + 'index.html', 'r+') as idx2:
        idx2Content = idx2.read()
        ul_idx_r = idx2Content.find('      <div class="main-date">')
        ul_idx_string = idx2Content[ul_idx_r:]
        idx2Content = idx2Content.replace(ul_idx_string, html_li)
        idx2.seek(0, 0)
        idx2.truncate(0)
        idx2.write(idx2Content)
    idx2.close()    
#----------------------------------------------------------------------------------------------------

def CS2NR():
# Coming soon to New Releases  

    pdNR = pd.read_csv(newReleasesDB, sep=";")
    pdCS = pd.read_csv(csReleasesDB, sep=";")
    pdCSNR = pd.DataFrame(columns=['artist', 'album', 'link', 'image'])

    for index, row in pdCS.iterrows():
        if datetime.datetime.strptime(row.iloc[6], "%Y-%m-%d %H:%M:%S") <= datetime.datetime.now():
            if len(pdNR.loc[pdNR['link'] == row.iloc[2]]) == 0:
                try:
                    CS2_request = s.get(row.iloc[2], timeout=30)
                    CS2_request.encoding = 'UTF-8'
                    CS2_res = CS2_request.text
                except Exception as e:
                    print(f"Error accessing CS2NR album page: {e}")
                    continue  # Skip this album
                bigstring = 'data-testid="tracklist-footer-description">'
                ul2_r = CS2_res.find(bigstring)
                ul2_p = CS2_res.find('\n', ul2_r)
                ul2_string = CS2_res[ul2_r + len(bigstring):ul2_p]
                date_time2 = datetime.datetime.strptime(ul2_string, '%B %d, %Y')
                if row.iloc[6] != date_time2 and date_time2 > datetime.datetime.now():
                    pdCS.loc[index, 'release__date'] = date_time2
                    pdCS.loc[index, 'release__date_text'] = ul2_string
                else:
                    pdCSNR.loc[len(pdCSNR.index)] = [row.iloc[5], row.iloc[3], row.iloc[2], row.iloc[1]]

    # !!! ЗАПИСЬ В БД !!!
    pdCS.to_csv(csReleasesDB, sep=';', index=False)
    pdNR = pd.DataFrame()
    pdCS = pd.DataFrame()

    if len(pdCSNR) > 0:
        dldCategory = 'CS'
        caText = 'ANIME - CS'
        caGrad = '#FF6B9D, #C44569'

        dldDate = str(datetime.datetime.now())[0:10]
        htmlHead = """<head>
  <meta charset="utf-8">
  <title>Apple Music Releases</title>
  <link rel="stylesheet" type="text/css" href="../Resources/styles.css" />
  <SCRIPT language=JavaScript type=text/JavaScript>
    <!--
    function show(id) {
      if(document.getElementById("show" + id).style.display == 'none') {
        document.getElementById("show" + id).style.display = '';
      }else{
        document.getElementById("show" + id).style.display = 'none';
      }
    }

    function show_tr(id) {
      var elms;
      if (id=="v") {
        elms = document.querySelectorAll("[id='v']");
      } else if (id=="x") {
        elms = document.querySelectorAll("[id='x']");
      } else if (id=="d") {
        elms = document.querySelectorAll("[id='d']");
      } else if (id=="o") {
        elms = document.querySelectorAll("[id='o']");
      } else if (id=="") {
        elms = document.querySelectorAll("[id='']");
      }
      for (var i = 0; i < elms.length; i++) {
        if (elms[i].style.display == 'none') {
          elms[i].style.display = '';
        } else {
          elms[i].style.display = 'none';
        }
      }
    }
    //-->
  </SCRIPT>
</head>

<body>
  <input id="bV" type="button" value="V" onclick="show_tr('v');" class="bV" />
  <input id="bD" type="button" value="D" onclick="show_tr('d');" class="bD" />
  <input id="bX" type="button" value="O" onclick="show_tr('o');" class="bO" />
  <input id="bX" type="button" value="X" onclick="show_tr('x');" class="bX" />
  <input id="bE" type="button" value="  " onclick="show_tr('');" class="bE" />
  <input type="button" onclick="location.href='../index.html';" value="Index"  class="bI"/>
  <hr>
"""

        htmlStart = """  <table border="1">
    <tr id=""" + ('\"' + dldDate + '_' + caText + '\"').lower().replace(' ','_') +  """><th colspan="2" style="background: linear-gradient(to right, """ + caGrad + """);">""" + dldDate + """ | """ + caText + """</th></tr>
    <tr><th width="100px">Cover</th><th width="600px">Album</th></tr>
"""

        htmlText = ''

        htmlEnd = """  </table>
  <hr>
"""

        htmlFinal = """  <!-- End of File -->
  <script id="rendered-js" >
    [...document.querySelectorAll('[data-frame-load]')].forEach(button => {
      button.addEventListener('click', () => {
        const group = button.getAttribute('data-frame-load');
        [...document.querySelectorAll(`[data-frame-group="${group}"]`)].forEach(frame => {
          javascript:show(frame.getAttribute('data-frame-group') + '_');
          frame.setAttribute('src', frame.getAttribute('data-frame-src'));
        });
      });
    });
  </script>
</body>
"""

        fieldNames = ['date', 'category', 'artist', 'album', 'Best_Fav_New_OK', 'rec_send2TG', 'link', 'link_ym', 'link_zv', 'imga', 'send2TG', 'TGmsgID']
        csvfile = open(newReleasesDB, 'a+', newline='')
        writer = csv.DictWriter(csvfile, delimiter=';', fieldnames=fieldNames)

        for index, row in pdCSNR.iterrows():
            aralname = row.iloc[0] + ' - ' + row.iloc[1]
            aralinsert = aralname.replace(row.iloc[0], row.iloc[0] + '</b>') if len(aralname) < 80 else aralname[:aralname[:80].rfind(' ') + 1].replace(row.iloc[0], row.iloc[0] + '</b>') + '<br>' + aralname[aralname[:80].rfind(' ') + 1:]
            writer.writerow({'date': dldDate, 
                          'category': dldCategory, 
                          'artist': row.iloc[0], 
                          'album': row.iloc[1], 
                          'Best_Fav_New_OK': '', 
                          'rec_send2TG': '', 
                          'link': row.iloc[2], 
                          'link_ym': '', # External services disabled
                          'link_zv': '', # External services disabled
                          'imga': row.iloc[3], 
                          'send2TG': '', 
                          'TGmsgID': ''})

            htmlText += f"""  <!-- {row.iloc[0]} - {row.iloc[1]} -->
    <tr style="display:;" id=''>
      <td><a href="{row.iloc[3].replace('296x296bb.webp', '100000x100000-999.jpg').replace('296x296bf.webp', '100000x100000-999.jpg').replace('296x296bf-60.jpg', '100000x100000-999.jpg')}" target="_blank"><img src="{row.iloc[3]}" height="100px"></a></td>
      <td class="album_name"><a href="{row.iloc[2]}" target="_blank"><b>{aralinsert}</a><br><br><button data-frame-load="{row.iloc[2][row.iloc[2].rfind('/') + 1:]}">Preview</button></td>
    </tr> 
    <tr style="display:none;" id="show{row.iloc[2][row.iloc[2].rfind('/') + 1:]}_"><td colspan="2"><iframe id="embedPlayer" data-frame-group="{row.iloc[2][row.iloc[2].rfind('/') + 1:]}" data-frame-src="{row.iloc[2].replace('://', '://embed.')}?app=music&amp;itsct=music_box_player&amp;itscg=30200&amp;ls=1&amp;theme=light" height="450px" frameborder="0" sandbox="allow-forms allow-popups allow-same-origin allow-scripts allow-top-navigation-by-user-activation" allow="autoplay *; encrypted-media *; clipboard-write" style="width: 100%; overflow: hidden; border-radius: 10px; transform: translateZ(0px); animation: 2s ease 0s 6 normal none running loading-indicator; background-color: rgb(228, 228, 228);"></iframe></td></tr>
"""

        csvfile.close()

        yearNOW = dldDate[0:4]
        monthNOW = dldDate[0:7]
        monthTextNOW = datetime.datetime.strptime(dldDate, '%Y-%m-%d').strftime('%B')    
        HTMLFile = open(rootFolder + "index.html", "r")
        index = HTMLFile.read()
        monthDB = index[index.find('<a href="AMRs/AMR ') + len('<a href="AMRs/AMR '):index.find('.html">')]
        HTMLFile.close()
        monthTextDB = datetime.datetime.strptime(monthDB, '%Y-%m').strftime('%B')
        yearDB = monthDB[0:4]
        newMonth = 0
        newYear = 0

        if yearNOW != yearDB:
            newYear = 1
            with open(rootFolder + 'index.html', 'r+') as idx:
                idxContent = idx.read()
                idxContent = idxContent.replace('\n    <h2 class="title svelte-hprj71" data-testid="header-title">' + yearDB + ':</h2>',
                                              '\n    <h2 class="title svelte-hprj71" data-testid="header-title">' + yearNOW + ':</h2>\n        <a href="AMRs/AMR ' + monthNOW + '.html">' + monthTextNOW + '</a><br>\n    <h2 class="title svelte-hprj71" data-testid="header-title">' + yearDB + ':</h2>')
                idx.seek(0, 0)
                idx.write(idxContent)
            idx.close()
        else:
            if monthNOW != monthDB:
                newMonth = 1
                with open(rootFolder + 'index.html', 'r+') as idx:
                    idxContent = idx.read()
                    idxContent = idxContent.replace('\n        <a href="AMRs/AMR ' + monthDB + '.html">' + monthTextDB + '</a>',
                                                    '\n        <a href="AMRs/AMR ' + monthNOW + '.html">' + monthTextNOW + '</a> | \n        <a href="AMRs/AMR ' + monthDB + '.html">' + monthTextDB + '</a>')
                    idx.seek(0, 0)
                    idx.write(idxContent)
                idx.close()

        if htmlText != '':
            if newMonth == 1 or newYear == 1:
                with open(amrsFolder + 'AMR ' + monthNOW + '.html', 'w') as h2r:
                    h2r.write(htmlHead + '\n' + htmlStart + htmlText + htmlEnd + '\n' + htmlFinal)
                h2r.close()            
            else:
                with open(amrsFolder + 'AMR '+monthNOW + '.html', 'r+') as h2r:
                    h2rContent = h2r.read()
                    h2rContent = h2rContent.replace(htmlHead, '')
                    h2r.seek(0, 0)
                    h2r.write(htmlHead + '\n' + htmlStart + htmlText + htmlEnd + '\n' + h2rContent)
                h2r.close()

# nextWeekReleases_sender function removed - Telegram disabled
#----------------------------------------------------------------------------------------------------

amnr_logger('[Apple Music New Releases]', ver + " (c)&(p) 2022-" + str(datetime.datetime.now())[0:4] + " by Viktor 'MushroomOFF' Gribov")
caLink = find_link('https://music.apple.com/nz/curator/apple-anime/982302294', 'New Releases')

caText = 'ANIME'
caGrad = '#FF6B9D, #C44569'
collect_albums(caLink, caText, caGrad)
amnr_logger('[Apple Music New Releases]', 'Anime [NZ]     - OK')

# 只保留动画音乐，不需要Hard Rock
# caLink = find_link('https://music.apple.com/jp/curator/apple-music-hard-rock/979231690', 'New Releases')
# caText = 'HARD ROCK'
# caGrad = '#EE702E, #F08933'
# collect_albums(caLink, caText, caGrad)
# amnr_logger('[Apple Music New Releases]', 'Hard Rock [JP] - OK')

# caLink = 'https://music.apple.com/ru/room/1118077423'
# caText = 'METAL - RU'
# caGrad = '#81BB98, #9AD292'
# collect_albums(caLink, caText, caGrad)
# amnr_logger('[Apple Music New Releases]', 'Metal [RU]     - OK')

# caLink = 'https://music.apple.com/ru/room/1532200949'
# caText = 'HARD ROCK - RU'
# caGrad = '#EE702E, #F08933'
# collect_albums(caLink, caText, caGrad)
# amnr_logger('[Apple Music New Releases]', 'Hard Rock [RU] - OK')

caLink = find_link('https://music.apple.com/nz/curator/apple-anime/982302294', 'Coming Soon')
coming_soon(caLink)
amnr_logger('[Apple Music New Releases]', 'Comming Soon   - OK')

CS2NR()
amnr_logger('[Apple Music New Releases]', 'Anime [CS]     - OK')

amnr_logger('[Apple Music New Releases]', '[V] Done!')
