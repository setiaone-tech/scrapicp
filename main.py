import requests, re
from bs4 import BeautifulSoup as BS
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
app.secret_key = "scraping_eprints"

url = "http://eprints.uty.ac.id/"

@app.route('/', methods=['GET'])
def index():
    return "sites is live"

@app.route('/search', methods=['GET'])
def search():
    keywoard = request.args.get("keywoard")
    res = cari(keywoard)
    return jsonify({'code':200, 'data':res})

def cari(keywoard):
    data = []
    keywoard = keywoard.replace(" ","+")
    res = requests.get(f"{url}cgi/search/simple?q={keywoard}&_action_search=Search&_action_search=Search&_order=bytitle&basic_srchtype=ALL&_satisfyall=ALL")
    search = BS(res.text, "html.parser").find("div", {"class":"ep_search_controls_bottom"})
    search = search.findAll("a")
    data.append(carilink(f"{url}cgi/search/simple?q={keywoard}&_action_search=Search&_action_search=Search&_order=bytitle&basic_srchtype=ALL&_satisfyall=ALL"))
    for i in range(len(search)):
        if i > 1  and i < len(search)-1:
            data.append(carilink(url+search[i].get("href")))
    return data

def carilink(uerel):
    data = []
    res = requests.get(uerel).text
    search = BS(res, "html.parser").findAll("tr", {"class":"ep_search_result"})
    for i in search:
      author = (i.find("span", {"class":"person_name"}).string if i.find("span", {"class":"person_name"}) != None else "No Name")
      title = ("{}".format(i.find("a").string))
      link = ("{}".format(i.find("a").get("href")))
      data.append({"judul": title,"author": author,"link": link})
    return data

if '__name__' == '__main__':
    app.run(host='127.0.0.1', port='8080', debug=True)
