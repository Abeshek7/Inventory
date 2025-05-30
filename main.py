from flask import Flask,render_template,request,jsonify,session,url_for,send_file,redirect
import pandas as pd
import os,mysql.connector,io
from werkzeug.security import generate_password_hash, check_password_hash #created wed 28/05/25
from functools import wraps #created wed 28/05/25
from datetime import date, datetime #created wed 28/05/25


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

# --- Auth helpers ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Registration ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)
        created_date = date.today()
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO user_master (username, password, created_date) VALUES (%s, %s, %s)",
                (username, hashed_pw, created_date)
            )
            conn.commit()
            return redirect(url_for('login'))
        except mysql.connector.Error:
            return render_template('register.html', error="Username already exists.")
        finally:
            cursor.close()
            conn.close()
    return render_template('register.html')

# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT * FROM user_master WHERE username=%s", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                last_login_time = datetime.now()
                cursor.execute("""
                    UPDATE user_master 
                    SET last_login = %s 
                    WHERE id = %s
                """, (last_login_time, user['id']))
                conn.commit()

                session['user_id'] = user['id']
                session['username'] = user['username']

                return redirect(url_for('firstpage'))
            else:
                return render_template('login.html', error="Invalid credentials.")
        
        except mysql.connector.Error as e:
            print("Login DB Error:", e)
            return render_template('login.html', error="Database error.")
        
        finally:
            cursor.close()
            conn.close()

    return render_template('login.html')


# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def firstpage():
    return render_template('index.html')

@app.route('/capture_owner',methods=['POST'])
@login_required
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
    LPN=data.get('LPN')
    uom=data.get('uom')
    qty=data.get('qty')
    owner = session.get('owner')
    username = session.get('username')
    created_at = datetime.now()
    
    conn=None
    cursor=None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert into inv_capture table
        sql = """INSERT INTO inv_capture1 
                (owner, location, sku, lpn, uom, qty, username, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        val = (owner, locn, sku, LPN, uom, qty, username, created_at)
        cursor.execute(sql, val)
        conn.commit()

        # Call stored procedure to update ASN numbers
        cursor.callproc('process_download_dummy', [username])
        conn.commit()
        
        return jsonify({"message": "Inventory data saved successfully!"}), 200

    except mysql.connector.Error as err:
        print("MySQL Error: ", err)
        return jsonify({"error": "Database error"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

@app.route('/download_excel')
def download_excel():
    conn = get_db_connection()
 
    try:
        df1 = pd.read_sql(
            '''SELECT DISTINCT "" as `Column Name`, "" as `GenericKey`, 
                      asn_number as `ASN/Receipt`, owner as `Owner`, status as `Receipt Status` 
               FROM download_table WHERE download_status = 'NO' ''',
            conn
        )

        df2 = pd.read_sql(
            '''SELECT "" as `Column Name`, "" as `GenericKey`, asn_number as `ASN/Receipt`, 
                      sku as `Item`, owner as `Owner`, line_number as `Line #`, qty as `Expected Qty`, 
                      uom as `UOM`, lpn as `LPN`, location as `LOCATION` 
               FROM download_table WHERE download_status = 'NO' ''',
            conn
        )

        cursor = conn.cursor()
        cursor.execute("UPDATE download_table SET download_status = 'YES' WHERE download_status = 'NO'")
        conn.commit()
        cursor.close()

    except Exception as e:
        print("Error in download_excel:", e)
        return jsonify({"error": "Database error while exporting"}), 500

    finally:
        conn.close()
    
    #first sheet details
    header_row_first_sheet=["Column Name", "GenericKey", "RECEIPTKEY","STOREKEY","Status"]
    
    first_row=["Messages", "GenericKey"] + list(df1.columns[2:])
    
    df1.columns = header_row_first_sheet
 
    final_df1 = pd.DataFrame([first_row], columns=header_row_first_sheet)
    final_df1 = pd.concat([final_df1, df1], ignore_index=True)
    
    #second sheet details   
    header_row_1 = [
        "Column Name", "GenericKey", "RECEIPTKEY", "SKU","STOREKEY", "RECEIPTLINENUMBER", "QTYEXPECTED", "UOM", "TOID", "TOLOC"]
    
    second_row = ["Messages", "GenericKey"] + list(df2.columns[2:])

    df2.columns = header_row_1

    final_df2 = pd.DataFrame([second_row], columns=header_row_1)
    final_df2 = pd.concat([final_df2, df2], ignore_index=True)
    
    
    #third sheet details
    header_row_third_sheet=[["Date Format","M/d/yy h:mm a","MM Month, dd:Day, yy:year, mm:minute, hh:hours"],
                            ["Time Zone","(GMT-05:00) Eastern Time (US & Canada)","America/New_York"],
                            ["Empty Fields","[blank]","To remove existing values in character fields and leave them empty, place the value [blank] (including the brackets) in the respective cells on the import spreadsheet."]]
    
    final_df3 = pd.DataFrame(header_row_third_sheet)
    
    #memory buffer in which we will write the excel file
    output = io.BytesIO()
    
    #pd.excelwriter --> pandas functio which is used to write the dataframes to the excel file
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        final_df1.to_excel(writer, index=False,sheet_name='Data')
        final_df2.to_excel(writer, index=False,sheet_name='Detail')
        final_df3.to_excel(writer, index=False,header=False,sheet_name='Validations')
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name='inventory_export.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )



if __name__ == '__main__':
    app.run(debug=True)