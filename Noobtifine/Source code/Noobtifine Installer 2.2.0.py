import os, sys, shutil, pathvalidate, time
from datetime import datetime
from dotenv import load_dotenv
import json

from github import Github
from github import Auth
from github import GithubException
from urllib.request import urlretrieve

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

if getattr(sys, 'frozen', False): #get application path
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)


load_dotenv(resource_path('.env')) #load environment variables
GITHUB_TOKEN: str = os.getenv('GITHUB_TOKEN')

##################################[ github repo & auth ]#################################
print('Connecting...')
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
def startUI():
    clear()
    print('''Noobtifine installer 2.2.0
    Online based installer
    but... I still can't make time to learn UI/UX
    ''')
##################################[ global var & load config ]##############################

appdataRoaming =os.getenv('APPDATA')
workdir = os.path.join(application_path, "Noobtifine")
if not os.path.exists(workdir): os.makedirs(workdir) #make sure workdir exist

supportedLaunchers = [
        "Official Launcher",
        "SKLauncher",
        "MultiMC",
        "TLauncher"
    ]

### load configs ###
config = {}
configFile = 'config.json'
configPath = os.path.join(workdir,configFile)

def updateConfig():
    # global mcFolder,launcher,instanceFolder,noobtifineVariantPreference
    
    config['DIR']['mcFolder'] = mcFolder
    config['LAUNCHER']['launcher'] = launcher
    config['DIR']['instanceFolder'] = instanceFolder
    config['NOOBTIFINE_PREFERENCE']['variant']=noobtifineVariantPreference
    
    with open(configPath, 'w') as f:
        json.dump(config,f,indent=4)
def generateConfig():
    config['DIR'] = {
        "mcFolder": os.path.join(appdataRoaming, ".minecraft"),
        "instanceFolder": os.path.join(appdataRoaming, ".minecraft")
    }
    config['LAUNCHER'] = {
        "launcher": "Official Launcher",
    }
    config['NOOBTIFINE_PREFERENCE'] = {
        "variant": 'Core'
    }
    with open(configPath, 'w') as f:
        json.dump(config,f,indent=4)

def modCfgInit():
    modCfgFile = "noobtifine_mod_cfg.json"
    modCfgPath = os.path.join(workdir,Release_version,'Noobtifine',modCfgFile)
    return modCfgFile,modCfgPath

if not os.path.exists(configPath): generateConfig()

with open(configPath) as f:
    config = json.load(f)
mcFolder = config['DIR']['mcFolder']
instanceFolder = config['DIR']['instanceFolder']
launcher = config['LAUNCHER']['launcher']
noobtifineVariantPreference = config['NOOBTIFINE_PREFERENCE']['variant']

##################################[ Main Loop ]#################################
def main():
    #set every variable used/assigned in main loop as global
    global launcher, mcFolder,instanceFolder,supportedOptionalFeatures,supportedOptionalFeaturesPath,Release_filename,Release_version,Release_filePath,variant,variantPath,chosenOptionalFeatures, noobtifineVariantPreference,chosenOptionalFeaturesPath,Noobtifine_version, modCfgFile,modCfgPath

    startUI()

    launcher = promptLauncher()
    mcFolder = promptMCFolderLocation()
    instanceFolder = promptInstanceFolderLocation()

    Release_filename,Release_version,Noobtifine_version,Release_filePath,variant,variantPath = chooseRelease()
    noobtifineVariantPreference = variant

    supportedOptionalFeatures,supportedOptionalFeaturesPath = fetchSupportedOptionalFeatures(Release_version)

    chosenOptionalFeatures,chosenOptionalFeaturesPath = chooseOptionalFeatures(supportedOptionalFeatures)

    modCfgFile,modCfgPath = modCfgInit()
    downloadRelease(Release_version,Release_filePath)
    mergeCore() #because other variants are additions to core variant
    downloadOptionalFeatures(chosenOptionalFeatures,chosenOptionalFeaturesPath)

    installRelease()
    installOptionalFeatures()
    
    updateConfig()
    downloadPostLaunch()
    postInstallation()
    closeProgram(5)

def fetchLatest_postLaunchRevision():
    url = 'https://raw.githubusercontent.com/Blinear/personal-mc-repo/main/Noobtifine/postLaunchRevisionLatest.txt'
    req = requests.get(url)
    filecontent = req.text
    output = filecontent.split(".zip")[0]+".zip" #cut anything in the file after first .zip
    return(output)

def fetchSupportedOptionalFeatures(Release_version):
    supportedFeatures = []
    supportedFeaturesPath = []
    optionalFeaturesArray, optionalFeaturesPathArray = fetchContent('/Noobtifine/Optional')
    for i,x in enumerate(optionalFeaturesPathArray):
        versionsFile = fetchContent(x)[0] 
        for versionFile in versionsFile:
            version = versionFile[:len(versionFile)-4]
            if version == Release_version:
                supportedFeaturesPath.append(x)
                supportedFeatures.append(optionalFeaturesArray[i])

    return supportedFeatures, supportedFeaturesPath

