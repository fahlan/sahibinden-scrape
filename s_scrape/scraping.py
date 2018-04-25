from s_scrape.base import Scraper
from s_scrape.base import UPPER_DELAY, LOWER_DELAY
from s_scrape.utils import URLutils

# scraping
from bs4 import BeautifulSoup
from lxml import html
from multiprocessing import Pool

import re


class MainPageScraper(Scraper):
    def __init__(self, n_jobs):
        super().__init__(url="https://www.sahibinden.com/kategori/otomobil")
        self._modelurls = []
        self.submodelurls = []
        self._listings = []
        self.n_jobs = n_jobs

    @property
    def linklist(self):
        return self._modelurls

    @property
    def listings(self):
        return self._listings

    def scrapeModels(self):

        c = URLutils.readURL(self.link)
        soup = BeautifulSoup(c, "html.parser")
        ctgList = soup.find_all("ul", {"class": "categoryList"})
        carList = ctgList[0].find_all("li")

        for car in carList:
            tmp = car.find("a", href=True)
            self._modelurls.append("https://www.sahibinden.com" + tmp['href'] + "?pagingOffset=")

    @classmethod
    def _get_submodels_from_page(self, url):
        sublist = list()
        print("----> Scraping sub-models from url: %s" % (url))
        c = URLutils.delayedreadURL(url, LOWER_DELAY, UPPER_DELAY)
        soup = BeautifulSoup(c, "html.parser")
        subList = soup.find_all("li", {"class": "cl3"})

        for itm in subList:
            tmp = itm.find("a", href=True)
            if tmp['href'] != "#":
                ret_str = "https://www.sahibinden.com" + tmp['href']
                sublist.append(ret_str)
        return sublist

    def scrapeSubModels(self):
        with Pool(self.n_jobs) as pool:
            self.submodelurls = pool.map(self._get_submodels_from_page, self._modelurls)

    @classmethod
    def _get_listings_from_page(self, url):
        try:
            # TODO, check sahibinden.com page structure, can't scrape listings currently
            print("----> Scraping listings from url: %s" % (url))
            c = URLutils.delayedreadURL(url, LOWER_DELAY, UPPER_DELAY)
            soup = BeautifulSoup(c, "html.parser")
            listitems = soup.find_all("tr", {"class": "searchResultsItem"})

            for itm in listitems:
                try:
                    tmp = itm.find("a", href=True)
                    ret_str = "https://www.sahibinden.com" + tmp['href']
                    return ret_str
                except:
                    pass
        except:
            pass

    @classmethod
    def _get_listings_upperlimit(self, link):
        # TODO needs better reading for upplerlimit, possible bottleneck
        c = URLutils.readURL(link)
        xpth = '//*[@id="searchResultsSearchForm"]/div/div[4]/div[1]/div[1]/div/div[1]/span'

        tot = URLutils.choosebyXPath(c, xpth)
        tot = tot.replace(".", "")
        tot = re.findall('\d+',tot)
        tot = int(tot[0])
        rem = tot % 20
        tot = tot + rem
        if tot < 20:
            tot = 20
        return min(tot, 980)

    def scrapeListings(self):
        links = list()

        # flatten submodelurls, list of lists
        flat_list = list()
        for sublist in self.submodelurls:
            for item in sublist:
                flat_list.append(item)

        with Pool(self.n_jobs) as pool:
            for mainlink in flat_list:
                upperlimit = self._get_listings_upperlimit(mainlink)
                print("Upperlimit for link: %s   -->   is %d" % (mainlink, upperlimit))
                for pagingoffset in range(0, upperlimit + 10, 20):
                    link = mainlink + "?pagingOffset=" + str(pagingoffset)
                    links.append(link)
            self._listings = pool.map(self._get_listings_from_page, links)
        print("Listings scraped succesfully...")
        return self._listings


