# test_mysql.py
import mysql.connector

conn = mysql.connector.connect(
    host="uplant.mysql.database.azure.com",
    user="julianbar", 
    password="CaP25_plant1!1_JB",
    ssl_ca="/Users/julianbartosz/git/schoolwork/UPlant/backend/root/DigiCertGlobalRootCA.crt.pem"
)
print("Connected successfully!")