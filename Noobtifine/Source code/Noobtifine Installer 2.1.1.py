import os, sys, shutil, pathvalidate, time
from datetime import datetime

from github import Github
from github import Auth
from github import GithubException
from urllib.request import urlretrieve
from zipfile import ZipFile

import requests

##################################[ Load Environment Variables]##########################

def resource_path(relative_path): #handle multiple files in pyinstaller onefile
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

from dotenv import load_dotenv
load_dotenv(resource_path('.env')) #load environment variables
GITHUB_TOKEN: str = os.getenv('GITHUB_TOKEN')

##################################[ github repo & auth ]#################################
auth = Auth.Token(GITHUB_TOKEN) #login as dummy github account
g = Github(auth=auth)
try:
    g.get_user().login
except requests.exceptions.ConnectionError as e:
    print(f'Connection Failed, please connect to the internet \n\nError:\n{e}')
    input('Press enter to exit')
    exit()
except GithubException as e:
    if e.status == 401:
        print('Bad credentials, please update your installer or contact developer (Blinear)')
        input('Press enter to exit')
repo = g.get_repo("blinear/personal-mc-repo")
##################################[ UI ]#################################
print('''Noobtifine installer 2.1.1
Online based installer
but... I still can't make time to learn UI/UX
''')
##################################[ global var]##############################

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

appdataRoaming =os.getenv('APPDATA')
launcher = ''
instanceFolder = ''
workdir = os.path.join(application_path, "Noobtifine")
mcFolder = os.path.join(appdataRoaming, ".minecraft")

Optional_feature = []


##################################[ Logic ]#################################
def main():
    global launcher, mcFolder,instanceFolder,Optional_feature
    if not os.path.exists(workdir):
        os.makedirs(workdir)
    launcher = getLauncher()
    mcFolder = getMCFolderLocation()
    instanceFolder = getInstanceFolderLocation()
    Optional_feature = fetchLatest_optionalFeatures()
    chooseRelease()
    for i in range(len(Optional_feature)):
        chooseOptional(i)
    downloadRelease()
    for i in range(len(Optional_feature)):
        downloadOptional(i)
    installRelease()
    installOptional()
    downloadPostLaunch()
    postInstallation()

def fetchLatest_postLaunchRevision():
    url = 'https://raw.githubusercontent.com/Blinear/personal-mc-repo/main/Noobtifine/postLaunchRevisionLatest.txt'
    req = requests.get(url)
    filecontent = req.text
    output = filecontent.split(".zip")[0]+".zip" #cut anything in the file after first .zip
    return(output)
def fetchLatest_optionalFeatures():
    url = 'https://raw.githubusercontent.com/Blinear/personal-mc-repo/main/Noobtifine/optionalFeatures.txt'
    req = requests.get(url)
    filecontent = req.text
    output = filecontent.split('\n')
    return output
def getLauncher():
    supportedLaunchers = [
        "Official Launcher",
        "SKLauncher",
        "MultiMC",
        "TLauncher"
    ]

    print('Select launcher:')
    for id,val in enumerate(supportedLaunchers):
        print(f'{id+1}.) {val}')
    print('Leave blank & press enter if unlisted')
    n = input("Enter number: ")
    if n == '': return "other"
    launcher = supportedLaunchers[int(n)-1]
    return launcher
def getMCFolderLocation():
    printSeparator()
    print('\nInsert .minecraft folder location')
    print("*if you've never changed this, chances are its still default.")
    print('leave blank & press enter for default ', '('+mcFolder+')')
    tmpIn = str(input("Folder location: "))
    if tmpIn == "": tmpIn = mcFolder
    tmpIn = tmpIn.replace('"', '')
    if tmpIn != '': 
        try: #check path validity
            pathvalidate.validate_filepath(tmpIn[2:])
        except pathvalidate.ValidationError as e:
            print('\npath invalid, please try again\n')
            print(tmpIn)
            closeProgram()
    return tmpIn
