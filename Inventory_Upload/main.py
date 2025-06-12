from flask import Flask,render_template,request,jsonify,session,url_for
import os,mysql.connector


app=Flask(__name__)

#returns 24 bytes not character
app.secret_key = os.urandom(24)

def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='admin123',
        database='inventory'
    )
    return connection

@app.route('/')
def firstpage():
    return render_template('index.html')

@app.route('/capture_owner',methods=['POST'])
def capture_owner():
    data=request.get_json()
    owner=data.get('owner')
    print(f"Owner: {owner}")
    
    session['owner']=owner
    
    return jsonify({'redirect': url_for('second_html')})

@app.route('/inventory')
def second_html():
    return render_template('inventory.html')

@app.route('/second_form',methods=['POST'])
def capture_inventory():
    data=request.get_json()
    locn=data.get('locn')
    sku=data.get('sku')
    uom=data.get('uom')
    qty=data.get('qty')
    owner = session.get('owner')
    print(f"owner:{owner},locn:{locn},sku:{sku},uom:{uom},qty:{qty}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = "INSERT INTO sample (owner,location,sku,uom,qty) VALUES (%s, %s, %s, %s, %s)"
        val = (owner,locn,sku,uom,qty)
        cursor.execute(sql, val)

        conn.commit()
        
        return jsonify({"message": "Inventory data saved successfully!"}),200

    except mysql.connector.Error as err:
        print("MySQL Error: ", err)
        return jsonify({"error": "Database error"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
     
   
if __name__ == '__main__':
    app.run(debug=True) 