import scrapy
from urllib.parse import urlencode
import re
import urllib.request
import os
import mysql.connector


queries=["Laptops with AMD Ryzen 5 processor"]
class AmazonSpider(scrapy.Spider):
    name = 'amazon'
    def __init__(self):
        self.mydb=mysql.connector.connect(host="localhost",user="root",passwd="root",database="employee_db")
        self.executer = self.mydb.cursor()
        self.executer.execute("use internship_task")

    def start_requests(self):
        for query in queries:
            url = 'https://www.amazon.in/s?' + urlencode({'k': query})
            print(f"###########URL################{url}")
            yield scrapy.Request(url=url, callback = self.parse_keyword_response)

    def parse_keyword_response(self, response):
        products = response.xpath('//*[@data-asin]') #taking all tags with data-asin attribute
        print(products)
        for product in products:
            # print("###############Product#############",product,type(product))
            asin = product.xpath('@data-asin').extract_first()  #extracting the value of data-asin
            # print("#########ASIN##########",asin)
            product_url = f"https://www.amazon.in/dp/{asin}"
            # print("################ product URL ##############",product_url)
            yield scrapy.Request(url=product_url, callback=self.parse_product_page, meta={'asin': asin}) #meta can be considered as a dictionary passed as an argument

    def parse_product_page(self, response): 
        asin = response.meta['asin']
        print("#########inside parse product page#############")

        product_url=f"https://www.amazon.in/dp/{asin}"
        print("############product_url#############",product_url)

        title = response.xpath('//*[@id="productTitle"]/text()').extract_first()
        print("######################Product Title###########",title)

        rating = response.xpath('//*[@id="acrPopover"]/@title').extract_first()
        print('#########rating########',rating)

        price=response.xpath('//*[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span[2]/span[1]/text()').extract()
        print('##############price##########',price[0])

        about_product = response.xpath('//*[@id="feature-bullets"]//li/span/text()').extract() #// li represents all li tags
        print("#########about product#########",about_product[0:3])

        published_date=response.xpath('//*[@id="productDetails_detailBullets_sections1"]/tbody/tr[4]/td/text()').extract_first()
        
        print("###########published date#########",published_date)

        # image = re.search('"large":"(.*?)"',response.text).groups()[0]
        image_url=response.xpath('//*[@id="imgTagWrapperId"]/img/@src').extract_first() 

        #downling image using url

        full_path="images/"+title.split("/")[0]+"/"
        file_name=full_path.split("/")[1]
        try:
            urllib.request.urlretrieve(image_url,full_path+".jpg")
            # print("0")
        except FileNotFoundError:
            try:
                os.mkdir("images")
                os.mkdir(f"{full_path}")
                # print(os.curdir)
                # print(full_path)
                urllib.request.urlretrieve(image_url,full_path+f"{file_name}.jpg")
                # print("1")
            except FileExistsError:
                os.mkdir(f"{full_path}")
                urllib.request.urlretrieve(image_url,full_path+".jpg")

        insert_command=f"insert into data(title,product_url,image_url,rating,price,about_product,published_date) values ('{title}','{product_url}','{image_url}','{rating}','{price}','{about_product}','{published_date}');"
        self.executer.execute(insert_command)
        self.mydb.commit()
        
        # yield {'Title': title,'product_url':product_url, 'image_url': image_url, 'Rating': rating,'Price': price,'About_product': about_product,'published_date':published_date}
