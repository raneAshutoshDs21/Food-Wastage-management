import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Page configuration - MUST BE FIRST
st.set_page_config(
    page_title="Food Donation Management System",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
@st.cache_resource
def init_connection():
    return sqlite3.connect('food_donation.db', check_same_thread=False)

conn = init_connection()

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2E8B57;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def execute_query(query, params=None):
    """Execute SQL query and return results"""
    try:
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return pd.DataFrame()

def execute_insert_update_delete(query, params=None):
    """Execute insert, update, or delete queries"""
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return False

# Sidebar navigation
st.sidebar.title("🍽️ Navigation")
page = st.sidebar.selectbox("Choose a page:", [
    "Dashboard", 
    "Food Listings", 
    "Providers & Receivers", 
    "Claims Management", 
    "Analytics", 
    "CRUD Operations"
])

# Main header
st.markdown('<h1 class="main-header">Food Donation Management System</h1>', unsafe_allow_html=True)

# Dashboard Page
if page == "Dashboard":
    st.header("📊 Dashboard Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_providers = execute_query("SELECT COUNT(*) as count FROM providers")
        st.metric("Total Providers", total_providers['count'].iloc[0] if not total_providers.empty else 0)
    
    with col2:
        total_receivers = execute_query("SELECT COUNT(*) as count FROM receivers")
        st.metric("Total Receivers", total_receivers['count'].iloc[0] if not total_receivers.empty else 0)
    
    with col3:
        total_food_items = execute_query("SELECT COUNT(*) as count FROM food_listings")
        st.metric("Food Listings", total_food_items['count'].iloc[0] if not total_food_items.empty else 0)
    
    with col4:
        total_claims = execute_query("SELECT COUNT(*) as count FROM claims")
        st.metric("Total Claims", total_claims['count'].iloc[0] if not total_claims.empty else 0)
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Providers by Type")
        provider_types = execute_query("SELECT Type, COUNT(*) as count FROM providers GROUP BY Type")
        if not provider_types.empty:
            fig = px.pie(provider_types, values='count', names='Type', 
                        title="Distribution of Provider Types")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Claims by Status")
        claim_status = execute_query("SELECT Status, COUNT(*) as count FROM claims GROUP BY Status")
        if not claim_status.empty:
            fig = px.bar(claim_status, x='Status', y='count', 
                        title="Claims Status Distribution")
            st.plotly_chart(fig, use_container_width=True)

# Food Listings Page
elif page == "Food Listings":
    st.header("🥘 Food Listings")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cities = execute_query("SELECT DISTINCT Location FROM food_listings ORDER BY Location")
        city_filter = st.selectbox("Filter by City:", 
                                  ["All"] + cities['Location'].tolist() if not cities.empty else ["All"])
    
    with col2:
        food_types = execute_query("SELECT DISTINCT Food_Type FROM food_listings ORDER BY Food_Type")
        food_type_filter = st.selectbox("Filter by Food Type:", 
                                       ["All"] + food_types['Food_Type'].tolist() if not food_types.empty else ["All"])
    
    with col3:
        meal_types = execute_query("SELECT DISTINCT Meal_Type FROM food_listings ORDER BY Meal_Type")
        meal_type_filter = st.selectbox("Filter by Meal Type:", 
                                       ["All"] + meal_types['Meal_Type'].tolist() if not meal_types.empty else ["All"])
    
    # Build query with filters
    query = """
    SELECT fl.*, p.Name as Provider_Name, p.Contact as Provider_Contact
    FROM food_listings fl
    JOIN providers p ON fl.Provider_ID = p.Provider_ID
    WHERE 1=1
    """
    params = []
    
    if city_filter != "All":
        query += " AND fl.Location = ?"
        params.append(city_filter)
    
    if food_type_filter != "All":
        query += " AND fl.Food_Type = ?"
        params.append(food_type_filter)
    
    if meal_type_filter != "All":
        query += " AND fl.Meal_Type = ?"
        params.append(meal_type_filter)
    
    query += " ORDER BY fl.Expiry_Date"
    
    # Display results
    food_listings = execute_query(query, params if params else None)
    
    if not food_listings.empty:
        st.subheader(f"Found {len(food_listings)} food listings")
        
        # Display as cards
        for idx, row in food_listings.iterrows():
            with st.expander(f"🍽️ {row['Food_Name']} - {row['Quantity']} units"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Provider:** {row['Provider_Name']}")
                    st.write(f"**Location:** {row['Location']}")
                    st.write(f"**Food Type:** {row['Food_Type']}")
                    st.write(f"**Meal Type:** {row['Meal_Type']}")
                
                with col2:
                    st.write(f"**Quantity:** {row['Quantity']}")
                    st.write(f"**Expiry Date:** {row['Expiry_Date']}")
                    st.write(f"**Contact:** {row['Provider_Contact']}")
                    
                    if st.button(f"Claim This Food", key=f"claim_{row['Food_ID']}"):
                        st.session_state[f'claim_food_id'] = row['Food_ID']
                        st.rerun()
    else:
        st.info("No food listings found with the selected filters.")

# Providers & Receivers Page
elif page == "Providers & Receivers":
    st.header("🏪 Providers & Receivers")
    
    tab1, tab2 = st.tabs(["Providers", "Receivers"])
    
    with tab1:
        st.subheader("Food Providers")
        
        # City filter for providers
        provider_cities = execute_query("SELECT DISTINCT City FROM providers ORDER BY City")
        provider_city_filter = st.selectbox("Filter Providers by City:", 
                                           ["All"] + provider_cities['City'].tolist() if not provider_cities.empty else ["All"])
        
        # Provider query
        if provider_city_filter == "All":
            providers = execute_query("SELECT * FROM providers ORDER BY Name")
        else:
            providers = execute_query("SELECT * FROM providers WHERE City = ? ORDER BY Name", 
                                    [provider_city_filter])
        
        if not providers.empty:
            st.dataframe(providers, use_container_width=True)
            
            # Provider statistics
            st.subheader("Provider Statistics")
            provider_stats = execute_query("""
                SELECT p.Type, COUNT(fl.Food_ID) as Total_Foods, SUM(fl.Quantity) as Total_Quantity
                FROM providers p
                LEFT JOIN food_listings fl ON p.Provider_ID = fl.Provider_ID
                GROUP BY p.Type
                ORDER BY Total_Quantity DESC
            """)
            
            if not provider_stats.empty:
                fig = px.bar(provider_stats, x='Type', y='Total_Quantity',
                            title="Total Food Quantity by Provider Type")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No providers found.")
    
    with tab2:
        st.subheader("Food Receivers")
        
        # City filter for receivers
        receiver_cities = execute_query("SELECT DISTINCT City FROM receivers ORDER BY City")
        receiver_city_filter = st.selectbox("Filter Receivers by City:", 
                                           ["All"] + receiver_cities['City'].tolist() if not receiver_cities.empty else ["All"])
        
        # Receiver query
        if receiver_city_filter == "All":
            receivers = execute_query("SELECT * FROM receivers ORDER BY Name")
        else:
            receivers = execute_query("SELECT * FROM receivers WHERE City = ? ORDER BY Name", 
                                    [receiver_city_filter])
        
        if not receivers.empty:
            st.dataframe(receivers, use_container_width=True)
            
            # Receiver statistics
            st.subheader("Receiver Statistics")
            receiver_stats = execute_query("""
                SELECT r.Type, COUNT(c.Claim_ID) as Total_Claims
                FROM receivers r
                LEFT JOIN claims c ON r.Receiver_ID = c.Receiver_ID
                GROUP BY r.Type
                ORDER BY Total_Claims DESC
            """)
            
            if not receiver_stats.empty:
                fig = px.pie(receiver_stats, values='Total_Claims', names='Type',
                            title="Claims Distribution by Receiver Type")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No receivers found.")

# Claims Management Page
elif page == "Claims Management":
    st.header("📋 Claims Management")
    
    # Claim food if triggered from Food Listings
    if 'claim_food_id' in st.session_state:
        st.subheader("🆕 Make a New Claim")
        
        food_id = st.session_state['claim_food_id']
        
        # Get food details
        food_details = execute_query("SELECT * FROM food_listings WHERE Food_ID = ?", [food_id])
        
        if not food_details.empty:
            food = food_details.iloc[0]
            st.write(f"**Claiming:** {food['Food_Name']} ({food['Quantity']} units)")
            
            # Get receivers for selection
            receivers = execute_query("SELECT Receiver_ID, Name FROM receivers ORDER BY Name")
            
            if not receivers.empty:
                receiver_id = st.selectbox("Select Receiver:", 
                                         options=receivers['Receiver_ID'].tolist(),
                                         format_func=lambda x: receivers[receivers['Receiver_ID'] == x]['Name'].iloc[0])
                
                if st.button("Submit Claim"):
                    # Insert new claim
                    claim_query = """
                        INSERT INTO claims (Food_ID, Receiver_ID, Status, Timestamp)
                        VALUES (?, ?, 'Pending', ?)
                    """
                    
                    if execute_insert_update_delete(claim_query, 
                                                   [food_id, receiver_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')]):
                        st.success("✅ Claim submitted successfully!")
                        del st.session_state['claim_food_id']
                        st.rerun()
        
        if st.button("Cancel Claim"):
            del st.session_state['claim_food_id']
            st.rerun()
    
    st.divider()
    
    # Claims overview
    st.subheader("All Claims")
    
    claims_query = """
        SELECT c.Claim_ID, c.Status, c.Timestamp,
               fl.Food_Name, fl.Quantity, fl.Food_Type,
               r.Name as Receiver_Name, r.Type as Receiver_Type,
               p.Name as Provider_Name
        FROM claims c
        JOIN food_listings fl ON c.Food_ID = fl.Food_ID
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
        JOIN providers p ON fl.Provider_ID = p.Provider_ID
        ORDER BY c.Timestamp DESC
    """
    
    claims = execute_query(claims_query)
    
    if not claims.empty:
        # Status filter
        status_filter = st.selectbox("Filter by Status:", 
                                   ["All", "Pending", "Completed", "Cancelled"])
        
        if status_filter != "All":
            filtered_claims = claims[claims['Status'] == status_filter]
        else:
            filtered_claims = claims
        
        st.dataframe(filtered_claims, use_container_width=True)
        
        # Update claim status
        st.subheader("Update Claim Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            claim_ids = filtered_claims['Claim_ID'].tolist()
            selected_claim = st.selectbox("Select Claim ID:", claim_ids)
        
        with col2:
            new_status = st.selectbox("New Status:", ["Pending", "Completed", "Cancelled"])
        
        with col3:
            st.write("")  # Space
            st.write("")  # Space
            if st.button("Update Status"):
                update_query = "UPDATE claims SET Status = ? WHERE Claim_ID = ?"
                if execute_insert_update_delete(update_query, [new_status, selected_claim]):
                    st.success("✅ Claim status updated!")
                    st.rerun()
    else:
        st.info("No claims found.")

# Analytics Page
elif page == "Analytics":
    st.header("📈 Dashboard Analytics")
    
    # High-level insights for dashboard
    st.subheader("📊 Key Performance Indicators")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Food waste prevention impact
        total_food = execute_query("SELECT SUM(Quantity) as total FROM food_listings")
        claimed_food = execute_query("""
            SELECT SUM(fl.Quantity) as total 
            FROM food_listings fl 
            JOIN claims c ON fl.Food_ID = c.Food_ID 
            WHERE c.Status = 'Completed'
        """)
        
        if not total_food.empty and not claimed_food.empty:
            total_val = total_food['total'].iloc[0] or 0
            claimed_val = claimed_food['total'].iloc[0] or 0
            waste_prevented = (claimed_val / total_val * 100) if total_val > 0 else 0
            st.metric("Food Waste Prevented", f"{waste_prevented:.1f}%", 
                     help="Percentage of listed food successfully claimed")
    
    with col2:
        # Average response time
        avg_response = execute_query("""
            SELECT AVG(julianday('now') - julianday(Timestamp)) as avg_days
            FROM claims 
            WHERE Status = 'Completed'
        """)
        
        if not avg_response.empty and avg_response['avg_days'].iloc[0]:
            st.metric("Avg Response Time", f"{avg_response['avg_days'].iloc[0]:.1f} days",
                     help="Average time to complete claims")
        else:
            st.metric("Avg Response Time", "N/A")
    
    with col3:
        # Active listings
        active_listings = execute_query("""
            SELECT COUNT(*) as count 
            FROM food_listings fl
            LEFT JOIN claims c ON fl.Food_ID = c.Food_ID AND c.Status = 'Completed'
            WHERE c.Food_ID IS NULL
        """)
        
        if not active_listings.empty:
            st.metric("Active Listings", active_listings['count'].iloc[0],
                     help="Food listings not yet claimed")
    
    st.divider()
    
    # Visual Analytics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏙️ City Distribution")
        city_stats = execute_query("""
            SELECT 
                Location as City,
                COUNT(*) as Food_Listings,
                SUM(Quantity) as Total_Quantity
            FROM food_listings
            GROUP BY Location
            ORDER BY Total_Quantity DESC
        """)
        
        if not city_stats.empty:
            fig = px.bar(city_stats, x='City', y='Total_Quantity',
                        title="Food Quantity by City")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for city distribution")
    
    with col2:
        st.subheader("🍽️ Food Types")
        food_type_stats = execute_query("""
            SELECT Food_Type, COUNT(*) as Count
            FROM food_listings
            GROUP BY Food_Type
            ORDER BY Count DESC
        """)
        
        if not food_type_stats.empty:
            fig = px.pie(food_type_stats, values='Count', names='Food_Type',
                        title="Food Types Distribution")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for food types")
    
    st.divider()
    
    # Provider Performance
    st.subheader("🏪 Top Performing Providers")
    top_providers = execute_query("""
        SELECT 
            p.Name,
            p.Type,
            COUNT(fl.Food_ID) as Total_Listings,
            SUM(fl.Quantity) as Total_Quantity,
            COUNT(c.Claim_ID) as Total_Claims
        FROM providers p
        LEFT JOIN food_listings fl ON p.Provider_ID = fl.Provider_ID
        LEFT JOIN claims c ON fl.Food_ID = c.Food_ID
        GROUP BY p.Provider_ID, p.Name, p.Type
        ORDER BY Total_Quantity DESC
        LIMIT 10
    """)
    
    if not top_providers.empty:
        st.dataframe(top_providers, use_container_width=True)
    else:
        st.info("No provider data available")
    
    # Recent Activity
    st.subheader("📅 Recent Activity")
    recent_claims = execute_query("""
        SELECT 
            c.Timestamp,
            fl.Food_Name,
            r.Name as Receiver_Name,
            c.Status
        FROM claims c
        JOIN food_listings fl ON c.Food_ID = fl.Food_ID
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
        ORDER BY c.Timestamp DESC
        LIMIT 10
    """)
    
    if not recent_claims.empty:
        st.dataframe(recent_claims, use_container_width=True)
    else:
        st.info("No recent claims found")
    
    # Quick Stats
    st.subheader("⚡ Quick Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        expiring_soon = execute_query("""
            SELECT COUNT(*) as count 
            FROM food_listings 
            WHERE DATE(Expiry_Date) <= DATE('now', '+3 days')
        """)
        if not expiring_soon.empty:
            st.metric("Expiring Soon", expiring_soon['count'].iloc[0], 
                     help="Items expiring within 3 days")
    
    with col2:
        pending_claims = execute_query("SELECT COUNT(*) as count FROM claims WHERE Status = 'Pending'")
        if not pending_claims.empty:
            st.metric("Pending Claims", pending_claims['count'].iloc[0])
    
    with col3:
        completed_today = execute_query("""
            SELECT COUNT(*) as count 
            FROM claims 
            WHERE Status = 'Completed' AND DATE(Timestamp) = DATE('now')
        """)
        if not completed_today.empty:
            st.metric("Completed Today", completed_today['count'].iloc[0])
    
    with col4:
        unique_receivers = execute_query("""
            SELECT COUNT(DISTINCT Receiver_ID) as count 
            FROM claims
        """)
        if not unique_receivers.empty:
            st.metric("Active Receivers", unique_receivers['count'].iloc[0])
    
    st.info("💡 For detailed SQL analysis and comprehensive reporting, check the separate analytics notebook.")

# CRUD Operations Page
elif page == "CRUD Operations":
    st.header("⚙️ CRUD Operations")
    
    operation = st.selectbox("Select Operation:", ["Create", "Read", "Update", "Delete"])
    table = st.selectbox("Select Table:", ["providers", "receivers", "food_listings", "claims"])
    
    if operation == "Create":
        st.subheader(f"Add New {table.title().rstrip('s')}")
        
        if table == "providers":
            with st.form("add_provider"):
                name = st.text_input("Provider Name*")
                type_val = st.selectbox("Type*", ["Restaurant", "Grocery Store", "Supermarket", "Bakery", "Other"])
                address = st.text_area("Address*")
                city = st.text_input("City*")
                contact = st.text_input("Contact*")
                
                if st.form_submit_button("Add Provider"):
                    if all([name, type_val, address, city, contact]):
                        query = "INSERT INTO providers (Name, Type, Address, City, Contact) VALUES (?, ?, ?, ?, ?)"
                        if execute_insert_update_delete(query, [name, type_val, address, city, contact]):
                            st.success("✅ Provider added successfully!")
                    else:
                        st.error("Please fill all required fields.")
        
        elif table == "receivers":
            with st.form("add_receiver"):
                name = st.text_input("Receiver Name*")
                type_val = st.selectbox("Type*", ["NGO", "Community Center", "Individual", "Orphanage", "Other"])
                city = st.text_input("City*")
                contact = st.text_input("Contact*")
                
                if st.form_submit_button("Add Receiver"):
                    if all([name, type_val, city, contact]):
                        query = "INSERT INTO receivers (Name, Type, City, Contact) VALUES (?, ?, ?, ?)"
                        if execute_insert_update_delete(query, [name, type_val, city, contact]):
                            st.success("✅ Receiver added successfully!")
                    else:
                        st.error("Please fill all required fields.")
        
        elif table == "food_listings":
            with st.form("add_food_listing"):
                food_name = st.text_input("Food Name*")
                quantity = st.number_input("Quantity*", min_value=1, value=1)
                expiry_date = st.date_input("Expiry Date*")
                
                # Get providers for selection
                providers = execute_query("SELECT Provider_ID, Name FROM providers ORDER BY Name")
                if not providers.empty:
                    provider_id = st.selectbox("Provider*", 
                                             options=providers['Provider_ID'].tolist(),
                                             format_func=lambda x: providers[providers['Provider_ID'] == x]['Name'].iloc[0])
                    
                    # Get provider type
                    provider_type = execute_query("SELECT Type FROM providers WHERE Provider_ID = ?", [provider_id])
                    location = st.text_input("Location*")
                    food_type = st.selectbox("Food Type*", ["Vegetarian", "Non-Vegetarian", "Vegan"])
                    meal_type = st.selectbox("Meal Type*", ["Breakfast", "Lunch", "Dinner", "Snacks"])
                    
                    if st.form_submit_button("Add Food Listing"):
                        if all([food_name, quantity, expiry_date, location]):
                            query = """
                                INSERT INTO food_listings 
                                (Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """
                            params = [food_name, quantity, expiry_date.strftime('%Y-%m-%d'), provider_id, 
                                    provider_type['Type'].iloc[0], location, food_type, meal_type]
                            
                            if execute_insert_update_delete(query, params):
                                st.success("✅ Food listing added successfully!")
                        else:
                            st.error("Please fill all required fields.")
                else:
                    st.warning("No providers found. Please add providers first.")
    
    elif operation == "Read":
        st.subheader(f"View {table.title()}")
        
        data = execute_query(f"SELECT * FROM {table} ORDER BY 1")
        if not data.empty:
            st.dataframe(data, use_container_width=True)
            st.info(f"Total records: {len(data)}")
        else:
            st.info(f"No records found in {table}")
    
    elif operation == "Update":
        st.subheader(f"Update {table.title().rstrip('s')}")
        
        # Get records for selection
        data = execute_query(f"SELECT * FROM {table} ORDER BY 1")
        if not data.empty:
            # Select record to update
            record_id = st.selectbox(f"Select {table.rstrip('s').title()} to Update:", 
                                   options=data.iloc[:, 0].tolist(),
                                   format_func=lambda x: f"ID: {x} - {data[data.iloc[:, 0] == x].iloc[0, 1]}")
            
            # Get current record
            current_record = data[data.iloc[:, 0] == record_id].iloc[0]
            
            # Update form based on table
            if table == "providers":
                with st.form("update_provider"):
                    name = st.text_input("Provider Name", value=current_record['Name'])
                    type_val = st.selectbox("Type", ["Restaurant", "Grocery Store", "Supermarket", "Bakery", "Other"],
                                          index=["Restaurant", "Grocery Store", "Supermarket", "Bakery", "Other"].index(current_record['Type'])
                                          if current_record['Type'] in ["Restaurant", "Grocery Store", "Supermarket", "Bakery", "Other"] else 0)
                    address = st.text_area("Address", value=current_record['Address'])
                    city = st.text_input("City", value=current_record['City'])
                    contact = st.text_input("Contact", value=current_record['Contact'])
                    
                    if st.form_submit_button("Update Provider"):
                        query = "UPDATE providers SET Name=?, Type=?, Address=?, City=?, Contact=? WHERE Provider_ID=?"
                        if execute_insert_update_delete(query, [name, type_val, address, city, contact, record_id]):
                            st.success("✅ Provider updated successfully!")
                            st.rerun()
        else:
            st.info(f"No records found in {table}")
    
    elif operation == "Delete":
        st.subheader(f"Delete {table.title().rstrip('s')}")
        st.warning("⚠️ This operation cannot be undone!")
        
        # Get records for selection
        data = execute_query(f"SELECT * FROM {table} ORDER BY 1")
        if not data.empty:
            record_id = st.selectbox(f"Select {table.rstrip('s').title()} to Delete:", 
                                   options=data.iloc[:, 0].tolist(),
                                   format_func=lambda x: f"ID: {x} - {data[data.iloc[:, 0] == x].iloc[0, 1]}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"🗑️ Delete {table.rstrip('s').title()}", type="primary"):
                    primary_key = data.columns[0]
                    query = f"DELETE FROM {table} WHERE {primary_key} = ?"
                    if execute_insert_update_delete(query, [record_id]):
                        st.success(f"✅ {table.rstrip('s').title()} deleted successfully!")
                        st.rerun()