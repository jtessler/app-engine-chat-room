from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext.webapp.util import login_required
import cgi
import jinja2
import os
import webapp2

class ChatUser(ndb.Model):
  """ Stored user model. Should be keyed by the User ID. """
  nickname = ndb.StringProperty()

class HandleSend(webapp2.RequestHandler):
  """ When a user sends a message to be echoed to all other users. """
  def post(self):
    data = self.request.get('data')
    users = ChatUser.query();
    for user in users.iter():
      channel.send_message(user.key.string_id(),
                           '%s: %s' % (user.nickname, cgi.escape(data)))

class HandleJoin(webapp2.RequestHandler):
  """ Stores a new user model and notifies all other users. """
  def post(self):
    user = users.get_current_user()
    new_chat_user = ChatUser.get_or_insert(user.user_id(),
                                           nickname = user.nickname())

    existing_users = ChatUser.query(ChatUser.key != new_chat_user.key);
    channel.send_message(new_chat_user.key.string_id(),
                         'Welcome, %s! Other chatters: %d' %
                         (new_chat_user.nickname, existing_users.count()))
    for existing_user in existing_users.iter():
      channel.send_message(existing_user.key.string_id(),
                           '%s joined' % new_chat_user.nickname)

class HandleLeave(webapp2.RequestHandler):
  """ Deletes the user model and notifies all other users. """
  def post(self):
    user = users.get_current_user()
    chat_user = ChatUser.get_by_id(user.user_id())
    chat_user.key.delete()

    other_users = ChatUser.query();
    for user in other_users.iter():
      channel.send_message(user.key.string_id(),
                           '%s left' % user.nickname)

class HandleMain(webapp2.RequestHandler):
  """ Renders index.html an initializes the chat room channel. """
  @login_required
  def get(self):
    user = users.get_current_user()
    token = channel.create_channel(user.user_id())
    template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render({ 'token': token }))

jinja_environment = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

app = webapp2.WSGIApplication([
  ('/', HandleMain),
  ('/join', HandleJoin),
  ('/send', HandleSend),
  ('/leave', HandleLeave),
], debug=True)
