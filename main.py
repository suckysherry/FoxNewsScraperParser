from foxnewsScraperParser import *

if __name__ == '__main__':
    start = '20200401'
    end = '20200401'
    keys = ['the']
    logging.basicConfig(level=logging.INFO,
                        filename='output.log',
                        datefmt='%Y/%m/%d %H:%M:%S',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(module)s - %(message)s')
    logger = logging.getLogger(__name__)
    scraper = Scraper(start, end, keys, logger)
    logger.info('Start scraping meta data')
    scraper.scrape_save_meta_data()
    parser = Parser(start, end, keys, logger)
    logger.info('Start parsing and downloading articles and images')
    parser.parse_download_articles()
    logger.info('Finish')
