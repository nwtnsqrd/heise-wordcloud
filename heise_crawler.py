import requests
from bs4 import BeautifulSoup
import sqlite3
from time import strftime
from wordcloud import WordCloud


'''
init_table() creates the frontpage_stats table in sqlite3
'''
def init_table(conn):
  c = conn.cursor()
  sql = 'CREATE TABLE IF NOT EXISTS frontpage_stats(id integer primary key autoincrement, date text, title text, synopsis text)'

  c.execute(sql)
  conn.commit()

  return


'''
insert_into_table() adds the scraped data to individual rows
'''
def insert_into_table(conn, teaser_titles, teaser_synopsis):
  c = conn.cursor()

  sql = 'INSERT INTO frontpage_stats (date, title, synopsis) VALUES (?, ?, ?)'

  # len(teaser_titles) should always be len(teaser_synopsis), but in case it's not we just ignore the additional data
  for i in range(min(len(teaser_titles), len(teaser_synopsis))):
    c.execute(sql, (strftime('%Y-%m-%d'), teaser_titles[i].text.strip(), teaser_synopsis[i].text.strip()))

  conn.commit()

  return


'''
get_all_rows() selects all rows and prints them
'''
def get_all_rows(conn):
  cur = conn.cursor()
  cur.execute('SELECT * from frontpage_stats')

  rows = cur.fetchall()

  for row in rows:
    print(row)

  return


'''
prepare_wordcloud() sanitizes the text and puts it into a single, whitespace-separated string
'''
def prepare_wordcloud(conn):
  cur = conn.cursor()
  cur.execute('SELECT title, synopsis from frontpage_stats WHERE date = \'%s\'' % strftime('%Y-%m-%d'))

  rows = cur.fetchall()
  rows = str(rows)
  rows = rows.split(' ')
  res = ''

  for row in range(len(rows)):
    rows[row] = rows[row].replace("'", '').replace('(', '').replace(')', '').replace(',', '').replace('"', '').replace(':', '').replace('[', '').replace(']', '').replace('?', '').replace('Der', '').replace('Die', '').replace('Das', '').replace('Auf', '').replace('Mit', '').replace('Ein', '').replace('Eine', '')

    # its important to check whether the string is empty FIRST - otherwise you get IndexError: string index out of range
    if rows[row] != '' and (is_number(rows[row][0]) or rows[row][0].isupper()):
      res += rows[row] + ' '
  
  return res


'''
create_wordcloud() does exactly what you think it does
'''
def create_wordcloud(prepared_string):
  wc = WordCloud(collocations=False, width=1920, height=1080, background_color='white').generate(prepared_string)
  wc.to_file('./images/wordcloud_%s.png' % strftime('%Y-%m-%d-%H-%M-%S'))

  return


'''
is_number() checks if a string is actually a number
'''
def is_number(s):
  try:
      int(s)
      return True
  except ValueError:
      pass

  try:
      import unicodedata
      unicodedata.numeric(s)
      return True
  except (TypeError, ValueError):
      pass
 
  return False


'''
main() scrapes the website and calls a function that works with the scraped data
'''
def main():
  url = 'https://www.heise.de'
  session = requests.Session()
  session.headers.update({ 'User-Agent' : 'One scrapy boi 1.0' })

  page = session.get(url)
  page_content = page.content

  soup = BeautifulSoup(page_content, 'html.parser')

  news_content = soup.find('div', { 'id' : 'mitte_links' })

  teaser_titles = news_content.find_all('span', { 'class' : 'a-article-teaser__title-text' })
  teaser_synopsis = news_content.find_all('p', { 'class' : 'a-article-teaser__synopsis' })

  conn = sqlite3.connect('heise_frontpage.db')
  #init_table(conn)
  insert_into_table(conn, teaser_titles, teaser_synopsis)
  #get_all_rows(conn)
  create_wordcloud(prepare_wordcloud(conn))
  conn.close()

if __name__ == '__main__':
    main()