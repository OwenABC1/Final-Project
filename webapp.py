from flask import Flask, redirect, url_for, session, request, jsonify, render_template, flash
from markupsafe import Markup
#from flask_apscheduler import APScheduler
#from apscheduler.schedulers.background import BackgroundScheduler
from flask_oauthlib.client import OAuth
from bson.objectid import ObjectId

import pprint
import os
import time
import pymongo
import sys
import pydealer
from pydealer import Card, Deck, Stack

 
app = Flask(__name__)

app.debug = False #Change this to False for production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' #Remove once done debugging

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
oauth.init_app(app) #initialize the app to be able to make requests for user information

#Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',  
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)

#Connect to database
url = os.environ["MONGO_CONNECTION_STRING"]
client = pymongo.MongoClient(url)
db = client[os.environ["MONGO_DBNAME"]]
collection = db['FinalProject'] #TODO: put the name of the collection here
#print(db.list_collection_names())

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

#context processors run before templates are rendered and add variable(s) to the template's context
#context processors must return a dictionary 
#this context processor adds the variable logged_in to the conext for all templates



@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}
    

AddedCards = 0
gamestage = 0
deck = pydealer.Deck()
hand = pydealer.Stack() 
firstTime = 'false'
display = 'false'
foo_hidden = False  

@app.route('/add_cards', methods=['POST'])
def add_cards():
    global AddedCards
    global gamestage
    global deck
    global hand
    global display
    
    if AddedCards < 5:  # Only add cards if less than 2 cards have been added
        AddedCards += 1
        dealt = deck.deal(1)
        hand.add(dealt)
    
    gamestage = 1
  
    return jsonify({'AddedCards': AddedCards})

    
@app.route('/restart', methods=['POST'])
def restart():
    global gamestage
    global AddedCards
    global deck
    global hand
    global display
    gamestage = 0
    if gamestage == 0:
        AddedCards = 0 
        deck = pydealer.Deck()
        hand = pydealer.Stack()
        deck.shuffle()
        display = 'false'
     
      
    return jsonify({'gamestage': gamestage})
    
@app.route('/', methods=["GET","POST"])
def home():

    global AddedCards
    global gamestage
    global hand
    global deck
    global firstTime
    global display
    
    if 'chips' not in session:
        session['chips'] = 0
    if 'bet' not in session:
        session['bet'] = 0
        print(session['bet'])
    
    if firstTime == 'false':
        firstTime = 'true'
        deck.shuffle()
    

    highscores = ""
    documents = []
    # Get the user's highscore from the database
    if 'github_token' in session:
        print("I see gthub token")
        if "PostHS" in request.form:  #option to submit score prompt with post HS form
            print("Tyring to submit hs")
            newDict = {"USER":session['user_data']['login'],"Score":session['chips']+session['bet']}
            LastDoc = {}
            for doc in collection.find():
                LastDoc = doc
            print(newDict)
            print(LastDoc)   
            if newDict["USER"] != LastDoc["USER"] and newDict["Score"] != LastDoc["Score"]:
                collection.insert_one(newDict)
                print(session["chips"])
              
    for c in collection.find():
        highscores = highscores + Markup("User: "+c["USER"]+"Score: "+str(c["Score"]))
        documents.append({"User": c["USER"], "Score": c["Score"]})
    print(highscores)
    print(documents)
    
    
    
    if 'chips' not in session:
        session['chips'] = 500

    if "AddChips" in request.form:
        session['chips'] = 500 
        session['bet'] = 0
        print("chips: "+ str(session['chips']))
    
    if not hand:  # Only initialize hand if it's empty
        hand = pydealer.Stack()
        
    total = 0
    num_aces = 0
    
    
    if 'bet' not in session:
        session['bet'] = 0
    if "BetChips" in request.form and session['chips'] > 0:
        session['bet'] = session['bet'] + 50 
        session['chips'] = session['chips'] - 50 
        print("chips: "+ str(session['chips']))
        print("bet: "+ str(session['bet']))
    #print("chips: "+ str(chips))
    
    if 'bet' not in session:
        session['bet'] = 0
    if "BetChips100" in request.form and session['chips'] >= 100:
        session['bet'] = session['bet'] + 100 
        session['chips'] = session['chips'] - 100 
        print("chips: "+ str(session['chips']))
        print("bet: "+ str(session['bet']))
    #print("chips: "+ str(chips))
    
    
    
    if 'bet' not in session:
        session['bet'] = 0
    if "BetChipsAll" in request.form and session['chips'] > 0:
        session['bet'] = session['bet'] + session['chips'] 
        session['chips'] = 0 
        print("chips: "+ str(session['chips']))
        print("bet: "+ str(session['bet']))
    #print("chips: "+ str(chips))
    

    for card in hand:
        if card.value.isdigit():
            card_value = int(card.value)
        elif card.value in ['Jack', 'Queen', 'King']:
            card_value = 10
        elif card.value == 'Ace':
            card_value = 11
            num_aces += 1
        else:
            card_value = 0  # Default case, should not happen with standard cards
        
        total += card_value

        # Adjust for Aces
        while total > 21 and num_aces > 0:
            total -= 10
            num_aces -= 1
            
        if total > 21:
            display = 'true'
            SendDisplay()
            print(display)
            session['bet'] = 0
            print("BUUUUUUUST")
            
        if total == 21:
            print("win")
            session['chips'] = session['chips'] + 2*(int(session['bet']))
            session['bet'] = 0
            print(session['bet'])
            print(session['chips'])
    app.logger.info(f"Total value of cards in hand: {total}")

    return render_template('home.html', held=hand, total_value=total,display=display,chips=session['chips'], bet=session['bet'])
