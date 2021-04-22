import poplib
import email
import re
from email.header import decode_header
import psycopg2
import config

address = config.address
password = config.password
gmail = poplib.POP3_SSL(config.pop3_address, config.pop3_port)
gmail.user(address)
gmail.pass_(password)

class Retrieve_mail():
	def __init__(self, num):
		mail = email.message_from_bytes(b'\r\n'.join(gmail.retr(num)[1]))
		if mail['To'] == "foo@gmail.com":
			self.sender = self.encode_header(mail['From'])
			self.date = self.encode_header(mail['Date'])
			self.subject = self.encode_header(mail['Subject'])
			self.receiver = self.encode_header(mail['To'])
			if mail.is_multipart():
				for part in mail.walk():
					if part.get_payload(decode=True):
						message = part.get_payload(decode=True)
						if mail.get_content_charset():
							message = message.decode(mail.get_content_charset())
						elif mail.get_charsets()[1]:
							try:
								message = message.decode(mail.get_charsets()[1])
							except:
								pass
						else:
							try:
								message = message.decode()
							except:
								pass
					else:
						continue
					break
			else:
				message = mail.get_payload(decode=True)
				if message:
					if mail.get_content_charset():
						message = message.decode(mail.get_content_charset())
					else:
						message = message.decode()
					if "text/html" in mail['Content-Type']:
						message = re.sub('\n', "", message)
						message = re.sub('<style(.)*/style>', "", message)
						message = re.sub('<[^>]*?>', "", message)
			self.message = message
	
	def encode_header(self, element):
		element = decode_header(element)
		output = ""
		for i in element:
			data, encode_type = i
			if encode_type:
				output = output + data.decode(encode_type)
			elif "bytes" in str(type(data)):
				output = output + data.decode()
			else:
				output = output + data
		return output

num = gmail.stat()[0]
conn = psycopg2.connect(host=config.db_host, port=config.db_port, dbname=config.db_name, user=config.db_user, password=config.db_password)
with conn:
	conn.autocommit = True
	with conn.cursor() as cur:
		while num <= gmail.stat()[0] and num > 0:
			mail = Retrieve_mail(num)
			try:
				query = "insert into public.imported_mails (\"from\", \"to\", \"subject\", \"body\") values ('" + mail.sender + "', '" + mail.receiver + "', '" + mail.subject + "', '" + mail.message + "');"
				cur.execute(query)
			except:
				pass
			num -= 1
		cur.close()