def getInstanceFolderLocation():
    instanceFolder = mcFolder
    if (launcher == 'TLauncher') or (launcher == 'MultiMC'):
        return instanceFolder
    printSeparator()
    match launcher:
        case "Official Launcher":
            print("Insert your intended installation's game directory")
        case "SKLauncher":
            print("Insert your intended profile's game directory")
        case _: #for launchers except the above
            print('Insert your game directory')
    print("*if you've never changed this, chances are its still default.")
    print('leave blank & press enter for default', '('+instanceFolder+')')
    tmpIn = str(input("Folder location: "))
    tmpIn = tmpIn.replace('"', '')
    if tmpIn != '': 
        instanceFolder=tmpIn
        try: #check path validity
            pathvalidate.validate_filepath(instanceFolder[2:])
        except pathvalidate.ValidationError as e:
            print('\npath invalid, please try again\n') 
            print(instanceFolder)
            closeProgram()
    return instanceFolder
def chooseRelease():
    global Release_filename, Release_filePath, Release_folder
    print("Choose version to install:")
    Release_filePath = chooseContent(chooseContent("/Noobtifine/Releases"))
    Release_filename = getFilename(Release_filePath)
    Release_folder = Release_filename[:len(Release_filename)-4]
def downloadRelease():
    printSeparator()
    if os.path.exists(os.path.join(workdir,Release_folder)): 
        return #skip download if requested noobtifine version already exist
    
    print("Downloading Release...")
    tmpFileLocation = os.path.join(workdir,"tmp.zip")
    downloadGithubFile(Release_filePath,tmpFileLocation)
    print("Unzipping...")
    unzip(tmpFileLocation,workdir)
    os.remove(tmpFileLocation)
def chooseOptional(idx):
    global Optional_feature
    # printSeparator()
    Optional_filePath = f'/Noobtifine/Optional/{Optional_feature[idx]}/{Release_filename}'
    
    if checkGithubFile_isExist(Optional_filePath) == False:
        Optional_feature[idx] = False
        return #skip if optional feature for selected noobtifne version doesn't exist
    
    print(f'Would you like to add {Optional_feature[idx]}? (Optional)\nanswer with: y/N')
    yn = input().lower()
    if yn != 'y':
        Optional_feature[idx] = False
        return
def downloadOptional(idx):
    if Optional_feature[idx] == False:
        return
    Optional_filePath = f'/Noobtifine/Optional/{Optional_feature[idx]}/{Release_filename}'
    localDir = os.path.join(workdir,"Optional",Optional_feature[idx])
    if os.path.exists(os.path.join(localDir,Release_folder)): 
        return #skip download if requested noobtifine version already exist
    
    print(f'Downloading {Optional_feature[idx]}...')
    tmpFileLocation = os.path.join(workdir,"tmp.zip")
    downloadGithubFile(Optional_filePath,tmpFileLocation)
    print("Unzipping...")
    unzip(tmpFileLocation,localDir)
    os.remove(tmpFileLocation)
    
    
def downloadPostLaunch():
    global PostLaunch_folder
    postLaunchRevision = fetchLatest_postLaunchRevision()
    PostLaunch_filePath = f'/Noobtifine/{postLaunchRevision}'
    PostLaunch_filename = getFilename(PostLaunch_filePath)
    PostLaunch_folder = PostLaunch_filename[:len(PostLaunch_filename)-4]

    if os.path.exists(os.path.join(workdir,PostLaunch_folder)): 
        return #skip download if requested postlaunch already exist
    
    print("Downloading post launch...")
    tmpFileLocation = os.path.join(workdir,"tmp.zip")
    downloadGithubFile(PostLaunch_filePath,tmpFileLocation)
    print("Unzipping...")
    unzip(tmpFileLocation,workdir)
    os.remove(tmpFileLocation)
    print('Installation completed.')
