import sqlite3 as lite

class DBophandle:
    def connecttodb(self, dbname):
	self.dbname = dbname
	self.con = lite.connect(dbname)
	self.cur = self.con.cursor()

    def inituserdb(self):
	cursor = self.cur
	cursor.execute("CREATE TABLE usertable(uname text PRIMARY KEY, pbkey text, prkey text)")
	self.con.commit()

    def insertuser(self, usname, pbkey, prkey):
	cursor = self.cur
	params = (usname, pbkey, prkey)
	cursor.execute("INSERT INTO usertable VALUES (?, ?, ?)", params)
	self.con.commit()

    def getuser(self, usname):
        cursor=self.cur
	cursor.execute("SELECT * FROM usertable WHERE uname="+ "'" + usname + "'" )
	row = cursor.fetchone()
	if row is None:
	  return None
	else:
	  return (row[1], row[2])  
