#main file

import requests
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
import copy
import numpy

def rgbString(r, g, b): 
    #https://www.cs.cmu.edu/~112/notes/notes-graphics.html#otherShapesAndText
    # Don't worry about the :02x part, but for the curious,
    # it says to use hex (base 16) with two digits.
    return f'#{r:02x}{g:02x}{b:02x}'

CLIENT_ID = '61a8d28c87264535b7d48422dab5ef0b'
CLIENT_SECRET = 'ff81e90e0070439a83f330f0aa2f4f8f'
AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'

COLOR_SCHEMES = ((rgbString(190, 255, 210), rgbString(54, 170, 116), rgbString(0, 82, 58), 'a'), 
                (rgbString(211, 196, 227), rgbString(215, 65, 167), rgbString(58, 23, 114), 'b'),
                (rgbString(253, 212, 191), rgbString(242, 163, 166), rgbString(206, 106, 133), 'c'),
                (rgbString(247, 249, 249), rgbString(146, 220, 229), rgbString(43, 45, 66), 'd'))
#custom picked color scheme tuple: first is lightest color, midtone, darker color

def playSong(url):
    r = requests.get(url, allow_redirects=True)
    print(url, r)
    open('song.mp3', 'wb').write(r.content)
    pygame.mixer.music.load('song.mp3')
    pygame.mixer.music.play()
    pygame.mixer.music.set_volume(0.2)

