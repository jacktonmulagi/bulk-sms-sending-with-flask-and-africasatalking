import os
import re
from hashlib import md5

import pymysql
from flask import Flask, request, render_template, flash, url_for, session

import africastalking
from flask_ngrok import run_with_ngrok


from werkzeug.utils import redirect
from datetime import datetime


app = Flask(__name__)
run_with_ngrok(app)

username = os.getenv('user_name', 'esurvey')
api_key = os.getenv('api_key', 'de8fbaad2b31fde57ec236a23f26c679c7d63e4eb0c6973db514373912bfec39')

africastalking.initialize(username, api_key)
sms = africastalking.SMS
conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db='bulksms')
app.secret_key = 'many random bytes'


mysql = pymysql

@app.route('/login', methods=['GET', 'POST'])
def login():
# Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cur = conn.cursor()
        cur.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        # Fetch one record and return result
        account = cur.fetchone()
                # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg='')


@app.route("/main", methods=["GET", "POST"])
def main():
    cur = conn.cursor()
    cur.execute("SELECT  * FROM deliveryreport")
    data = cur.fetchall()
    cur.close()

    cur = conn.cursor()
    cur.execute("SELECT phoneNo FROM phoneno")
    number = cur.fetchall()
    cur.close()
    if request.method == "POST":
        flash("MESSAGE WAS SEND Successfully")
        sms_message = request.form['smsMessage']
        for row in number:
            phone_number = row[0]
            response = sms.send(sms_message, [phone_number])
        print(sms_message)
        print(phone_number)




        print(response)



    return render_template('index.html', deliveryreport=data)


@app.route('/', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = (request.form['password'])
        email = request.form['email']

                # Check if account exists using MySQL
        cur = conn.cursor()
        cur.execute('SELECT * FROM accounts WHERE username = %s', (username))
        account = cur.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cur.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email))
            conn.commit()
            msg = 'You have successfully registered!'
            return redirect(url_for('login'))
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)













@app.route('/insert', methods=["GET", "POST"])
def insert():
    if request.method == "POST":
        flash("MESSAGE WAS SEND Successfully")
        Status = "SEND"
        sms_message = request.form['smsMessage']

        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')





        cur = conn.cursor()
        cur.execute("INSERT INTO  sendingsms (Date, Text, Status ) VALUES (%s, %s,  %s)",
                    (formatted_date, sms_message, Status))
        conn.commit()
        return redirect(url_for('main'))

@app.route('/logout')
def logout():
    session.pop('username',None)
    return redirect(url_for('login'))



@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return redirect(url_for('main'))
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/phoneiist/', methods=["GET", "POST"])
def phone_list():
    cur = conn.cursor()
    cur.execute("SELECT  * FROM phoneno")
    data = cur.fetchall()
    cur.close()

    return render_template('phonelist.html', phoneno=data)


@app.route('/delivery_report/', methods=['GET', 'POST'])
def inbound_sms():
    now = datetime.now()
    formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')

    # Sender's phone number
    messageId = request.values.get('id')

    to_number = request.values.get('phoneNumber')

    network = request.values.get('networkCode')

    status = request.values.get('status')

    Total_cost = request.values.get('cost')

    failure_for_Reason = request.values.get('failureReason')

    print('Message received - phoneNumber: %s, status: %s, networkCode: %s ,cost: %s ,id: %s' % (to_number, status, network,Total_cost, messageId))
    cur = conn.cursor()
    cur.execute("INSERT INTO  deliveryreport (Time, to_number, network,status ) VALUES (%s, %s, %s, %s)",
                (formatted_date, to_number,  network, status))
    conn.commit()


    # Print the message

    return "Delivery status reported"

@app.route('/contacts/', methods=['GET', 'POST'])
def contacts():
    # Output message if something goes wrong...
    msg = ''
    # Check if phone" POST requests exist (user submitted form)
    if request.method == 'POST' and 'phone' in request.form:
        # Create variables for easy access
        phone = request.form['phone']


          # Check if phone exists using MySQL
        cur = conn.cursor()
        cur.execute('SELECT * FROM phoneno WHERE phoneNo = %s', (phone))
        account = cur.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'phone number already exists!'


        elif not phone:
            msg = 'Please fill out the form!'
        else:
            # phone doesnt exists and the form data is valid, now insert new account into accounts table
            cur.execute('INSERT INTO phoneno VALUES (NULL, %s)', ( phone ) )
            conn.commit()
            msg = 'You have successfully registered!'
            return redirect(url_for('main'))
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('contacts.html', msg=msg)

@app.route('/profile/', methods=["GET", "POST"])
def profile():
    cur = conn.cursor()
    cur.execute("SELECT  * FROM accounts")
    data = cur.fetchall()
    cur.close()

    return render_template('profile.html', accounts=data)




if __name__ == "__main__":
    app.run(debug=True)
