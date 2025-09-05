import requests
import time
import re

# Initialize Request session with common headers
requestSession = requests.Session()
requestSession.headers.update({'Origin': 'https://web.archive.org', 'Accept':'application/json', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'})

def fetchArchiveData(url:str):
    """Simple wrapper for requests that need a dictionary object from the JSON-formatted result."""
    r = requestSession.get(url)
    return r.json()

def formatData(data:list):
    """Formats header-based arrays into a more parsable format"""
    if len(data) == 0:
        return []
    
    newData = []
    header = data.pop(0)
    for listing in data:
        newListing = {}
        for idx, value in enumerate(listing):
            newListing[header[idx]] = value
        newData.append(newListing)
    return newData

def getLegacyArchives(URLentry:list):
    """Gets all archive listings from before the project token update (pre-2022)"""
    if len(URLentry) != 1:
        return []

    newData = []
    URLentry = URLentry[0]
    startYear = int(time.strftime('%Y', time.strptime(URLentry['timestamp'], '%Y%m%d%H%M%S')))
    endYear = int(time.strftime('%Y',time.strptime(URLentry['endtimestamp'], '%Y%m%d%H%M%S')))
    for year in range(startYear, endYear+1):
        print(f'Getting list of archives from {year}...')
        yearData = fetchArchiveData(f'http://web.archive.org/__wb/calendarcaptures/2?url={URLentry['original']}&date={year}')
        for archive in yearData['items']:
            if (archive[1] == '-') or (400 <= int(archive[1]) < 600):
                # Ignore archives with a status code of 4** or 5** (failure), or unspecified ("-")
                pass
            else:
                newEntry = {'original':'', 'timestamp':'', 'uniqcount':'', 'collections':[]}
                newEntry['original'] = URLentry['original']
                newEntry['timestamp'] = str(year) + str(archive[0]).zfill(10)
                newEntry['uniqcount'] = '1'
                newEntry['collections'] = yearData['colls'][int(archive[2])]
                newData.append(newEntry)
    return newData


def getArchivesForProject(projectID:str):
    print('Getting metadata about archives made before mid-2022...')
    dataDirect = fetchArchiveData(f'http://web.archive.org/web/timemap/json?url=https://projects.scratch.mit.edu/{projectID}&collapse=urlkey&matchType=exact&output=json&fl=original,timestamp,endtimestamp&filter=!statuscode:[45]..&limit=1')
    directEntry = formatData(dataDirect)
    directListing = getLegacyArchives(directEntry)

    print('Getting list of archives made after mid-2022...')
    dataTokens = fetchArchiveData(f'http://web.archive.org/web/timemap/json?url=https://projects.scratch.mit.edu/{projectID}?token&collapse=urlkey&matchType=prefix&output=json&fl=original,timestamp&filter=!statuscode:[45]..&limit=10000')
    tokenListing = formatData(dataTokens)

    listing = directListing + tokenListing
    listing = sorted(listing, key=lambda d: d['timestamp'])
    return listing

def mainLoop():
    currentProject = input('Enter a project link or ID to lookup (CTRL+C to exit): ')
    if 'scratch.mit.edu' in currentProject:
        currentProject = re.search(r'scratch\.mit\.edu\/projects\/(\d*)', currentProject)
        if currentProject == None:
            print('Invalid project link!')
            return
        else:
            currentProject = currentProject.group(1)
    elif re.search(r'\D', currentProject) != None:
        print('Invalid project ID!')
        return
    print(f'Getting list of archives for project ID {currentProject}...')
    listing = getArchivesForProject(currentProject)
    padding = len(str(len(listing)))
    print()

    if len(listing) == 0:
        print('There are no saved archives of this project. Preserve this project by archiving the following URL with a valid project token:')
        print(f'https://projects.scratch.mit.edu/{currentProject}')
        return

    print(f'Archived versions of project ID {currentProject}:')
    for idx, project in enumerate(listing):
        print(f'{str(idx+1).zfill(padding)}', end='')
        print(f' - {time.strftime('%m/%d/%Y %I:%M %p', time.strptime(project['timestamp'], '%Y%m%d%H%M%S'))}', end='')
        if 'collections' in project:
            print(f' (why: { ', '.join(project['collections'])})', end='')
        print()
    print()

    chosenArchive = listing[int(input('Which version to download? '))-1]
    autoFileName = f'{currentProject}_{chosenArchive['timestamp']}.sb3'
    fileName = input(f'Enter filename (default: {autoFileName}): ')
    if len(fileName) == 0:
        fileName = autoFileName
    print(f'Downloading project to {fileName}...')
    with open(fileName, 'w+b') as f:
        r = requestSession.get(f'http://web.archive.org/web/{chosenArchive['timestamp']}if_/{chosenArchive['original']}')
        f.write(r.content)
    print('Done! This file only has the "project.json", meaning that none of the assets are in the project file.')
    print('Open it in one of the below programs with an internet connection, then re-save it to make an offline copy:')
    print('  - Scratch website editor (not desktop)')
    print('  - TurboWarp editor (website or desktop)')

if __name__ == '__main__':
    try:
        print('Scratch Time Machine')
        print('Made by Mrk20200')
        print('Powered by the Internet Archive\'s Wayback Machine!')
        print()
        while True:
            mainLoop()
            print()
    except KeyboardInterrupt:
        exit()