import mysql.connector

mydb = mysql.connector.connect(host="localhost",user="root",passwd="",db="filtros")

cur = mydb.cursor()


cur.execute("SELECT * FROM reglas WHERE id_regla = (SELECT MAX(id_regla) from reglas )")

row = cur.fetchone()
mac_src = row[1]
mac_dst = row[2]
hora_ini = row[3]
horo_fin = row[4]

print (mac_src)
print (mac_dst)
