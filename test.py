from selenium import webdriver
from bs4 import BeautifulSoup
import datetime
import psycopg2

conn=psycopg2.connect(
        database="mydb",
        user='chingiz1',
        password='456123',
        port='5432',
        client_encoding='UTF-8'
    )

driver = webdriver.Chrome()
driver.get("https://cbu.uz/")
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")
list_cueransy=[]

for s in soup.find_all("div", class_="exchange__item_value"):
    list_cueransy.append(s.text)
cur=conn.cursor()

usd=list_cueransy[0]
eur=list_cueransy[1]
rub=list_cueransy[2]
gbp=list_cueransy[3]
jpy=list_cueransy[4]
chf=list_cueransy[5]
cny=list_cueransy[6]
data=[(str(usd),str(eur),str(rub),str(gbp),str(jpy),str(chf),str(cny),datetime.datetime.now()),]
cur.execute("""TRUNCATE TABLE currency""")
conn.commit()
cur.execute("""CREATE TABLE IF NOT EXISTS currency (
            id SERIAL PRIMARY KEY,
            usd VARCHAR(100),
            eur VARCHAR(100),
            rub VARCHAR(100),
            gbp VARCHAR(100),
            jpy VARCHAR(100),
            chf VARCHAR(100),
            cny VARCHAR(100),
            date_added TIMESTAMP
            )""")
cur.executemany("""INSERT INTO currency (usd, eur, rub, gbp, jpy, chf, cny, date_added) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",data)

conn.commit()
cur.close()
conn.close()



driver.quit()
