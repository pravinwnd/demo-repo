import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# Database setup
conn = sqlite3.connect('expenses.db')
c = conn.cursor()


# Create the expenses table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS expenses 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, description TEXT, type TEXT, amount REAL)''')

# Expense types
expense_types = ['Grocery', 'Travel', 'Fixed Expense', 'Savings', 'Fuel', 'Credits Given', 'Charity', 'Hotel']

# Function to add expense to the database
def add_expense(date, description, expense_type, amount):
    c.execute('INSERT INTO expenses (date, description, type, amount) VALUES (?, ?, ?, ?)', 
              (date.strftime('%Y-%m-%d'), description, expense_type, amount))  # Ensure date is in correct format
    conn.commit()

# Function to fetch all expenses from the database
def get_expenses(month=None):
    if month:
        c.execute('SELECT * FROM expenses WHERE strftime("%m", date) = ?', (month,))
    else:
        c.execute('SELECT * FROM expenses')
    return pd.DataFrame(c.fetchall(), columns=['ID', 'Date', 'Description', 'Type', 'Amount'])

# Function to edit an expense
def edit_expense(expense_id, date, description, expense_type, amount):
    c.execute('UPDATE expenses SET date=?, description=?, type=?, amount=? WHERE id=?', 
              (date.strftime('%Y-%m-%d'), description, expense_type, amount, expense_id))  # Correct format
    conn.commit()

# Function to delete an expense
def delete_expense(expense_id):
    c.execute('DELETE FROM expenses WHERE id=?', (expense_id,))
    conn.commit()

# Function to calculate total expenses for each type
def get_total_expenses_by_type():
    c.execute('SELECT type, SUM(amount) FROM expenses GROUP BY type')
    return pd.DataFrame(c.fetchall(), columns=['Type', 'Total Amount'])

# Streamlit App UI
st.title('Expense Tracker')

# Create two columns for layout
left_col, right_col = st.columns([2, 1])

# Left column: Input section for adding a new expense
with left_col:
    st.header('Add New Expense')
    expense_date = st.date_input('Date', date.today())
    expense_description = st.text_input('Description')
    expense_type = st.selectbox('Type', expense_types)
    expense_amount = st.number_input('Amount (INR)', min_value=0.0, format='%f')

    if st.button('Add Expense'):
        if expense_description and expense_amount > 0:
            add_expense(expense_date, expense_description, expense_type, expense_amount)
            st.success('Expense added successfully!')
        else:
            st.error('Please fill all the fields correctly.')

    # Filter by month and display expenses
    st.header('View Expenses')
    filter_month = st.selectbox('Filter by Month', ['All'] + [pd.date_range(start='2023-01', end=date.today(), freq='M').strftime('%B')[i] for i in range((date.today().month))])

    if filter_month == 'All':
        df_expenses = get_expenses()
    else:
        # Get the month number from the selected month name
        month_number = pd.to_datetime(filter_month, format='%B').month
        df_expenses = get_expenses(month=month_number)

    st.write('Expenses:')
    st.dataframe(df_expenses)

# Right column: Section for setting thresholds using sliders
with right_col:
    st.header('Set Thresholds')
    thresholds = {}
    for expense_type in expense_types:
        thresholds[expense_type] = st.slider(f'{expense_type} (INR)', min_value=0, max_value=50000, step=100, value=10000)

# Display total expenses by type and compare with user-defined thresholds
st.header('Expense Summary by Type')

total_expenses_by_type = get_total_expenses_by_type()

for index, row in total_expenses_by_type.iterrows():
    expense_type = row['Type']
    total_amount = row['Total Amount']
    threshold = thresholds.get(expense_type, 0)

    st.write(f'{expense_type}: ₹{total_amount} / ₹{threshold}')
    
    # Check if the threshold is breached and display a warning message
    if total_amount > threshold:
        st.warning(f'You have exceeded the threshold for {expense_type}! You spent ₹{total_amount}, which is over the set threshold of ₹{threshold}.')

# Edit and Delete functionality
st.header('Edit/Delete Expenses')
expense_id = st.selectbox('Select Expense to Edit/Delete', options=df_expenses['ID'] if not df_expenses.empty else [None])
if expense_id is not None:
    expense_data = df_expenses[df_expenses['ID'] == expense_id]

    # Ensure we have a single row for editing
    if not expense_data.empty:
        expense_data = expense_data.iloc[0]
        
        # Display current values for editing
        st.write(f"Current Values: {expense_data.to_dict()}")
        
        # Use the correct format for the date
        edit_date = st.date_input('Edit Date', value=pd.to_datetime(expense_data['Date']).date())
        edit_description = st.text_input('Edit Description', value=expense_data['Description'])
        edit_type = st.selectbox('Edit Type', expense_types, index=expense_types.index(expense_data['Type']))
        edit_amount = st.number_input('Edit Amount (INR)', min_value=0.0, value=expense_data['Amount'], format='%f')

        if st.button('Update Expense'):
            edit_expense(expense_id, edit_date, edit_description, edit_type, edit_amount)
            st.success('Expense updated successfully!')

        if st.button('Delete Expense'):
            delete_expense(expense_id)
            st.success('Expense deleted successfully!')

# Close the connection
conn.close()
