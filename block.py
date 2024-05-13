#import requests
#from bs4 import BeautifulSoup
#
#
#agent = "Mozilla%2F5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537" + \
#    ".36+(KHTML%2C+like+Gecko)+Chrome%2F90.0.4430.85+Safari%2F537" + \
#    ".36+RuxitSynthetic%2F1.0+v7014856858959599523+t4743487995012709438" + \
#    "+ath1fb31b7a+altpriv+cvcv%3D2+smf%3D0"
#
#query = "Ray Ridley Ridley Engineering"
#
#search_url = f"https://www.google.com/search?q={query}"
#
#req = requests.get(search_url, agent)
#
#print(req)
#
#content = BeautifulSoup(req.content, 'html.parser')
#
#test = content.find('article')
#print(content.find_all('div'))
#print(content.prettify())
#with open("test.txt", "w") as f:
#    f.write(content.prettify())
#    f.close()

bad_locations = ["google", "facebook", "instagram",
                 "linkedin", "twitter", "ratemyprofessors",
                 "coursicle", "youtube", "amazon",
                ".doc", ".pdf", "wiki", "imgres"]

for b in bad_locations:
    print(b)
