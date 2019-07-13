import mysql.connector

mydb = mysql.connector.connect(host="localhost",user="root",passwd="",db="filtros")

cur = mydb.cursor()


cur.execute("SELECT * FROM reglas")

for row in cur.fetchall():
    print (row[2])