def promptLauncher():
    global supportedLaunchers, launcher
    
    print('Select launcher:')
    for id,val in enumerate(supportedLaunchers):
        if val == 'MultiMC': val = 'MultiMC or its forks (eg. UltimMC, PolyMC, PollyMC, PrismLauncher)'
        print(f'{id+1}. {val}')
    print(f'Enter 0 if unlisted, leave blank for default ({launcher})')
    n = input("Enter number: ")
    if n == '0': return "other"
    if n == '': return launcher
    launcher = supportedLaunchers[int(n)-1]
    return launcher

def promptMCFolderLocation():
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

def promptInstanceFolderLocation():
    global instanceFolder

    if (launcher == 'TLauncher') or (launcher == 'MultiMC'):
        instanceFolder = mcFolder
        return instanceFolder
    printSeparator()
    match launcher:
        case "Official Launcher":
            print("Insert your intended installation's game directory")
        case "SKLauncher":
            print("Insert your intended profile's game directory")
        case _: #for launchers except the above
            print('Insert your game directory')
    print("*if you've never changed this, its probably the same as .minecraft folder")
    print(f'leave blank & press enter for default, ({instanceFolder})')
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
    print("Choose variant to install:")
    if noobtifineVariantPreference == 'Original':defaultVariant = 1
    elif noobtifineVariantPreference == 'Extended': defaultVariant = 2
    elif noobtifineVariantPreference == 'Core': defaultVariant = 3
    else: defaultVariant = 3

    variant,variantPath = chooseContent("/Noobtifine/Releases",defaultVariant)
    Release_filename,Release_filePath = chooseContent(variantPath,1) #Defaults to latest version
    Release_version = Release_filename[:len(Release_filename)-4]
    Noobtifine_version = Release_version[Release_version.find("mc"):]
    return Release_filename,Release_version,Noobtifine_version,Release_filePath,variant,variantPath

def downloadRelease(Release_version,Release_filePath):

    if os.path.exists(os.path.join(workdir,Release_version)): 
        return #skip download if requested noobtifine version already exist
        
    printSeparator()
    print("Downloading Release...")
    tmpFilePath = os.path.join(workdir,"tmp.zip")
    tmpExtractPath = os.path.join(workdir,"tmp")
    os.makedirs(tmpExtractPath, exist_ok=True)

    downloadGithubFile(Release_filePath,tmpFilePath)
    print("Unzipping...")
    unzip(tmpFilePath,tmpExtractPath)
    
    if os.path.exists(os.path.join(tmpExtractPath,Release_version)): 
        #backwards compatibility for older zip structure
        shutil.move(os.path.join(tmpExtractPath,Release_version),os.path.join(workdir,Release_version)) 
        shutil.rmtree(tmpExtractPath)
    else:
        shutil.move(tmpExtractPath,os.path.join(workdir,Release_version))
    
    os.remove(tmpFilePath)  

    modCfg = {}
    modCfg['variant'] = variant
    with open(modCfgPath, 'w') as f:
        json.dump(modCfg,f,indent=4)

def mergeCore():
    Core_version = f'Noobtifine Core {Noobtifine_version}'
    Core_variantPath = "/Noobtifine/Releases/Core" 
    if Release_version == Core_version: 
        
        return
    if checkGithubFile_isExist(f'{Core_variantPath}/{Core_version}.zip') == False: return #backwards compatibility

    modCfg = {}
    if os.path.exists(modCfgPath):
        with open(modCfgPath) as f:
            modCfg = json.load(f)
        
    if modCfg.get('coreMerged') == True: return
    else: modCfg['coreMerged'] = False

   
    Core_filename = f'{Core_version}.zip'
    Core_filePath = f'{Core_variantPath}/{Core_filename}'
    if not os.path.exists(os.path.join(workdir,Core_version)): downloadRelease(Core_version,Core_filePath) #download core variant

    #merge core with variant
    shutil.copytree(os.path.join(workdir,Core_version), os.path.join(workdir,Release_version), dirs_exist_ok=True)

    modCfg['coreMerged'] = True
    with open(modCfgPath, 'w') as f:
        json.dump(modCfg,f,indent=4)

def chooseOptionalFeatures(supportedOptionalFeatures):
    printSeparator()
    chosenOptionalFeatures = []
    chosenOptionalFeaturesPath = []
    for i,x in enumerate(supportedOptionalFeatures):
        print(f'Would you like to add {x}? (Optional)\ntype: y or n')
        yn = input().lower()
        if yn == 'y':
            chosenOptionalFeatures.append(x)
            chosenOptionalFeaturesPath.append(supportedOptionalFeaturesPath[i])
    return chosenOptionalFeatures,chosenOptionalFeaturesPath

