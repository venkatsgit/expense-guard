import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime, date
from io import BytesIO
import os



custom_categories = ["Other"]

# Database configuration
DB_CONFIG = {
    "host" : os.getenv("MYSQL_HOST", "host.docker.internal"),
    "user" : os.getenv("MYSQL_USER", "remote_user"),
    "password" : os.getenv("MYSQL_PASSWORD", "Str0ng@Pass123"),
    "database" :  os.getenv("MYSQL_DB", "expense_insights")
}

def get_db_conn():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        st.error(f"Error connecting to MySQL database: {e}")
        return None



def load_expenses(user_id=None):
    conn = get_db_conn()
    if conn is None:
        return pd.DataFrame()
    try:
        cursor = conn.cursor(dictionary=True)
        if user_id:
            cursor.execute("SELECT id, date, expense, currency_code, description, category FROM expenses WHERE user_id = %s ORDER BY id ASC", (user_id,))
        else:
            cursor.execute("SELECT id, date, expense, currency_code, description, category FROM expenses ORDER BY id ASC")

        result = cursor.fetchall()
        return pd.DataFrame(result)
    except Error as e:
        st.error(f"Error loading expenses: {e}")
        return pd.DataFrame()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def update_expense(expense_id, update_data):
    conn = get_db_conn()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        safe_data = {k: (v.item() if hasattr(v, "item") else v) for k, v in update_data.items()}

        set_clause = ", ".join([f"{key}=%s" for key in safe_data.keys()])
        query = f"UPDATE expenses SET {set_clause} WHERE id = %s"

        expense_id = expense_id.item() if hasattr(expense_id, "item") else expense_id
        params = list(safe_data.values()) + [expense_id]

        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        st.error(f"Error updating expense: {e}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def show(user_id=None):
    st.header("📊 Complete Expense Records", divider='rainbow')

    with st.spinner("Loading expenses..."):
        df = load_expenses(user_id)

    if df.empty:
        st.warning("No expenses found!")
        return

    df['date'] = pd.to_datetime(df['date']).dt.date

    #filters
    with st.expander("🔍 FILTERS", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            category_filter = st.selectbox(
                "Category",
                ["All"] + sorted(df['category'].dropna().unique().tolist())
            )
        with col2:
            date_range = st.date_input(
                "Date Range",
                value=[df['date'].min(), df['date'].max()],
                min_value=df['date'].min(),
                max_value=df['date'].max()
            )

    filtered_df = df.copy()

    if category_filter != "All":
        filtered_df = filtered_df[filtered_df['category'] == category_filter]

    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['date'] >= date_range[0]) &
            (filtered_df['date'] <= date_range[1])
        ]

    #pagination
    pag_col1, pag_col2, pag_col3 = st.columns([1, 3, 1])
    with pag_col1:
        items_per_page = st.selectbox("Items per page", [10, 25, 50, 100], index=1)
    total_pages = max(1, (len(filtered_df) // items_per_page) + (1 if len(filtered_df) % items_per_page else 0))

    with pag_col3:
        page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=1)

    start_idx = (page_number - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_df = filtered_df.iloc[start_idx:end_idx].copy()

    existing_categories = df['category'].dropna().unique().tolist()
    all_categories = sorted(list(set(custom_categories + existing_categories)))
    paginated_df.loc[:, "amount_display"] = paginated_df.apply(
        lambda row: f"{row['expense']:.2f} {row['currency_code']}", axis=1
    )

    #data table
    editable_columns = ["date", "description", "amount_display", "category"]
    edited_df = st.data_editor(
        paginated_df[editable_columns],
        use_container_width=True,
        column_config={
            "date": st.column_config.DateColumn("Date", disabled=True),
            "description": st.column_config.TextColumn("Description", disabled=True),
            "amount_display": st.column_config.TextColumn("Amount", disabled=True),
            "category": st.column_config.SelectboxColumn(
                "Category",
                options=all_categories,
                width="medium"
            )
        },
        key="expense_editor",
        hide_index=True
    )
    # Save changes
    if st.button("💾 Save Changes", use_container_width=True):
        if "expense_editor" in st.session_state:
            edited_rows = st.session_state.expense_editor.get("edited_rows", {})
            if edited_rows:
                success_count = 0
                for idx, changes in edited_rows.items():
                    expense_id = paginated_df.iloc[idx]['id']

                    category_change = {}
                    if "category" in changes:
                        category_change["category"] = changes["category"]

                    if category_change and update_expense(expense_id, category_change):
                        success_count += 1

                if success_count > 0:
                    st.success(f"Successfully updated {success_count} expense(s)")
                    st.cache_data.clear()
                else:
                    st.error("No expenses were updated")
            else:
                st.warning("No changes detected")

    # Summary section
    st.divider()
    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.metric("Total Expenses", f"{len(filtered_df):,}")

    with summary_col2:
        st.metric("Total Amount", f"{filtered_df['expense'].sum():,.2f}")

    with summary_col3:
        st.metric("Showing Records", f"{start_idx + 1}-{min(end_idx, len(filtered_df))} of {len(filtered_df)}")

    # Download buttons
    # st.divider()
    # dl_col1, dl_col2 = st.columns(2)
    #
    # with dl_col1:
    #     csv = filtered_df.to_csv(index=False).encode('utf-8')
    #     st.download_button(
    #         label="📥 Download CSV",
    #         data=csv,
    #         file_name="expenses.csv",
    #         mime="text/csv",
    #         use_container_width=True
    #     )
    #
    # with dl_col2:
    #     output = BytesIO()
    #     with pd.ExcelWriter(output, engine='openpyxl') as writer:
    #         filtered_df.to_excel(writer, index=False)
    #     excel_data = output.getvalue()
    #     st.download_button(
    #         label="📥 Download Excel",
    #         data=excel_data,
    #         file_name="expenses.xlsx",
    #         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    #         use_container_width=True
    #     )