from flask import Flask,render_template,request,jsonify,session,url_for,send_file
import pandas as pd
import os,mysql.connector,io


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
    case=data.get('case')
    uom=data.get('uom')
    qty=data.get('qty')
    owner = session.get('owner')
    print(f"owner:{owner},locn:{locn},sku:{sku},case:{case},uom:{uom},qty:{qty}")
    
    conn=None
    cursor=None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = "INSERT INTO inv_capture (owner,location,sku,`case`,uom,qty) VALUES (%s, %s, %s, %s, %s, %s)"
        val = (owner,locn,sku,case,uom,qty)
        cursor.execute(sql, val)

        conn.commit()
        cursor.callproc('update_asn_and_line') #call the stored procedure in the database
        conn.commit()
        
        return jsonify({"message": "Inventory data saved successfully!"}),200

    except mysql.connector.Error as err:
        print("MySQL Error: ", err)
        return jsonify({"error": "Database error"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/download_excel')
def download_excel():
    conn = get_db_connection()
 
    df1 =pd.read_sql('SELECT DISTINCT  "" as `Column Name`, "" as `GenericKey`, asn_number as `ASN/Receipt`,owner as `Owner`,status as `Receipt Status` FROM inv_staging', conn)
    
    df2 = pd.read_sql('SELECT "" as `Column Name`, "" as `GenericKey`,asn_number as `ASN/Receipt`,sku as `Item`,owner as `Owner`,line_number as `Line #`,qty as `Expected Qty`,uom as `UOM`,`case` as `LPN`,location as `LOCATION` FROM inv_staging', conn)
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