@app.route("/sendDisplay")
def SendDisplay():
   
   
    global display
    


    return jsonify({'display': display})
    


@app.route('/getFooState', methods=['GET'])
def get_foo_state():
    global foo_hidden
    return jsonify({'fooHidden': foo_hidden})


@app.route('/setFooState', methods=['POST'])
def set_foo_state():
    global foo_hidden
    foo_hidden = request.json.get('fooHidden', False)
    return jsonify({'success': True})

    
    return render_template('home.html', held=dealt, total_value=total, chips=session['chips'], bet=session['bet'], highscores=highscores, documents=documents)



#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='http')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    flash('You were logged out.')
    return redirect('/')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        flash('Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args), 'error')      
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            flash('You were successfully logged in as ' + session['user_data']['login'] + '.')
        except Exception as inst:
            session.clear()
            print(inst)
            flash('Unable to login, please try again.', 'error')
    return redirect('/')
#@app.route('/post_highscore', methods=['POST'])
#def post_highscore():
#    if 'github_user_id' in session:
  #      highscore = session.get('chips')
#
 #       # Check if the user already has a highscore, and update it if it's higher
#        existing_user = collection.find_one({'github_user_id': session['github_user_id']})
#
 #       if existing_user:
  #          if existing_user['highscore'] < highscore:
  #              collection.update_one(
  #                  {'github_user_id': session['github_user_id']},
  #                  {'$set': {'highscore': highscore}}
  #              )
 #       else:
  #          collection.insert_one({
  #              'github_user_id': session['github_user_id'],
  #              'highscore': highscore
  #          })
#
  #      return redirect(url_for('home'))
 #   else:
  #      return redirect(url_for('login'))

@app.route('/page1', methods=["GET","POST"])
def renderPage1():
    highscores = ""
    documents = []
    # Get the user's highscore from the database
    if 'github_token' in session:
        print("I see gthub token")
        if "PostHS" in request.form:  #option to submit score prompt with post HS form
            print("Tyring to submit hs")
            newDict = {"USER":session['user_data']['login'],"Score":session['chips']}
            LastDoc = {}
            for doc in collection.find():
                LastDoc = doc
            print(newDict)
            print(LastDoc)   
            if newDict["USER"] != LastDoc["USER"] and newDict["Score"] != LastDoc["Score"]:
                collection.insert_one(newDict)
                print(session["chips"])
              
    for c in collection.find():
        highscores = highscores + Markup("User: "+c["USER"]+"Score: "+str(c["Score"]))
        documents.append({"User": c["USER"], "Score": c["Score"]})
    print(highscores)
    print(documents)
    return render_template('page1.html', highscores=highscores, documents=documents)
               
               
       
            #highscores = collection.find().sort('highscore', pymongo.DESCENDING)
          #  highscore_list = []
           # for user in highscores:
          #      username = user.get('github_user_id') 
           #     highscore = user.get('highscore', 0)
           #     highscore_list.append((username, highscore))
           # if highscore:
           #     chips = highscore.get('highscore', 0)
          #  else:
         #       chips = 0
      #  else:
       #    chips = 0
     
    

#    highscore_list = []
#    for user in highscores:
#        username = user.get('github_user_id') 
#        highscore = user.get('highscore', 0)
#        highscore_list.append((username, highscore))
    
   # return render_template('page1.html', highscore_list=highscore_list)


#the tokengetter is automatically called to check who is logged in
@github.tokengetter
def get_github_oauth_token():
    return session['github_token']


if __name__ == '__main__':
    app.run()
