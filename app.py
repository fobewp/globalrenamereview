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
import toolforge

app = flask.Flask(__name__)

@app.route('/')
def index():
  style   = 'body { font-family: sans-serif; }'
  style  += 'table { background-color: #f8f9fa; color: #202122; margin: 1em 0; border: 1px solid #a2a9b1; border-collapse: collapse; }\n'
  style  += 'th { background-color: #eaecf0; text-align: center;  border: 1px solid #a2a9b1; padding: 0.2em 0.4em; color: #202122; border-collapse: collapse; }\n'
  style  += 'td { border: 1px solid #a2a9b1; padding: 0.2em 0.4em; color: #202122; border-collapse: collapse; }\n'
  style  += 'a { text-decoration: none; color: #0645ad; background: none; }\n'
  style  += '.tell{ text-align: center; }\n'

  output = '<style>'+style+'</style>\n<body>\n'
  conn = toolforge.connect('huwiki','analytics') # conn is a pymysql.connection object.
  query = "SELECT page1.page_title AS 'Cím',CONCAT(af.afl_user_text, IF(COUNT(DISTINCT actor.actor_name)>1, CONCAT(' + ', COUNT(DISTINCT actor.actor_name)-1,' további'), '') ) AS 'Szerkesztő', CONCAT('https://hu.wikipedia.org/w/index.php?title=',page1.page_title,'&oldid=',flaggedpage_pending1.fpp_rev_id,'&diff=',page1.page_latest) AS 'Ellenőriz' FROM page as page1 INNER JOIN revision AS revision1 ON page1.page_id = revision1.rev_page INNER JOIN flaggedpage_pending AS flaggedpage_pending1 ON page1.page_id = flaggedpage_pending1.fpp_page_id INNER JOIN abuse_filter_log AS af ON af.afl_rev_id = revision1.rev_id INNER JOIN revision AS revision2 ON page1.page_id = revision2.rev_page INNER JOIN actor ON actor.actor_id = revision2.rev_actor WHERE revision1.rev_timestamp >= flaggedpage_pending1.fpp_pending_since AND af.afl_filter_id = 64 AND revision2.rev_timestamp >= flaggedpage_pending1.fpp_pending_since AND page1.page_namespace = 0 GROUP BY page1.page_title ORDER BY revision1.rev_timestamp DESC;"
  with conn.cursor() as cur: # querying articles
    rows = cur.execute(query) # number of affected rows
    output += '<p>Ez a lap az <a href="https://hu.wikipedia.org/wiki/Speci%C3%A1lis:Vand%C3%A1lsz%C5%B1r%C5%91/64">ellenőrzésre váró globális fájlátnevezéseket</a> listázza. Jelenleg '+str(rows)+' ilyen lap vár ellenőrzésre.</p>\n'
    output += '<table id="globalrename">\n'
    output += '<tr><th>Cikk</th><th>Szerkesztő(k)</th><th>Ellenőrzés</th></tr>'
    for i in range(rows):
      row = cur.fetchone()
      output += '<tr>'
      output += '<td><a href="https://hu.wikipedia.org/wiki/'+row[0].decode('utf-8')+'">'+row[0].decode('utf-8').replace("_"," ")+'</a></td>'
      output += '<td>'+row[1].decode('utf-8')+'</td>'
      output += '<td class="tell"><a href="'+row[2].decode('utf-8')+'">ellenőriz</a></td>'
      output += '</tr>\n'
    output += '</table>\n'
    output += '<p><a href="https://github.com/fobewp/globalrenamereview/tree/main">Forráskód</a></p>\n'
    output += '</body>'
  conn.close()
  return output
