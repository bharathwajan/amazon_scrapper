import scrapy
from urllib.parse import urlencode
import re
import urllib.request
import os    
import mysql.connector

queries=['Laptops with AMD Ryzen 5 processor']
class AmazonSpider(scrapy.Spider):
    name = "amazon"
    def __init__(self):
        self.mydb=mysql.connector.connect(host="localhost",user="root",passwd="root",database="employee_db")
        self.executer = self.mydb.cursor()
        self.executer.execute("use internship_task")

    def start_requests(self):
        for query in queries:
            url = 'https://www.amazon.in/s?' + urlencode({'k': query})
            yield scrapy.Request(url=url, callback = self.parse_keyword_response)

    def parse_keyword_response(self, response):
        products = response.xpath('//*[@data-asin]') 
        print(products)
        for product in products:
            asin = product.xpath('@data-asin').extract_first()  
            # print("#########ASIN##########",asin)   #ASIN ------> amazon standard identification number
            product_url = f"https://www.amazon.in/dp/{asin}"
            yield scrapy.Request(url=product_url, callback=self.parse_product_page, meta={'asin': asin}) #meta can be considered as a dictionary passed as an argument

    def parse_product_page(self, response): 
        asin = response.meta['asin']
        product_url=f"https://www.amazon.in/dp/{asin}"
        title = response.xpath('//*[@id="productTitle"]/text()').extract_first()
        rating = response.xpath('//*[@id="acrPopover"]/@title').extract_first()
        price=response.xpath('//*[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span[2]/span[1]/text()').extract()
        about_product = response.xpath('//*[@id="feature-bullets"]//li/span/text()').extract() #// li represents all li tags
        published_date=response.xpath('//*[@id="productDetails_detailBullets_sections1"]/tbody/tr[4]/td/text()').extract_first()
        if published_date==None:
            published_date="NULL"
        image_url=response.xpath('//*[@id="imgTagWrapperId"]/img/@src').extract_first() 
        exp="[a-zA-Z0-9]+"
        path="images/"+" ".join(re.findall(exp,title))[:10]+"/"
        path_imgname = path+f"{title[0:11]}.jpg"
        try:
            os.makedirs(path)
            urllib.request.urlretrieve(image_url , path_imgname)
        except:
            path_imgname=path+f"{title[0:11]}(1).jpg"
            urllib.request.urlretrieve(image_url , path_imgname)
        title=" ".join(re.findall(exp,title))  #using this for avoiding sql syntax errors
        about_product="".join(about_product[0:len(about_product)])
        about_product=" ".join(re.findall(exp,about_product))
        insert_command=f"insert into data(title,product_url,image_url,rating,price,about_product,published_date) values ('{title}','{product_url}','{image_url}','{rating}','{price[0]}','{about_product}','{published_date}');"
        self.executer.execute(insert_command)
        self.mydb.commit()
        # yield {'Title': title,'product_url':product_url, 'image_url': image_url, 'Rating': rating,'Price': price,'About_product': about_product,'published_date':published_date}
