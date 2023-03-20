import requests, re, asyncio, aiohttp
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup as BS
from flask import Flask, render_template, jsonify, request
import json
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "scraping_eprints"
CORS(app)

url_glob = "http://eprints.uty.ac.id"

@app.route('/api', methods=['GET'])
def index():
    return render_template("index.html")

@app.route('/search', methods=['GET'])
async def search():
    keywoard = request.args.get("keywoard")
    if not keywoard:
        return jsonify({'code':400, 'message':'keywoard cannot be empty'})
    try:
        res = await cari(keywoard)
        return jsonify({'code':200, 'data':res})
    except Exception as e:
        return jsonify({'code':500, 'message': str(e)})

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            task = asyncio.ensure_future(fetch(session, url))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        return responses

async def cari(keywoard):
    data = []
    datares = []
    keywoard = keywoard.replace(" ","+")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{url_glob}/cgi/search/simple?q={keywoard}&_action_search=Search&_action_search=Search&_order=bytitle&basic_srchtype=ALL&_satisfyall=ALL") as res:
            response_text = await res.text()
            search = BS(response_text, "html.parser").find("div", {"class":"ep_search_controls_bottom"})
            search = search.findAll("a")
            data.append(f"{url_glob}/cgi/search/simple?q={keywoard}&_action_search=Search&_action_search=Search&_order=bytitle&basic_srchtype=ALL&_satisfyall=ALL")
            for i in range(len(search)):
                if "Refine search" in search[i].text or "New search" in search[i].text or "Next" in search[i].text:
                    continue
                else:
                    data.append(url_glob+search[i].get("href"))
    results = await fetch_all(data)
    return results

    
async def fetch(session, url):
    async with session.get(url) as response:
        data = []
        res = await response.text()
        search = BS(res, "html.parser").findAll("tr", {"class":"ep_search_result"})
        for i in search:
          author = (i.find("span", {"class":"person_name"}).string if i.find("span", {"class":"person_name"}) != None else "No Name")
          title = ("{}".format(i.find("a").string))
          link = ("{}{}".format(url_glob, i.find("a", {"class":"ep_document_link"}).get("href")))
          filte = await getFilter(i.find("a").get("href"))
          gambar = ("{}{}".format(url_glob, i.find("img", {"class":"ep_doc_icon"}).get("src")))
          data.append({"judul": title,"author": author,"link": link,"gambar": gambar,"tahun":filte[0],"subject":filte[1],"division":filte[2]})
        return data

def carilink(uerel):
    data = []
    res = requests.get(uerel, timeout=60).text
    search = BS(res, "html.parser").findAll("tr", {"class":"ep_search_result"})
    for i in search:
      author = (i.find("span", {"class":"person_name"}).string if i.find("span", {"class":"person_name"}) != None else "No Name")
      title = ("{}".format(i.find("a").string))
      link = ("{}{}".format(url, i.find("a", {"class":"ep_document_link"}).get("href")))
      filte = getFilter(i.find("a").get("href"))
      gambar = ("{}{}".format(url, i.find("img", {"class":"ep_doc_icon"}).get("src")))
      data.append({"judul": title,"author": author,"link": link,"gambar": gambar,"tahun":filte[0],"subject":filte[1],"division":filte[2]})
    return data
    
@app.route('/latest', methods=['GET'])
async def latest():
    data = []
    res = requests.get(f"{url_glob}/cgi/latest", timeout=60).text
    search = BS(res, "html.parser").findAll("div", {"class":"ep_latest_result"})
    for i in search:
      author = (i.find("span", {"class":"person_name"}).string if i.find("span", {"class":"person_name"}) != None else "Universitas Teknologi Yogyakarta")
      title = (i.find("em").text)
      link = await getPdf(i.find("a").get("href"))
      tahun = re.search(r'\([0-9]+\)', str(i))
      tahun = tahun.group() if tahun != None else "Unknown"
      data.append({'author':author, 'title':title, 'tahun':tahun, 'link':link})
    return jsonify({'code':200,'data':data})

async def getPdf(link):
  async with aiohttp.ClientSession() as session:
    async with session.get(link) as response:
      res = await response.text()
  pdf = BS(res, "html.parser").find("a", {"class":"ep_document_link"})
  pdf = pdf.get("href") if pdf != None else "https://one.informaticscapstoneproject.my.id"
  return pdf

async def getFilter(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=60) as response:
            res = await response.text()
            tahun = BS(res, "html.parser").find("p")
            tahun = re.search(r'\([0-9]+\)', str(tahun))
            tahun = tahun.group() if tahun != None else "Unknown"
            all = BS(res, "html.parser").find("table", {"style":"margin-bottom: 1em; margin-top: 1em;"})
            subject = all.findAll("td")[1].text
            divisi = all.findAll("td")[2].text
            data = [tahun, subject, divisi]
            return data

app.run(host='127.0.0.1', port='8080', debug=True)
