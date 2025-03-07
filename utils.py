import pandas as pd
from fuzzywuzzy import process
import camelot

# Hard-coded Vehicle Charges DataFrame
charges_df = pd.read_csv('vehicle charges.csv')
charges_df.rename(columns={"20 feet": "20 FEET", "22 feet": "22 FEET", "32 feet": "32 FEET"}, inplace=True)

def safe_int(value):
    """Convert to integer safely, return 0 if conversion fails."""
    try:
        return int(float(str(value).replace(',', '')))
    except (ValueError, TypeError):
        return 0

def get_charges(destination: str, container_type: str):
    """Fetch the charge based on the destination and container type."""
    try:
        choices = charges_df['Destination'].unique()
        best_match, score = process.extractOne(destination, choices)

        if score < 85:
            return None, f"Destination '{destination}' is not in Agreement"

        if container_type not in charges_df.columns:
            return None, f"Vehicle type {container_type} is not in Agreement"

        # Get charge
        result = charges_df.loc[charges_df['Destination'] == best_match, container_type]
        
        if result.empty:
            return None, f"Charge not found for Destination: {best_match}, Vehicle type: {container_type}"

        return int(result.iloc[0]), None

    except Exception as e:
        return None, f"Error: {e}"

def calculate_price(row):
    """Calculate the total price including halting/unloading charges."""
    charge, remark = get_charges(row['Destination'], row['Vehicle Type'])

    halting_charge = safe_int(row.get('Halting/Unloading Charges', 0))

    total_price = (charge if charge is not None else 0) + halting_charge
    return int(total_price), remark

def process_pdf(file_path):
    """Extracts data from a PDF and processes it into a DataFrame."""
    
    tables = camelot.read_pdf(file_path, pages="all", flavor='lattice')

    df_list = []
    for i in range(len(tables)):
        df = tables[i].df.iloc[1:-2, :]
        df_list.append(df)

    if not df_list:
        return pd.DataFrame(), {}

    final_table = pd.concat(df_list, ignore_index=True)
    final_table.columns = final_table.iloc[0]  
    final_table = final_table[1:].reset_index(drop=True)

    for col in final_table.columns:
        if "Halting" in col and "Charges" in col:
            final_table.rename(columns={col: "Halting/Unloading Charges"}, inplace=True)
            break

    final_table[['Our Calculated Price', 'Remark']] = final_table.apply(
        lambda row: pd.Series(calculate_price(row)), axis=1
    )

    final_table["Our Calculated Price"] = final_table["Our Calculated Price"].astype(int)

    final_table['benifit'] = final_table.apply(
        lambda row: "-" if safe_int(row["Total Amount"]) == safe_int(row["Our Calculated Price"]) 
        else (safe_int(row["Our Calculated Price"]) - safe_int(row["Total Amount"])) 
        if safe_int(row["Our Calculated Price"]) > safe_int(row["Total Amount"]) 
        else "-", 
        axis=1
    )

    final_table['loss'] = final_table.apply(
        lambda row: "-" if round(safe_int(row["Total Amount"])) == round(safe_int(row["Our Calculated Price"])) 
        else (safe_int(row["Our Calculated Price"]) - safe_int(row["Total Amount"])) 
        if safe_int(row["Our Calculated Price"]) < safe_int(row["Total Amount"])
        else "-", 
        axis=1
    )

    # Extract totals
    cal_totals = final_table[~final_table["Sr. No"].str.match(r"^\d+$")]
    totals_split = cal_totals["Sr. No"].str.split("\n", expand=True)

    totals_dict = dict(zip(totals_split[0], totals_split[1]))

    return final_table, totals_dict