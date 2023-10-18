import psycopg2
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridUpdateMode,GridOptionsBuilder
from sqlalchemy import create_engine

st.set_page_config(layout = 'wide')
update_mode_value = GridUpdateMode.__members__['GRID_CHANGED']

engine = create_engine('postgresql://postgres:spike@localhost:5432/postgres')
conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password="spike")

# Send a ping to confirm a successful connection
if conn.closed:
    print("db down")
else:
    print("db up")

@st.cache_data(ttl=600)
def get_data(soNumber):
  
    query = f"""WITH cte AS(
                SELECT id
                FROM public.salesorders
                where salesorders.salesorder = '{soNumber}'
    )
                
                SELECT measurement1,measurement2,measurement3,measurement4
                FROM public.inspectiondata
                WHERE inspectiondata.so_id = (SELECT id from CTE) """
    
    return pd.read_sql(query, con=engine)


@st.cache_data(ttl=30)
def get_foreign_key_value(soValue):
  with conn.cursor() as cur:
    cur.execute("""SELECT id FROM public.salesorders WHERE salesorders.salesorder = %(value)s """, {'value':soValue})
    idNumber = cur.fetchone()[0]
    conn.commit()

    return idNumber

def main():
    # Register your pages
    pages = {
        "Data Viewer": dataViewer,
        "Input Data": inspectionData,
    }

    st.sidebar.title("Production SOFC options")

    # Widget to select your page, you can choose between radio buttons or a selectbox
    page = st.sidebar.radio("Select your page", tuple(pages.keys()))
    #page = st.sidebar.selectbox("Select your page", tuple(pages.keys()))

    # Display the selected page
    pages[page]()

def dataViewer():
    st.title("Data viewer")
    soNumber = st.text_input("Write your SO number here")

    if st.button('Submit'):
        items = get_data(soNumber)

        # Print results.
        AgGrid(items)

def inspectionData():
    """Render a view of the data in editable form
    The editable bit is created by configure_default_column['editable']=True
    """
    st.title("Input Data")

    sales_order= st.text_input('Sales Order')
    m_equipment = st.text_input('Measurement equipment')
    df = pd.read_excel('productiondata.xlsx')
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, editable=True)
    gridOptions = gb.build()
    gridResponse = AgGrid(df,gridOptions=gridOptions,update_mode=update_mode_value,allow_unsafe_jscode=True)

    


    if st.button('Submit'):
        
        try:
            sales_order_data = {"salesOrder" : sales_order,
                                "measurementEquipment": m_equipment}
            salesOrderDf = pd.DataFrame([sales_order_data])
            salesOrderDf.to_sql('salesOrders', engine, if_exists='append', index=False)
        except Exception as e:
           ""
        soID = get_foreign_key_value(sales_order)
        gridResponse['data']['so_id'] = soID
        gridResponse['data'].to_sql(
           "inspectiondata", engine, if_exists='append', index=False)
    

if __name__ == "__main__":
    main()