def downloadOptionalFeatures(chosenOptionalFeatures,chosenOptionalFeaturesPath):
    tmpFilePath = os.path.join(workdir,'tmp.zip')
    tmpExtractPath = os.path.join(workdir,"tmp")
    for i,x in enumerate(chosenOptionalFeatures):
        featureDirPath = os.path.join(workdir,"Optional",x)
        os.makedirs(featureDirPath, exist_ok=True)
        if os.path.exists(os.path.join(featureDirPath,Release_version)): #skip download if already downloaded
            continue
    
        print(f'Downloading {x}...')
        downloadGithubFile(f'{chosenOptionalFeaturesPath[i]}/{Release_filename}',tmpFilePath)
        print("Unzipping...")
        unzip(tmpFilePath,tmpExtractPath)
        if os.path.exists(os.path.join(tmpExtractPath,Release_version)): 
            #backwards compatibility for older zip structure
            shutil.move(os.path.join(tmpExtractPath,Release_version),os.path.join(featureDirPath,Release_version))
            shutil.rmtree(tmpExtractPath)
        else:
            shutil.move(tmpExtractPath,os.path.join(featureDirPath,Release_version))
        os.remove(tmpFilePath)            

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

    mod_src = os.path.join(workdir, Release_version,'Noobtifine')
    mod_dst = os.path.join(instanceFolder, "mods")
    shaderpacks_src = os.path.join(workdir, Release_version,'shaderpacks')
    shaderpacks_dst = os.path.join(instanceFolder, 'shaderpacks')
    modLoaderVersion_src = os.path.join(workdir, Release_version, 'versions')
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

def installOptionalFeatures():
    mod_dst = os.path.join(instanceFolder, "mods")
    if not os.path.exists(modCfgPath): #create json if not exist
        with open(os.path.join(mod_dst,modCfgFile), 'w') as f: 
            modCfg = {}
            modCfg['optionalFeature'] = []
            json.dump(modCfg,f,indent=4)
    with open(os.path.join(mod_dst,modCfgFile), 'r') as f: modCfg = json.load(f) #load modcfg in installed mods directory
    modCfg['optionalFeature'] = []
    for x in chosenOptionalFeatures:
        print(f'Installing {x}...')

        featureDirPath = os.path.join(workdir,"Optional",x)
        compatPath = os.path.join(featureDirPath,Release_version,'compatibility.json')
        if os.path.exists(compatPath):
            mod_src = os.path.join(featureDirPath,Release_version, "mods")
            with open(compatPath) as f:
                compatFile = json.load(f)
            for y in compatFile['INCOMPATIBILITY']['remove']:
                os.remove(os.path.join(mod_dst,y))
        else:#backwards compatibility for older optionalfeature zip structure
            mod_src = os.path.join(featureDirPath,Release_version)

        try: 
            shutil.copytree(mod_src, mod_dst, dirs_exist_ok=True)
        except FileNotFoundError:
            print('source path invalid')
            print(mod_src)
            print(mod_dst)
            closeProgram()
        modCfg['optionalFeature'].append(x) #append optional feature
        print('Install complete.')
    with open(os.path.join(mod_dst,modCfgFile), 'w') as f: json.dump(modCfg,f,indent=4) #update modcfg in installed mods directory

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
    contents = repo.get_contents(fileLoc).download_url.replace(' ','%20')
    urlretrieve(contents,output)

def fetchContent(target):
    contents = repo.get_contents(target)
    contents.reverse()
    contentArray = []
    contentPathArray = []
    i = 1
    for content_file in contents:
        tmp = str(content_file)
        prefixCut = tmp.rfind("/")+1
        suffixCut = len(tmp)-2
        content = tmp[prefixCut:suffixCut]
        contentPath = f'{target}/{content}'
        contentArray.append(content)
        contentPathArray.append(contentPath)
        i += 1
    return contentArray, contentPathArray

def chooseContent(target,defaultChoice=''):
    contentArray,contentPathArray = fetchContent(target)
    for id,x in enumerate(contentArray,1):
        print(f'{id}. {x}')
    
    if defaultChoice == '': n = int(input("Enter number: "))
    else: #has default parameter
        print(f'leave blank & press enter for default ({contentArray[defaultChoice-1]})')
        n = input(f"Enter number: ")
        if n == '': n = int(defaultChoice) 
        else: n = int(n)

    chosen = contentArray[n-1]
    chosenPath = contentPathArray[n-1]
    return chosen, chosenPath

def unzip(file,workdir=''):
    shutil.unpack_archive(file,workdir)

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