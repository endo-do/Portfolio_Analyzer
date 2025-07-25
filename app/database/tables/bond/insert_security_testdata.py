from datetime import date
from app.api.get_info import get_info
from app.api.get_eod import get_eod
from app.database.helpers.fetch_one import fetch_one
from app.database.helpers.fetch_all import fetch_all
from app.database.helpers.execute_change_query import execute_change_query

def get_category_mapping():
        rows = fetch_all("SELECT bondcategoryid, bondcategoryname FROM bondcategory", dictionary=True)
        return {row['bondcategoryname']: row['bondcategoryid'] for row in rows}

def get_currency_mapping():
        rows = fetch_all("SELECT currencyid, currencycode FROM currency", dictionary=True)
        return {row['currencycode']: row['currencyid'] for row in rows}

def insert_test_stocks(symbols):
    """
    Inserts or updates stocks in the DB using your existing functions get_info and get_eod.
    
    Args:
        symbols (list of str): List of ticker symbols to insert.
    """

    category_map = get_category_mapping()
    currency_map = get_currency_mapping()

    def map_category_to_id(category_name):
        return category_map.get(category_name, category_map.get('Other'))

    def map_currency_to_id(currency_code):
        return currency_map.get(currency_code, currency_map.get('USD'))


    for symbol in symbols:
        info = get_info(symbol)
        eod = get_eod(symbol)

        # fallback if info is empty (error handling)
        if not info:
            print(f"Skipping {symbol}: no info found")
            continue

        bondname = info.get("name", "")
        bondcategoryid = map_category_to_id(info.get("category"))
        bondcurrencyid = map_currency_to_id(info.get("currency"))
        bondcountry = info.get("country", "")
        bondwebsite = info.get("website", "")
        bondindustry = info.get("industry", "")
        bondsector = info.get("sector", "")
        bonddescription = info.get("description", "")

        # Check if bond exists
        existing_bond = fetch_one("""SELECT bondid FROM bond WHERE bondsymbol = %s""", (symbol,))

        # Insert new bond
        query = """
            INSERT INTO bond (
                bondname, bondsymbol, bondcategoryid, bondcurrencyid,
                bondcountry, bondwebsite, bondindustry, bondsector, bonddescription
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_change_query(query, (
            bondname, symbol, bondcategoryid, bondcurrencyid,
            bondcountry, bondwebsite, bondindustry, bondsector, bonddescription))

        # Get bondid
        bondid = fetch_one("""SELECT bondid FROM bond WHERE bondsymbol = %s""", (symbol,), dictionary=True)['bondid']

        if eod is not None:
            query = """INSERT INTO bonddata (bondid, bonddatalogtime, bondrate) VALUES (%s, %s, %s)"""
            execute_change_query(query, (bondid, date.today(), eod))

        print(f"Processed {symbol}")

    # Update securities update status
    execute_change_query("""UPDATE status SET securities = %s WHERE id = 1""", (date.today(),))

    print("Finished inserting/updating test stocks.")