def installRelease():
    printSeparator()
    print('Installing Noobtifine...')

    mod_src = os.path.join(workdir, Release_folder,'Noobtifine')
    mod_dst = os.path.join(instanceFolder, "mods")
    shaderpacks_src = os.path.join(workdir, Release_folder,'shaderpacks')
    shaderpacks_dst = os.path.join(instanceFolder, 'shaderpacks')
    modLoaderVersion_src = os.path.join(workdir, Release_folder, 'versions')
    modLoaderVersion_dst = os.path.join(mcFolder, 'versions')

    if (os.path.exists(mod_dst)):
        os.rename(mod_dst, mod_dst +' Backup '+ str(datetime.now().strftime("%d-%m-%Y %Hh %Mm %Ss")))

    try: 
        shutil.copytree(mod_src, mod_dst, dirs_exist_ok=True)
        shutil.copytree(shaderpacks_src, shaderpacks_dst, dirs_exist_ok=True)
        if (launcher != 'MultiMC'):
            shutil.copytree(modLoaderVersion_src, modLoaderVersion_dst, dirs_exist_ok=True)
    except FileNotFoundError:
        print('source path invalid')
        print(mod_src)
        print(mod_dst)
        print(shaderpacks_src)
        print(shaderpacks_dst)
        print(modLoaderVersion_src)
        print(modLoaderVersion_dst)
        closeProgram()

    print('Install complete.')
def installOptional():
    for i in range(len(Optional_feature)):
        if Optional_feature[i] == False:
            continue
        print(f'Installing {Optional_feature[i]}...')

        localDir = os.path.join(workdir,"Optional",Optional_feature[i])
        mod_src = os.path.join(localDir,Release_folder)
        mod_dst = os.path.join(instanceFolder, "mods")

        try: 
            shutil.copytree(mod_src, mod_dst, dirs_exist_ok=True)
        except FileNotFoundError:
            print('source path invalid')
            print(mod_src)
            print(mod_dst)
            closeProgram()

        print('Install complete.')
def postInstallation():
    printSeparator()
    if launcher == '':
        print('To use noobtifine, run minecraft using the appropriate modloader version')
        closeProgram(1)
    print('You will be guided on how to tell the launcher to use Noobtifine on launch')
    closeProgram(0,False)

    postInstallFile = 'manual installation tutorial.txt'
    match launcher:
        case "Official Launcher":
            postInstallFile = 'postInstallMojang.pdf'
        case "SKLauncher":
            postInstallFile = 'postInstallSKLauncher.pdf'
        case "MultiMC":
            postInstallFile = 'postInstallMultiMC.pdf'
        case "TLauncher":
            postInstallFile = 'postInstallTLauncher.pdf'
    helpAssetPath_postInstallFile = os.path.join(workdir,PostLaunch_folder,postInstallFile)
    os.startfile(helpAssetPath_postInstallFile)
    closeProgram(5)


#################################[ Helper Functions ]#################################
def checkGithubFile_isExist(fileLoc):
    try:
        repo.get_contents(fileLoc)
    except GithubException as e:
        if e.status == 404:
            # print(fileLoc, "doesn't exist")
            return False
    return True
def getFilename(filePath):
    prefixCut = filePath.rfind("/")+1
    return filePath[prefixCut:]
def downloadGithubFile(fileLoc,output="tmp.zip"):
    contents = repo.get_contents(fileLoc).download_url
    urlretrieve(contents,output)
def chooseContent(target):
    contents = repo.get_contents(target)
    contents.reverse()
    contentArray = []
    i = 1
    for content_file in contents:
        tmp = str(content_file)
        prefixCut = tmp.rfind("/")+1
        suffixCut = len(tmp)-2
        content = tmp[prefixCut:suffixCut]
        print(f'{i}.) {content}')
        contentArray.append(content)
        i += 1
    n = int(input("Enter number: "))
    chosen = f'{target}/{contentArray[n-1]}'
    return chosen
def unzip(file,workdir=''):
    with ZipFile(file, 'r') as myzip:
        myzip.extractall(workdir)
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')
def closeProgram(wait=5,Exit=True): #optional to assign argument, wait = 5 if argument is unspecified
    time.sleep(wait)
    if Exit == True:
        input('press enter to exit')
        exit()
    else: input('press enter to continue')
def printSeparator():
    print("\n_____________________________________________________________________________\n")

main()