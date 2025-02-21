import duckdb
from nomic import atlas

# This script is used to create an Atlas map from the Enron emails.
# It uses DuckDB to read the emails from the Parquet file and then
# uses the Atlas API to create a map.

# The first time you run this script, you might need to authenticate
# with atlas and store your credentials. This is done with
# $ nomic login

con = duckdb.connect(":memory:")
con.query(""" CREATE TABLE emails AS SELECT * FROM parquet_scan('emails.parquet') """)

# This dataset contains a large number of duplicate emails.
# When all the metadata is the same, we only want to show one of them, the earliest.
# Also, we replace any missing values with empty strings, and get the domain
# of the sender as a separate field.
filtered_emails = con.query(
    """
      SELECT "_text" "text",
      COALESCE(arbitrary("From"), '') "From",
      COALESCE(arbitrary("To"), '') "To",
      COALESCE(arbitrary("X-From"), '') "X-From",
      COALESCE(arbitrary("X-To"), '') "X-To",
      COALESCE(arbitrary("X-cc"), '') "X-cc",
      COALESCE(arbitrary("X-Origin"), '') "X-Origin",
      COALESCE(arbitrary(string_split_regex("from", '@')[2]), '') "from-domain", 
      arbitrary(_user) "user",
      arbitrary("Subject") "Subject",
      arbitrary(_folder) folder,
      arbitrary("Message-ID") "Message-ID",
      FIRST(CASE WHEN (timestamp < '1997-01-01' OR timestamp > '2003-01-01') THEN '1997-01-01 01:00:00' ELSE timestamp END)::TIMESTAMP as "timestamp",
      COUNT(*) copies FROM emails
      GROUP BY ALL ORDER BY copies DESC"""
).arrow()

# This sends the data to Atlas
# The identifier needs to be changed if multiple runs are done.
response = atlas.map_data(
    data=filtered_emails.to_pylist(),
    indexed_field="text",
    is_public=True,
    identifier="Enron Emails",
    description="A map of the de-duplicated emails from the Enron dataset",
)
