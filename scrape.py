''' Created by Boris Manashirov '''

from bs4 import BeautifulSoup
import requests
import re
import threading

url = 'https://en.wikipedia.org/wiki/List_of_animal_names' 
res = requests.get(url) 

# Parse the html using beautifulsoup
soup = BeautifulSoup(res.text, 'html.parser')

# Get only the relevant table
tb = soup.find_all('tbody')[2]

# Find <tr> tags that hold the information 
raw_tr_list = tb.find_all('tr')
# Slice redundant tags
tr_list = raw_tr_list[2:]

# Loop over tr_list and build dict of collateral adjectives and animals
# Also build dict of animals wiki url for further image extraction
result_dict = {}
href_dict = {}
for tr in tr_list:
    # Get animal's name - check for empty lines
    if(tr.td):
        animal_name = tr.td.a.text
        href_dict[animal_name] = tr.td.a.get('href')
    # Use css selector for collateral adjective
    col_adj = tr.select_one('td:nth-of-type(6)')
    if(col_adj):
        # Clean text from [] or () using regex
        col_adj_names = re.sub('\[.*\]', '', col_adj.text)
        col_adj_names = re.sub('\(.*\)', '', col_adj_names)
        # Split collateral adjectives when there is more than one per animal
        col_adj_names = col_adj_names.split()
        # Running on the collateral adjectives array (if there is more than one)
        for name in col_adj_names:
            # Rename '?' from wiki to UNKNOWN collateral adjective
            name = re.sub('\?', 'UNKNOWN', name)
            if name in result_dict:
                result_dict[name].append(animal_name)
            else:
                result_dict[name] = [animal_name]

# Function that gets image url link and the sends link to function that download and stores it
def get_link_and_download(animal_wiki_url, animal_name, href_dict):
    res = requests.get('https://en.wikipedia.org' + animal_wiki_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    a = soup.find('a', class_ = 'image')
    if(a) :
        img_link = a.img.get('src')
    else :
        infobox = soup.find('table', class_ = 'infobox')
        img_link = infobox.tbody.tr.next_sibling.next_sibling.a.img.get('src')
    download_and_store_img(img_link, animal_name, href_dict)

def download_and_store_img(img_link, animal_name, href_dict):
    res = requests.get('https:' + img_link)
    local_address = './tmp/'+ re.sub('\/', '', animal_name) +'.jpg'
    href_dict[animal_name] = local_address
    with open(local_address, 'wb') as f:
        f.write(res.content)

# Keep a list for threads for later .join()
threads = []

# Start threading
for animal_name, animal_wiki_url in href_dict.items():
    t = threading.Thread(target=get_link_and_download, args=[animal_wiki_url, animal_name, href_dict])
    t.start()
    threads.append(t)

for t in threads:
    t.join()

# Print all of the collateral adjectives and all of the animals which belong to it
# If an animal has more than one collateral adjective, it will be mentioned more than once
for col_adj, animal_name in result_dict.items():
    print('Collateral adjective:', col_adj)
    print('-------------------------------')
    for animal in animal_name:
        print('The animals which belong to it: ', animal)
        print('The local link to: ' + animal + ' is: ', href_dict[animal] + '\n')