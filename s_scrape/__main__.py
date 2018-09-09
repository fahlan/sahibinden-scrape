import time
import argparse
from s_scrape.scraping import DetailsScraper, MainPageScraper
from s_scrape.utils import IO

def _scrape_listings(njobs=4, wait=10, mode='standard'):
    print("Total threads: %s"%str(njobs))
    mscr = MainPageScraper(njobs, urlgetmode=mode)
    print("Scraping started...")
    mscr.scrapeModels()
    print("Main car models scraped...")
    mscr.scrapeSubModels()
    print("Sub car models scraped...")
    print("Waiting %d seconds before scraping listings..." %wait)
    time.sleep(wait)
    mscr.scrapeListings()
    return mscr.listings

def _full_scraper(njobs=4, wait = 10, mode='standard'):
    print("Total threads: %s"%str(njobs))
    mscr = MainPageScraper(njobs, urlgetmode=mode)
    print("Scraping started...")
    mscr.scrapeModels()
    print("Main car models scraped...")
    mscr.scrapeSubModels()
    print("Sub car models scraped...")
    print("Waiting %d seconds before scraping listings..." %wait)
    time.sleep(wait)
    mscr.scrapeListings()
    IO.save_list("listings.txt", mscr.listings)
    scr = DetailsScraper(mscr.listings, njobs, urlgetmode=mode)
    print("Waiting %d seconds before scraping listings..." %wait)
    time.sleep(wait)
    scr.scrapeDetails()
    return scr.final_list


def _using_saved_listings(listloc, njobs=4, mode='standard'):
    listings = IO.load_list(listloc)
    scr = DetailsScraper(listings, njobs, urlgetmode=mode)
    scr.scrapeDetails()
    return scr.final_list

parser = argparse.ArgumentParser()

parser.add_argument("--lf",help="""Load listings file for pre-scraped listings.""")
parser.add_argument("--lo",help="""Save listings only and exit.""", action='store_true')
parser.add_argument("--wait",help="""Seconds to wait before sending another request.""", type=int)
parser.add_argument("--nworkers",help="""Number of workers for concurrent processing.""", type=int)
parser.add_argument("--api", help="Sets api mode for URLutils.", action='store_true')
parser.add_argument("--sln", help="Sets selenium mode for URLutils.", action='store_true')

args = parser.parse_args()

if __name__ == "__main__":

    if args.sln and args.api:
        print("Can't set both selenium and api to True, falling back to standard mode.")
        urlmode = 'standard'
    elif args.sln:
        urlmode = 'selenium'
    elif args.api:
        urlmode = 'api'

    if args.lo:
        listings = _scrape_listings(njobs=args.nworkers, wait=args.wait, mode=urlmode)
        print("Listings scraped, saving listings.")
        IO.save_list("listings.txt", listings)
    elif args.lf:
        print("Pre-scraped listings location is given, using list for scraping main details...")
        results = _using_saved_listings(args.lf, njobs=args.nworkers, mode=urlmode)
    else:
        print("<<<-------Starting full scraper------->>>")
        results = _full_scraper(njobs=args.nworkers, wait=args.wait, mode=urlmode)

    try:
        print("Using pandas for easier CSV extraction...")
        import pandas as pd
        import datetime
        now = datetime.datetime.now()
        day = now.day
        month = now.month
        year = now.year
        suffix = str(day)+"-"+str(month)+"-"+str(year)
        #tempfix
        df = [x for x in results if x is not None]
        df = pd.DataFrame(df)
        df.to_csv("listings_"+suffix+".csv", index = False)
    except:
        IO.pickle_dump('listings_list.pkl', scr.final_list)
        print("Scraping & pickling complete.")