class DetailsScraper(Scraper):
    def __init__(self, listings, n_jobs):

        super().__init__(url="")
        self.listings = listings
        self.final_list = []
        self.n_jobs = n_jobs

        #Xpath references for posting details
        self.ilan_xpath = '//*[@id="classifiedId"]'
        self.ilantarihi_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[2]/span'
        self.marka_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[3]/span'
        self.seri_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[4]/span'
        self.model_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[5]/span'
        self.yil_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[6]/span'
        self.yakit_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[7]/span'
        self.vites_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[8]/span'
        self.km_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[9]/span'
        self.kasatipi_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[10]/span'
        self.motorgucu_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[11]/span'
        self.motorhacmi_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[12]/span'
        self.cekis_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[13]/span'
        self.renk_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[14]/span'
        self.garanti_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[15]/span'
        self.hasar_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[16]/span'
        self.plakauyruk_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[17]/span'
        self.kimden_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[18]/span'
        self.takas_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[19]/span'
        self.durum_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/ul/li[20]/span'

        self.fiyat_xpath = '//*[@id="classifiedDetail"]/div[1]/div[2]/div[2]/h3'

    def _get_details_from_url_xpath(self, url):

        car = {}
        print("----> Using xpath for scraping from url: %s" % url)
        c = URLutils.delayedreadURL(url, LOWER_DELAY, UPPER_DELAY)
        try:
            root = html.fromstring(c)

            car['clsid'] = root.xpath(self.ilan_xpath)[0].text.strip()
            car['IlanTarihi'] = root.xpath(self.ilantarihi_xpath)[0].text.strip()
            car['Marka'] = root.xpath(self.marka_xpath)[0].text.strip()
            car['Seri'] = root.xpath(self.seri_xpath)[0].text.strip()
            car['Model'] = root.xpath(self.model_xpath)[0].text.strip()
            car['Yil'] = root.xpath(self.yil_xpath)[0].text.strip()
            car['Yakit'] = root.xpath(self.yakit_xpath)[0].text.strip()
            car['Vites'] = root.xpath(self.vites_xpath)[0].text.strip()
            car['Km'] = root.xpath(self.km_xpath)[0].text.strip()
            car['Motor Gucu'] = root.xpath(self.motorgucu_xpath)[0].text.strip()
            car['Motor Hacmi'] = root.xpath(self.motorhacmi_xpath)[0].text.strip()
            car['Cekis'] = root.xpath(self.cekis_xpath)[0].text.strip()
            car['Kapi'] = root.xpath(self.kapi_xpath)[0].text.strip()
            car['Renk'] = root.xpath(self.renk_xpath)[0].text.strip()
            car['Garanti'] = root.xpath(self.garanti_xpath)[0].text.strip()
            car['Hasar Durumu'] = root.xpath(self.hasar_xpath)[0].text.strip()
            car['Plaka / Uyruk'] = root.xpath(self.plakauyruk_xpath)[0].text.strip()
            car['Kimden'] = root.xpath(self.kimden_xpath)[0].text.strip()
            car['Takas'] = root.xpath(self.takas_xpath)[0].text.strip()
            car['Durumu'] = root.xpath(self.durum_xpath)[0].text.strip()
            car['Fiyat'] = root.xpath(self.fiyat_xpath)[0].text.strip()
            print(car)
            print(" **** Processing complete **** ")
            return car
        except:
            pass

    def _get_details_from_url(self, url):

        list_dict = {0: 'clsid',
                     1: 'IlanTarihi',
                     2: 'Marka',
                     3: 'Seri',
                     4: 'Model',
                     5: 'Yil',
                     6: 'Yakit',
                     7: 'Vites',
                     8: 'Km',
                     9: 'Motor Gucu',
                     10: 'Motor Hacmi',
                     11: 'Cekis',
                     12: 'Kapi',
                     13: 'Renk',
                     14: 'Garanti',
                     15: 'Hasar Durumu',
                     16: 'Plaka / Uyruk',
                     17: 'Kimden',
                     18: 'Takas',
                     19: 'Durumu'}

        print("----> Scraping car post details from url: %s" % (url))
        c = URLutils.delayedreadURL(url, LOWER_DELAY, UPPER_DELAY)

        try:
            soup = BeautifulSoup(c, "html.parser")
            infoList = soup.find_all("ul", {"class": "classifiedInfoList"})
            li = infoList[0].find_all("li")
            fiyat = soup.find_all("div", {"class": "classifiedInfo"})
            fiyat = fiyat[0].find("h3").text.strip()

            car = {}

            for i, res in enumerate(li):
                car[list_dict.get(i)] = res.find("span").text.strip()
            car['Fiyat'] = fiyat
            print(car)
            print(" **** Processing complete **** ")
            return car
        except:
            pass

    def scrapeDetails(self):
        with Pool(self.n_jobs) as pool:
            results = pool.map(self._get_details_from_url_xpath, self.listings)
        self.final_list = results