class Track (object):
    def __init__ (self, trackData): 
        self.trackData = trackData
        self.complete = False
        self.selected = True
        self.hovered = False
        
    def addAttributes(self, attributes):
        self.attributes = attributes
        if attributes:
            self.complete = True
        else:
            print("Attributes not found")
    def addTSNE(self, tsne):
        self.tsne = tsne

    def isComplete(self):
        return self.complete
    def setScreenSpace(self, x, y, r):
        self.screenX = x
        self.screenY = y
        self.radius = r

    def setBucket(self, index):
        self.bucket = index

    def getBucket(self):
        return self.bucket

    def getTSNE(self):
        return self.tsne

    def getTrackId(self): #string
        return self.trackData['id']

    def getTrackName(self): #string
        return self.trackData['name']

    def getArtist(self): #JSON
        return self.trackData['artists'][0]  

    def getPreviewLink(self): #string
        return self.trackData['preview_url']

    def getAlbumName(self): #string
        return self.trackData['album']['name']

    def getDate(self): #string
        return self.trackData['album']['release_date']

    def getPopularity(self): #int
        return self.trackData['popularity']

    def getAttributes(self): #JSON
        if self.complete and self.attributes:
            return self.attributes

    def getTrackData(self): #JSON
        return self.trackData   
    
    def prominentFeatures(self): 
        # all songs beyond a certain threshold are joined together in a sentence
        attributeDict = {}
        avg = 0
        for attribute in self.attributes:
            selected = ['danceability', 'energy', 'loudness', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence']
            if attribute not in selected:
                continue
            attributeDict[attribute] = self.attributes[attribute]
            avg += self.attributes[attribute]

        threshUpper = 0.9
        threshLower = 0.1
        prominentFinal = 'This song is significantly '
        keywords = []
        for attributeKey in attributeDict:
            if attributeDict[attributeKey] > threshUpper:
                if attributeKey == 'danceability':
                    keyword = 'danceable' 
                elif attributeKey == 'energy':
                    keyword = 'energetic'
                elif attributeKey == 'loudness':
                    keyword = 'loud'
                elif attributeKey == 'speechiness':
                    keyword = 'speechy'
                elif attributeKey == 'acousticness':
                    keyword = 'acoustic'
                elif attributeKey == 'instrumentalness':
                    keyword = 'instrumental'
                elif attributeKey == 'liveness':
                    keyword = 'lively'
                elif attributeKey == 'valence':
                    keyword = 'happy'
            elif attributeDict[attributeKey] < threshLower:
                if attributeKey == 'danceability':
                    keyword = 'less danceable' 
                elif attributeKey == 'energy':
                    keyword = 'slow'
                elif attributeKey == 'loudness':
                    keyword = 'quiet'
                elif attributeKey == 'speechiness':
                    keyword = 'less speechy'
                elif attributeKey == 'acousticness':
                    keyword = 'synthetic'
                elif attributeKey == 'instrumentalness':
                    keyword = 'less instrumental'
                elif attributeKey == 'valence':
                    keyword = 'sad'
            else:
                continue

            if keyword:
                keywords.append(keyword)
        if len(keywords) == 2:
            joinedKeywords = keywords[0] + ' and ' + keywords[1]
        else:
            joinedKeywords = ', '.join(keywords)
            joinedKeywords = joinedKeywords.rsplit(',', 1)[0] + ', and' + joinedKeywords.rsplit(',', 1)[1]
        return prominentFinal + joinedKeywords + '.'

    def getScreenSpace(self): 
        return self.screenX, self.screenY, self.radius

    def checkPress(self, app, event): #true/false
        try:
            dx = self.screenX - event.x
            dy = self.screenY - event.y
            if (dx ** 2 + dy ** 2)**0.5 <= self.radius:
                self.selected = True
                playSong(self.getPreviewLink())
                return True
            else:
                self.selected = False
                return False
        except Exception as e:
            self.selected = False

    def checkHover(self, app, event):
        dx = self.screenX - event.x
        dy = self.screenY - event.y
        if (dx ** 2 + dy ** 2)**0.5 <= self.radius:
            app.selectedBucket = self.getBucket()
            self.hovered = True
            return True
        else:
            self.hovered = False
            return False
        
def getTokenClientCredentials(): 
    #https://stmorse.github.io/journal/spotify-api.html
    response = requests.post(AUTH_URL, {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    })
    return response.json()['access_token']

def getArtistData(authToken, artist_id = '36QJpDe2go2KgaRleHCDTp'):
    #gets
    headers = {
        'Authorization': 'Bearer {token}'.format(token=authToken)
    }
    r = requests.get(BASE_URL + 'artists/' + artist_id , 
                 headers=headers)
    d = r.json()
    return d

def getArtistTopTracks(authToken, artist_id = '36QJpDe2go2KgaRleHCDTp'):
    headers = {
        'Authorization': 'Bearer {token}'.format(token=authToken)
    }
    r = requests.get(BASE_URL + 'artists/' + artist_id + '/top-tracks' , 
                 headers=headers, params = {'market':'US'})
    d = r.json()
    # print(d)
    trackList = set()
    for track in d['tracks']:
        trackList.add(track['id'])
    return trackList

def getArtistSongs(authToken, artist_id = '36QJpDe2go2KgaRleHCDTp'):
    print('getting artist for id:', artist_id)
    # defaults to drake
    headers = {
        'Authorization': 'Bearer {token}'.format(token=authToken)
    }
    # https://stmorse.github.io/journal/spotify-api.html 
    # START CITATION: Minimal modification
    r = requests.get(BASE_URL + 'artists/' + artist_id + '/albums', 
                 headers=headers, 
                 params={'include_groups': 'album,single', 'limit': 50})
    d = r.json()
    albums = [] # to keep track of duplicates
    allTracks = {}  
    # loop over albums and get all tracks
    # if len(d['items']) == 0:
    #     return None
    for album in d['items']:
        album_name = ascii(album['name']) 
        #added in by me, deals with non-ascii letters
        trim_name = album_name.split('(')[0].strip()
        if trim_name.upper() in albums:
            continue
        albums.append(trim_name.upper()) # use upper() to standardize
        # this takes a few seconds so let's keep track of progress    
        print(album_name)
        # pull all tracks from this album
        r = requests.get(BASE_URL + 'albums/' + album['id'] + '/tracks', 
            headers=headers)
        tracks = r.json()['items']
        # print(tracks)
        #END CITATION 
        # Compile all tracks in album into megalist. 
        # Megalist then put into batches of 50, with much faster analysis
        for trackData in tracks:
            if trackData['id'] not in allTracks.keys():
                allTracks[trackData['id']] = Track(trackData)

    allTracksList = list(allTracks.keys())
    batchSize = 40
    if len(allTracks) == 0:
        return None
    for pair in getIndexes(len(allTracks), batchSize): #batch
        tracksForRequest = ''
        for i in range(pair[0], pair[1]): #song in batch assigned into batch
            tracksForRequest += allTracksList[i] + ','
        # print(tracksForRequest)
        tracksForRequest = tracksForRequest[:-1]
        r = requests.get(BASE_URL + 'audio-features/', 
            headers=headers, params={'ids':tracksForRequest})
        try:
            features = r.json()['audio_features']
        except:
            print(r.json())

        for feature in features:
            if feature == None:
                print('alltracks', feature)

                continue
            allTracks[feature['id']].addAttributes(feature)
    
    return allTracks

def getIndexes (n, batchSize=50): 
    # returns tuples of n batches split into 50s but with a non-len 50 end
    if n == 0:
        return None
    batches = []
    for i in range(0, n//batchSize):
        batches.append( (i*batchSize, i * batchSize + batchSize))
    if n%batchSize != 0:
        batches.append((n - n%batchSize, n))
    return batches 

def analyzeMusic(authToken, dataDict):
    # numpy code written by me, returns dictionary of TSNE pairs
    attributesSelected = ['danceability', 'energy', 'loudness', 'speechiness', 
        'acousticness', 'instrumentalness', 'liveness', 'valence']
    index = 0
    dataArray = numpy.zeros(shape=(len(dataDict),len(attributesSelected) + 1))
    indexDict = {}
    for track in dataDict:
        trackAttributes = numpy.array([index])
        if not dataDict[track].isComplete():
            continue
        for attribute in dataDict[track].getAttributes():
            if attribute in attributesSelected:
                trackAttributes = numpy.append(trackAttributes, 
                    dataDict[track].getAttributes()[attribute])
        dataArray[index] = trackAttributes
        indexDict[index] = track
        index += 1

    #TSNE from https://stmorse.github.io/journal/spotify-api.html 
    Xs = StandardScaler().fit_transform(dataArray)
    if len(Xs) < 2: #has to be on more than two elements
        return {}
    tsne = TSNE(n_components=2, perplexity=5, 
        early_exaggeration=2, random_state=1).fit_transform(Xs)
    for key in indexDict:
        dataDict[indexDict[key]].addTSNE(tsne[key]) 
    return dataDict

import random
def dist(point1, point2):
    return ((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)**0.5

def kMeansCluster(tracks, numClusters): #wrapper function
    # https://www.analyticsvidhya.com/blog/2019/08/comprehensive-guide-k-means-clustering/
    # main steps:
        # Pick a point as a centroid
        # Assign points to said centroid
        # Create a new centroid based on the average/center of assigned points/clusters
        # Recursively do this until the end condition.
    def calculateCentroid(points):
        if len(points)<0:
            print('empty centroid cluster')
            return (0,0) 
        tX = 0
        tY = 0
        for p in points:
            tX += p[0]
            tY += p[1]
        return (tX/len(points), tY/len(points))

    def nearestCentroid(point, centroids):
        closestDist = None
        closestCentroid = None
        for i in range(len(centroids)):
            distPC = dist(point, centroids[i])
            if closestDist == None or distPC < closestDist:
                closestCentroid = i
                closestDist = distPC
        if closestDist == None or closestCentroid == None:
            return None
        return closestCentroid
    
    tsneDict = {} #[tsne tuple, integer cluster code]
    for trackId in tracks:
        tsneDict[trackId] = [tuple(tracks[trackId].getTSNE()), None]
    startingCentroids = [None] * numClusters
    # distPC = dist(point, centroids[i])
    # start with random centroids
    for i in range(numClusters):
        rKey = random.choice(list(tsneDict.keys()))
        while tsneDict[rKey][0] in startingCentroids:
            rKey = random.choice(list(tsneDict.keys()))
        tsneDict[rKey][1] = i
        startingCentroids[i] = tsneDict[rKey][0]

    def kMeansHelper (tracks, centroids, iterations):
        if iterations == 0: #base case
            return tracks

        newTracks = {} # id: (tsne, bucket)
        clusters = {} # {centroid bucket number : track tsne value}

        #assign new clusters
        for trackID in tracks:
            groupNum = nearestCentroid(tracks[trackID][0], centroids)
            trackTSNE = tracks[trackID][0]
            newTracks[trackID] = (trackTSNE, groupNum)
            if groupNum not in clusters.keys():
                clusters[groupNum] = []
            clusters[groupNum].append(trackTSNE)

        newCentroids = {}
        for clusterKey in clusters:
            # calculate new centroids
            newCentroids[clusterKey] = calculateCentroid(clusters[clusterKey])
        return kMeansHelper(newTracks, newCentroids, iterations - 1)
        
    return kMeansHelper (tsneDict, startingCentroids, 50)

def searchMusic(authToken, searchField): #gets query, returns as JSON
    headers = {
        'Authorization': 'Bearer {token}'.format(token=authToken)
    }
    if len(searchField) == 0:
        return None
    query = ''
    for keyword in searchField.split(' '):
        query += keyword + '+'
    query = query[:-1]
    r = requests.get(BASE_URL + 'search/' , 
                 headers=headers, 
                 params={'q': query, 'type': 'artist'})
    d = r.json()
    return d['artists']['items']

from cmu_112_graphics import *

class customButton (object):
    def __init__ (self, callback, name, aX, aY, width, height, anchor = 'nw', color = 'grey', additionalData = '', outline = ''):
        self.color = color
        self.callback = callback
        self.name = name
        self.updateButton(aX, aY, width, height, color = self.color, outline = outline)
        self.additionalData = additionalData
        
    def updateButton(self, aX, aY, width, height, anchor = 'nw', color = 'grey', outline = ''):
        self.color = color
        self.outline = outline
        if anchor == 'nw':
            self.x0 = aX
            self.y0 = aY
            self.x1 = aX + width
            self.y1 = aY + height
        else:
            self.x0 = aX - width / 2
            self.y0 = aY - height / 2
            self.x1 = aX + width / 2
            self.y1 = aY + height / 2
        self.x0, self.x1 = min(self.x0, self.x1), max(self.x0, self.x1)
        self.y0, self.y1 = min(self.y0, self.y1), max(self.y0, self.y1)
    def __str__ (self):
        return 'name {} x0 {} y0 {} x1 {} y1 {}'.format(self.name, self.x0, self.y0, self.x1, self.y1)

    def checkPress(self, app, event):
        if event.x >= self.x0 and event.x <= self.x1 and event.y >= self.y0 and event.y <= self.y1:
            if len(self.additionalData) > 0:
                self.callback(app, self.additionalData)
            else:
                self.callback(app)

    def drawButton(self, app, canvas):
        centerX = self.x0 + abs(self.x1 - self.x0) / 2
        centerY = self.y0 + abs(self.y1 - self.y0) / 2
        # print(self.color)
        if self.outline != '':
            canvas.create_rectangle(self.x0, self.y0, self.x1, self.y1, fill = app.medium, outline = app.lighter)
            canvas.create_text(self.x0 + 5, centerY, text = self.name, fill = app.lighter, anchor = 'w')
        else:
            canvas.create_rectangle(self.x0, self.y0, self.x1, self.y1, fill = app.medium, outline = '')
            canvas.create_text(self.x0 + 5, centerY, text = self.name, fill = app.lighter, anchor = 'w')

    def getDims(self):
        return self.x0, self.y0, self.x1, self.y1
    
def searchPressed(app):
    app.isSearching = True
    app.buttons['searchButton'].name = 'Type to search'
    print('pressed')



import pygame

def selectColorScheme(app):
    scheme = random.choice(COLOR_SCHEMES)
    try:
        while scheme[0] == app.lighter:
            scheme = random.choice(COLOR_SCHEMES)
    except:
        pass
    app.lighter = scheme[0]
    app.medium = scheme[1]
    app.darker = scheme[2]
    print(scheme)

def selectArtist(app, artistID): 
    # called everytime an artist is loaded, acts as a secondary appstarted for certain attributes
    selectColorScheme(app)
    app.selectedBucket = None
    app.timeStart = 0
    app.timeEnd = 0
    app.recommendationCluster = None
    app.searchField = ''
    app.isSearching = False
    app.artistData = getArtistData(app.authToken, artistID)
    print(app.artistData)
    if app.artistData['images']:
        app.artistImage = app.loadImage(app.artistData['images'][0]['url'])
        app.artistImage = app.scaleImage(app.artistImage, 1/6)
    else:
        app.artistImage = None
    trackInfo = getArtistSongs(app.authToken, artistID)
    app.topArtistTracks = getArtistTopTracks(app.authToken, artistID)

    app.clusterDict = {}
    if trackInfo:
        app.disp = (0,0)
        app.scale = 5
        app.dataPoints = analyzeMusic(app.authToken, trackInfo)
        clustered = kMeansCluster(app.dataPoints, 10)
        
        for trackId in clustered:
            if clustered[trackId][1] not in app.clusterDict.keys():
                app.clusterDict[clustered[trackId][1]] = set()
            app.clusterDict[clustered[trackId][1]].add(trackId)

            app.dataPoints[trackId].setBucket(clustered[trackId][1])
    else:
        app.dataPoints = {}

def appStarted(app):
    selectColorScheme(app)
    app.helpImage = app.loadImage('help.png')
    app.clicked = False
    app.centerX, app.centerY = app.width // 2, app.height // 2
    pygame.init()
    pygame.mixer.init()
    app.disp = (0,0)
    app.screenDisp = (0,0)
    app.dragDisp = (0,0)
    b = customButton(searchPressed, name = 'Search Artists', aX = 35, aY = 80, width = 150, height = 25, color = app.medium, outline = app.lighter)
    app.buttons = {'searchButton':b}
    
    app.authToken = getTokenClientCredentials() 
    selectArtist(app, '4O15NlyKLIASxsJ0PrXPfz')

def mouseDragged(app, event):
    app.screenDisp = ((event.x + app.dragDisp[0])/app.scale, (event.y + app.dragDisp[1])/app.scale)
    print('dragged', app.screenDisp, app.scale)

def mouseMoved(app, event):
    hasSelected = False
    for pointKey in app.dataPoints:
        if app.dataPoints[pointKey].checkHover(app, event):
            hasSelected = True
    if not hasSelected:
        app.selectedBucket = None

def mousePressed(app, event):
    app.clicked = True
    app.dragDisp = (app.screenDisp[0]/app.scale  - event.x, app.screenDisp[0]/app.scale - event.y)

    print('pressed', app.dragDisp) 
    for button in app.buttons:
        app.buttons[button].checkPress(app, event)
    hasPressed = False
    for pointKey in app.dataPoints:
        if (app.dataPoints[pointKey].checkPress(app, event)):
            hasPressed = True
            break
    if not hasPressed:
        #select all
        for pointKey in app.dataPoints:
            app.dataPoints[pointKey].selected = True

def mouseReleased(app, event):
    print('released')
    app.dragDisp = (0,0)

def keyPressed(app, event):
    
    app.clicked = True
    print(event.key)
    if not app.isSearching:
        increment = 50 / app.scale
        dx = 0
        dy = 0
        if event.key.upper() == 'W':
            dy = -1
        elif event.key.upper() == 'A':
            dx = 1
        elif event.key.upper() == 'S':
            dy = 1
        elif event.key.upper() == 'D':
            dx = -1
        app.disp = (app.disp[0]+ increment * dx, app.disp[1]+ increment * dy)
    if event.key == 'Up':
        app.scale *= 1.5
    if event.key == 'Down':
        app.scale /= 1.5
    if event.key.isalnum() and len(event.key) == 1 and app.isSearching:
        app.searchField += event.key
    if event.key == 'Delete' and len(app.searchField) > 0:
        app.searchField = app.searchField[:-1]
    if event.key == 'Escape':
        app.searchField = ''
        app.isSearching = False
    if event.key == 'Enter' and len(app.searchField) != 0: 
        #search and replace buttons
        newDict = {}
        for button in app.buttons:
            if 'artist' not in button:
                newDict[button] = app.buttons[button]
        app.buttons = newDict
        d = searchMusic(app.authToken, app.searchField)
        cx, cy = 35,110
        dist = 20
        i = 0
        for item in d:
            key = 'artist:' + item['name'] + str(i)
            print(key)
            b = customButton(selectArtist, name = item['name'], aX = cx, 
                aY = cy + dist*i, width = 150, height = 25, additionalData = item['id'], color = app.medium)
            app.buttons[key] = b

            i += 1
    if event.key == 'Space':
        app.searchField += ' '
    if event.key.upper() == 'H' and app.clicked == True and len(app.searchField) == 0:
        app.clicked = False
    if event.key == 'R':
        selectColorScheme(app)
    if app.isSearching:
        app.buttons['searchButton'].name = app.searchField

        if app.searchField == '':
            app.buttons['searchButton'].name = 'Type to search'
    else:
        app.buttons['searchButton'].name = 'Search Artists'

def redrawAll(app, canvas):
    canvas.create_rectangle(0, 0, app.width, app.height, fill = app.darker)
    for point in app.dataPoints:
        if not app.dataPoints[point].isComplete():
            continue
        name = app.dataPoints[point].getTrackName()
        rSmaller = 5
        r = 8
        rLarger = 15
        pX = app.centerX + (app.screenDisp[0] + app.disp[0] + app.dataPoints[point].getTSNE()[0]) * app.scale
        pY = app.centerY + (app.screenDisp[1] - app.disp[1] + app.dataPoints[point].getTSNE()[1]) * app.scale
        # pX = app.screenDisp[0] + app.centerX + ( app.disp[0] + app.dataPoints[point].getTSNE()[0]) * app.scale
        # pY = app.screenDisp[1] + app.centerY + ( - app.disp[1] + app.dataPoints[point].getTSNE()[1]) * app.scale
        app.dataPoints[point].setScreenSpace(pX, pY, r)
        fill = app.medium
        if app.selectedBucket == app.dataPoints[point].getBucket():
            #highlighted
            fill = app.lighter
        if app.dataPoints[point].hovered or point in app.topArtistTracks:
            canvas.create_oval(pX - rLarger, pY - rLarger, pX + rLarger, pY + rLarger, fill = fill, outline = app.lighter)
            app.dataPoints[point].setScreenSpace(pX, pY, rLarger)
            canvas.create_text(pX, pY + 20, text = name, fill = app.lighter)
        elif app.dataPoints[point].getPreviewLink():
            canvas.create_oval(pX - r, pY - r, pX + r, pY + r, fill = fill, outline = '')
        else:
            canvas.create_oval(pX - rSmaller, pY - rSmaller, pX + rSmaller, pY + rSmaller, fill = fill, outline = '')            

    for buttonKey in app.buttons:
        app.buttons[buttonKey].drawButton(app, canvas)
    drawArtistData(app, canvas)
    drawRecommendedSongs(app, canvas)
    drawTitle(app, canvas)
    # drawHelpString(app, canvas)
    if not app.clicked:
        canvas.create_rectangle(0, 0, app.width, app.height, fill = 'black')
        canvas.create_image(app.width/2, app.height/2, image=ImageTk.PhotoImage(app.helpImage))

def drawHelpString(app, canvas):
    x, y = app.width - 35, 7 * app.height / 8
    dist = 20
    helpString = '''Use the Up and Down keys to zoom in and out.
    Use WASD or drag to pan the screen.
    Hover over an artist for recommendations, and click to hear a preview.
    '''
    i = 0
    for helpLine in helpString.splitlines():
        canvas.create_text(x, y + dist * i, text = helpLine, anchor = 'ne', fill = app.lighter)
        i += 1
        
def drawTitle(app, canvas):
    x, y = 35,35
    canvas.create_text(x, y, text = 'Spotify Profiles', anchor = 'nw', fill = app.lighter, font = 'Helvetica 26 bold')

def drawArtistData(app, canvas):
    x, y = 35, app.height - 150
    dist = 20
    if app.artistImage:
        canvas.create_image(x, y-dist, image=ImageTk.PhotoImage(app.artistImage), anchor = 'sw')
    if not app.artistData:
        return
    canvas.create_text(x, y, text = app.artistData['name'], anchor = 'sw', fill = app.lighter, font = 'Helvetica 36 bold')
    for i in range(len(app.artistData['genres'])):
        if i > 4:
            break
        canvas.create_text(x, y + dist * (i+1), text = app.artistData['genres'][i], anchor = 'nw', fill = app.lighter)

def drawRecommendedSongs(app, canvas):
    if app.selectedBucket == None:
        return
    selected = None
    for trackId in app.clusterDict[app.selectedBucket]:
        if app.dataPoints[trackId].hovered:
            selected = app.dataPoints[trackId].getTrackId()
            break
    if selected == None:
        return
    point0 = (app.dataPoints[selected].getTSNE()[0], app.dataPoints[selected].getTSNE()[1])
    x1, y1 = app.width - 35, 35 #top right corner
    dist = 20
    similarText = "Songs similar to " + app.dataPoints[selected].getTrackName() + ' that you may like:'
    promFeatText = app.dataPoints[selected].prominentFeatures()
    recs = closestNTracks(app, app.clusterDict[app.selectedBucket],point0, 10)
    canvas.create_text(x1, y1, text = promFeatText, fill = app.lighter, anchor = 'ne')
    canvas.create_text(x1, y1 + dist, text = similarText, fill = app.lighter, anchor = 'ne', font = 'Helvetica 14 bold')

    for i in range(len(recs)):
        canvas.create_text(x1, y1 + dist * (i+2), text = app.dataPoints[recs[i]].getTrackName(), fill = app.lighter, anchor = 'ne')

def closestTrack(app, tracks, position):
    closest = None
    closestId = None
    for trackId in tracks:
        d = dist(position, app.dataPoints[trackId].getTSNE())
        if closest == None or d < closest:
            closestId = trackId
            closest = d
    return closestId

def closestNTracks(app, tracks, position, n): # similar to selection sort
    newTracks = copy.copy(tracks)
    closestTracks = []
    for i in range(n):
        if i > len(newTracks):
            break
        closest = closestTrack(app, newTracks, position)
        closestTracks.append(closest)
        newTracks.remove(closest)
    return closestTracks

def runPlot():
    runApp(width=1200, height=1000)

def testAll():
    runPlot()

testAll()