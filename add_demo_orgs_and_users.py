import zipfile
import requests
import csv
import argparse


url = "https://www.briandunning.com/sample-data/us-500.zip"
USERNAME = "<user name>"
API_TOKEN = "<API token>"
ZENDESK_URL = "<instance URL>"

def getDemoContentFile():
    try:
        r = requests.get(url, allow_redirects=True)
        print(f"Successfully downloaded the source file {url}")

    except:
        print(f"Error. Cannot access the source file initially located at {url}")
        exit()

    if r.status_code == 200:
        open('us-500_TST.zip', 'wb').write(r.content)
        with zipfile.ZipFile('us-500_TST.zip', 'r') as zip:
            zip.printdir()
            zip.extractall()
            file_list = zip.namelist()
            # print(file_list)
            if "us-500.csv" in file_list:
                print("Data was successfully extracted.")

def loadData(fileName):
    with open(fileName, newline='') as sourcefile:
        csv_reader = csv.reader(sourcefile, delimiter=',', quotechar='"')
        orgs ={}
        users = {}
        x=0
        for line in csv_reader:
            lineArray = line
            if x>0: #to avoid the header of the file
                # print(lineArray)
                orgs[x] = {'name':lineArray[2].replace('"',''),'domain_names':[lineArray[11].replace('"','').replace('http://','')]}
                users[x] = {"name":lineArray[0].replace('"','')+' '+lineArray[1].replace('"',''),"email":lineArray[10].replace('"','')}
            x=x+1
        # print("org::",orgs)
        # print(json.dumps(orgs,indent=4))
        # print("org200::",orgs[200])
        # print("user200::",users[1])
        return {"data":{"users":users,"orgs":orgs}}

def addToZendesk(endpoint,info):
    headers = {'content-type': 'application/json'}
    data = {endpoint:info}
    try:
        post_response = requests.request("POST", ZENDESK_URL+"/api/v2/"+endpoint+"s", auth=(USERNAME + '/token',API_TOKEN), headers=headers, json=data)
        # print(str(post_response.status_code),post_response.content)
        if post_response.status_code!=201 and post_response.status_code!=422:
            print("Zendesk reponded: ",post_response,post_response.content)
            exit()
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")

    if post_response.status_code == 200 or post_response.status_code == 201:
        print(f"\n{endpoint.capitalize()} '{post_response.json().get(endpoint,0).get('name',0)}' successfully added.")
        #adding to cache
        if endpoint == 'organization':
            org = {"name":post_response.json().get("organization",0).get('name',0),"id":post_response.json().get("organization",0).get('id',0)}
            return post_response.json().get("organization",0).get('id',0)
        if endpoint == 'user':
            return post_response.json().get("user",0).get('id',0)
    else:
        if "'error': 'DuplicateValue'" in str(post_response.json()):
            return -1
        return 0    

print("Starting script")
parser = argparse.ArgumentParser(description="Creating users and organizations in a newly created Zendesk instance.")
parser.add_argument("-o","--numOrgs", help="number of demo organizations to be created (max: 500)",type=int,required=True)
parser.add_argument("-u","--numUsers", help="number of demo users to be created per organization", type=int, required=True) 
parser.add_argument("-v", "--verbose", action="store_true", help="show details of the script")
args = parser.parse_args()
if parser.parse_args().numOrgs:
    if parser.parse_args().numOrgs > 500:
        print("Error: the maximum number of unique demo organizations is 500! Please try again.")
        exit()
    print(f"The number of demo organizations will be {str(parser.parse_args().numOrgs)}")
if parser.parse_args().numUsers:
    if parser.parse_args().numOrgs > 50:
        print("Error: the maximum number of unique users per organization is 50! Please try again.")
        exit()
    print(f"The number of demo users per organization will be {str(parser.parse_args().numUsers)}")
getDemoContentFile() 
demoData = loadData("us-500.csv")     
reqNumOrgs = parser.parse_args().numOrgs
OrgSuccessCounter = 0
orgNum = 0
userNum = 0
addData = True
bar = "\|/-"
i=0
while OrgSuccessCounter < reqNumOrgs:
    print("Processing your request ", bar[i], end="\r")
    i += 1
    if i>3:
        i=0
    orgNum += 1
    resp = addToZendesk("organization",demoData.get('data').get('orgs').get(orgNum))   
    if resp >0:
        OrgSuccessCounter += 1
        UserSuccessCounter = 0
        while UserSuccessCounter < parser.parse_args().numUsers:
            userNum += 1
            demoData.get('data').get('users').get(userNum)['organization_id']=resp
            userResp = addToZendesk("user",demoData.get('data').get('users').get(userNum))   
            if userResp >0:
                UserSuccessCounter += 1



