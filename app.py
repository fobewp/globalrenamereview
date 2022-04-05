# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import flask
import re
import requests
import toolforge
import urllib.parse

def getrequest(url: str, **kwargs):
  r = requests.get(url, params=kwargs)
  r.raise_for_status()
  return r

def getdbs() -> dict:
  toolforge.set_user_agent('globalrenamereview')
  dblist = getrequest('https://noc.wikimedia.org/conf/dblists/flaggedrevs.dblist').text
  dbnames = [db for db in [re.sub('#.*$', '', line).strip() for line in dblist.splitlines()] if db != '']
  sitematrix = getrequest('https://meta.wikimedia.org/w/api.php', action='sitematrix', format='json').json()['sitematrix']
  dbs = {}
  for dbname in dbnames:
    for num in sitematrix:
      if num.isdigit():
        for site in sitematrix[num]['site']:
          if site['dbname'] == dbname:
            dbs[dbname] = {'url': site['url'], 'langcode': sitematrix[num]['code']}
      elif num == 'specials':
        for special in sitematrix[num]:
          if special['dbname'] == dbname:
            dbs[dbname] = {'url': special['url'], 'langcode': 'en'}
  return dbs

fr_dbs = getdbs()
supported_languages = ['en', 'de', 'hu']
query = r'''
SELECT
	page1.page_title,
	actor1.actor_name AS renamer,
	COUNT(DISTINCT actor2.actor_name) AS pending_users,
	flaggedpage_pending1.fpp_rev_id AS pending_oldid
FROM
	page as page1
	INNER JOIN revision AS revision1 ON page1.page_id = revision1.rev_page
	INNER JOIN flaggedpage_pending AS flaggedpage_pending1 ON page1.page_id = flaggedpage_pending1.fpp_page_id
	INNER JOIN actor AS actor1 ON actor1.actor_id = revision1.rev_actor
	INNER JOIN `comment` AS comment1 ON comment1.comment_id = revision1.rev_comment_id
	INNER JOIN revision AS revision2 ON page1.page_id = revision2.rev_page
	INNER JOIN actor AS actor2 ON actor2.actor_id = revision2.rev_actor
WHERE
	revision1.rev_timestamp >= flaggedpage_pending1.fpp_pending_since
	AND (comment1.comment_text RLIKE '^\\(\\[\\[c\\:GR\\|GR\\]\\]\\)' OR comment1.comment_text RLIKE '[G|g]lobal[R|r]eplace')
	AND revision2.rev_timestamp >= flaggedpage_pending1.fpp_pending_since
	AND page1.page_namespace = 0
GROUP BY
	page1.page_title
ORDER BY
	revision1.rev_timestamp DESC;
'''

app = flask.Flask(__name__)

@app.route('/')
@app.route('/<dbname>')
def index(dbname='huwiki'):
  if dbname not in fr_dbs:
    flask.abort(404)
  conn = toolforge.connect(dbname, 'analytics') # conn is a pymysql.connection object.
  domain, targetlang = fr_dbs[dbname]['url'], fr_dbs[dbname]['langcode']
  rows = []
  with conn.cursor() as cur: # querying articles
    rowcount = cur.execute(query) # number of affected rows
    for i in range(rowcount):
      row = cur.fetchone()
      urltitle = urllib.parse.quote(row[0].decode('utf-8'))
      rows.append({
        'url': '%s/wiki/%s' % (domain, urltitle),
        'title': row[0].decode('utf-8').replace('_', ' '),
        'renamer': row[1].decode('utf-8'),
        'others': row[2] - 1,
        'reviewurl': '%s/w/index.php?title=%s&oldid=%d&diff=curr' % (domain, urltitle, row[3])
      })
  conn.close()
  lang = flask.request.accept_languages.best_match(supported_languages)
  return flask.render_template(lang + '.html', lang=targetlang, count=rowcount, rows=rows, dbnames=fr_dbs.keys())
