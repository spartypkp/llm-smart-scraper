from typing import List, Optional, Dict, Any
import tiktoken
import psycopg
import json
import os

from psycopg.rows import class_row, dict_row
from typing import Optional, List, Any, Dict, Callable, Tuple, Type, Union
from openai import OpenAI
from anthropic import Anthropic
from anthropic.types import MessageParam

from pydantic import BaseModel, Field, model_validator
from datetime import datetime



from psycopg import sql

# ===== Database Functions =====
def db_connect(row_factory=None):
    """ Connect to the PostgreSQL database server. Optionally provide a pyscopg3 row factory to add type information to the returned rows. """
    conn = None
    try:
        # # connect to the local PostgreSQL server
        db_name = os.getenv("DB_NAME")
        db_host = os.getenv("DB_HOST")
        db_username = os.getenv("DB_USERNAME")
        db_password = os.getenv("DB_PASSWORD")
        db_port = os.getenv("DB_PORT")

        # connect to the Supabase PostgreSQL server
        # db_name = os.getenv("SUPABASE_DB_NAME")
        # db_host = os.getenv("SUPABASE_DB_HOST")
        # db_username = os.getenv("SUPABASE_DB_USERNAME")
        # db_password = os.getenv("SUPABASE_DB_PASSWORD")
        # db_port = os.getenv("SUPABASE_DB_PORT")

        conn = psycopg.connect(dbname=db_name,host=db_host,user=db_username,password=db_password,port=db_port,client_encoding="utf8")
            
		# If a row factory is provided, use it
        if row_factory is not None:
            conn.row_factory = row_factory
        return conn
    except (Exception, psycopg.DatabaseError) as error:
        raise error

# Experimental Function. Intended to replace the 'pydantic_' functions below.
# def execute_query(query: sql.Composed, params: Tuple[Any, ...] = (), model_class: Optional[Type[BaseModel]] = None, auto_commit: bool = True) -> Optional[List[BaseModel]]:
#     """
#     Execute a SQL query and optionally map results to a Pydantic model.
    
#     Args:
#         query (str): SQL query string.
#         params (Tuple[Any, ...]): Parameters for the query.
#         model_class (Type[BaseModel], optional): Pydantic model for result mapping.
#         auto_commit (bool): Whether to commit the transaction after executing the query.
    
#     Returns:
#         Optional[List[BaseModel]]: List of model instances or None.
#     """
    
#     with psycopg.connect(conninfo=DATABASE_URI) as conn:
#         print(query.as_string(conn))
#         convert_to_default = False
#         if model_class:
#             conn.row_factory = class_row(model_class)
#         else:
#             conn.row_factory = dict_row
#             convert_to_default = True
#         with conn.cursor() as cursor:
#             cursor.execute(query, params)

#             if auto_commit:
#                 conn.commit()

#             if cursor.description:  # This will be None for non-SELECT queries
#                 results = cursor.fetchall()

#             # Could be horribly inefficient for mega results
#             if convert_to_default:
#                 converted_results = []
#                 for dct in results:
#                     converted_results.append(DefaultModel(data=dct))
#                 return converted_results
#             return results
#     return None

def pydantic_select(sql_select: str, modelType: Any) -> List[Any]:
    """
    Executes a SQL SELECT statement and returns the result rows as a list of Pydantic models.

    Args:
        sql_select (str): The SQL SELECT statement to execute.
        modelType (Optional[Any]): The Pydantic model to use for the row factory

    Returns:
        List[Any]: The rows returned by the SELECT statement as a list of Pydantic Models.
    """   
    # Use the provided modelType (PydanticModel) for the row factory
    if modelType:
        conn = db_connect(row_factory=class_row(modelType))
    

    cur = conn.cursor()

    # Execute the SELECT statement
    cur.execute(sql_select)

    # Fetch all rows
    rows = cur.fetchall()
    

    # Close the cursor and the connection
    cur.close()
    conn.close()

    return rows

def pydantic_insert(table_name: str, models: List[Any]):
    """
    Inserts the provided List of Pydantic Models into the specified table.

    Args:
        table_name (str): The name of the table to insert into.
        nodes (List[Any]): The list of Pydantic Models to insert.
        user (str): The user making the request.
    """
    # Get the psycopg3 connection object
    conn = db_connect()

    with conn.cursor() as cursor:
        for model in models:
            # Convert the NodeModel to a dictionary and exclude default values
            
            model_dict = model.model_dump(mode="json",exclude_defaults=True)

            for key, value in model_dict.items():
                if type(value) == dict:
                    model_dict[key] = json.dumps(value)

            # 
            

            # Prepare the column names and placeholders
            columns = ', '.join(model_dict.keys())
            placeholders = ', '.join(['%s'] * len(model_dict))

            

            # Create the INSERT statement using psycopg.sql to safely handle identifiers
            query = psycopg.sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                psycopg.sql.Identifier(table_name),
                psycopg.sql.SQL(columns),
                psycopg.sql.SQL(placeholders)
            )

            # Execute the INSERT statement
            cursor.execute(query, tuple(model_dict.values()))

    # Commit the changes
    conn.commit()
    conn.close()

def pydantic_update(table_name: str, models: List[Type[BaseModel]], where_field: str, update_columns: Optional[List[str]] = None, where_field_source_override: Optional[str] = None ):
    """
    Updates the specified table with the provided List of Pydantic Models.

    Args:
        table_name (str): The name of the table to update.
        nodes (List[PydanticModel]): The nodes to use for the update.
        where_field (str): The field to use in the WHERE clause of the update statement.
        update_columns (Optional[List[str]]): The columns to include in the update. If None, all fields are included. Defaults to None.
        user (Optional[str]): The user making the request. Defaults to None.
    """
    conn = db_connect()

    with conn.cursor() as cursor:
        for model in models:
            # Convert the NodeModel to a dictionary and exclude where field, include values to update only
            if update_columns:
                model_dict = model.model_dump(mode="json",exclude_defaults=True, include=update_columns.append(where_field))
            else:
                model_dict = model.model_dump(mode="json",exclude_defaults=True)

            for key, value in model_dict.items():
                if type(value) == dict:
                    model_dict[key] = json.dumps(value)
            
            if(where_field_source_override):
                where_value = model_dict[where_field_source_override]
                del model_dict[where_field_source_override]
            else:
                where_value = model_dict[where_field]
            
                del model_dict[where_field]

            # Prepare the column names and placeholders
            set_statements = ', '.join([f"{column} = %s" for column in model_dict.keys()])
            
            query = psycopg.sql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
                psycopg.sql.Identifier(table_name),
                psycopg.sql.SQL(set_statements),
                psycopg.sql.Identifier(where_field)
            )
            # print(query.as_string(conn))
            # Execute the UPDATE statement
            cursor.execute(query, tuple(list(model_dict.values()) + [where_value]))
    conn.commit()
    conn.close

def pydantic_bulk_update(
    table_name: str,
    models: List[Type[BaseModel]],
    where_field: str,
    update_columns: Optional[List[str]] = None,
    where_field_source_override: Optional[str] = None,
):
    """
    Updates the specified table with the provided List of Pydantic Models in bulk.

    Args:
        table_name (str): The name of the table to update.
        models (List[Type[BaseModel]]): The models to use for the update.
        where_field (str): The field to use in the WHERE clause of the update statement.
        update_columns (Optional[List[str]]): The columns to include in the update. If None, all fields are included. Defaults to None.
        where_field_source_override (Optional[str]): The alternative field name in the model to be used for the WHERE clause. Defaults to None.
    """

    # Print out all parameters, formatted nicely
    # print(f"table_name: {table_name}")
    # print(f"# of models: {len(models)}")
    # print(f"where_field: {where_field}")
    # print(f"update_columns: {update_columns}")
    # print(f"where_field_source_override: {where_field_source_override}")
    
    conn = db_connect()
    
    # Batch size for bulk update
    batch_size = 1000
    columns_to_include_input = None
    columns_to_include_output = []
    # If where_field_source_override is provided, use it, otherwise use where_field
    #print(f"where_field_source_override is None: {where_field_source_override is None}")
    if update_columns is None:
        set_statements = ', '.join(
                [f"{column} = v.{column}" for column in models[0].model_dump().keys()]
            )   
        columns_to_include_output = models[0].model_dump().keys()
    else:
        set_statements = ', '.join(
                [f"{column} = v.{column}" for column in update_columns]
            )
        # Columns to get from the input model
        if where_field_source_override is None:
            columns_to_include_input = [where_field]
        else:
            columns_to_include_input = [where_field_source_override]
        columns_to_include_input.extend(update_columns)
        # Columns to map to the table
        columns_to_include_output.append(where_field)
        columns_to_include_output.extend(update_columns)
        
    # print(f"Columns to include input: {columns_to_include_input}")
    # print(f"Columns to include output: {columns_to_include_output}")
    # print(f"Set statements: {set_statements}")
    
    with conn.cursor() as cursor:
        # Process models in batches
        for i in range(0, len(models), batch_size):
            batch = models[i:i + batch_size]

            # Collect values for the bulk update
            value_tuples = []
           
            
            for model in batch:

                # Dump model to a dictionary, including only the columns specified in columns_to_include
                if columns_to_include_input:
                    model_dict: Dict[str, Any] = model.model_dump(mode="json", include=columns_to_include_input)
                
                else:
                    model_dict: Dict[str, Any] = model.model_dump(mode="json")

                # Convert nested dictionaries to JSON strings
                for key, value in model_dict.items():
                    if isinstance(value, dict):
                        model_dict[key] = json.dumps(value)


                if where_field_source_override:
                    where_value = model_dict[where_field_source_override]
                    del model_dict[where_field_source_override]
                else:
                    where_value = model_dict[where_field]
                    del model_dict[where_field]

                # Add the values tuple for this row, including the where_value at the end
                value_tuple = (where_value, ) + tuple(model_dict.values())
                #print(value_tuple)
                # exit(1)
                value_tuples.append(value_tuple)

            # Prepare the columns for the SET part of the query
            

            # Prepare the VALUES part with placeholders
            placeholders = ', '.join(
                ['%s'] * (len(value_tuples[0]))
            )
            values_sql = ', '.join(
                [f"({placeholders})" for _ in range(len(value_tuples))]
            )

            # Create the query with VALUES and JOIN
            query = f"""
                UPDATE {table_name} AS t
                SET {set_statements}
                FROM (VALUES {values_sql}) AS v ({', '.join(columns_to_include_output)})
                WHERE t.{where_field}::text = v.{where_field}::text;
            """
            #print(query)
            

            # Flatten the value_tuples for the cursor execution
            flat_values = [value for row in value_tuples for value in row]

            # Execute the batch update
            cursor.execute(query, flat_values)
            conn.commit()
    conn.close()

def pydantic_upsert(table_name: str, models: List[Any], where_field: str):
    """
    Performs an upsert operation on the specified table with the provided list of Pydantic Models.

    Args:
        table_name (str): The name of the table to upsert into.
        nodes (List[PydanticModels]): The list of pydantic models to use for the upsert.
        where_field (str): The field to use in the WHERE clause of the update statement.
        user (Optional[str]): The user making the request. 
    """
    for model in models:
        try:
            pydantic_insert(table_name=table_name, models=[model])
        except psycopg.errors.UniqueViolation:
            pydantic_update(table_name=table_name, models=[model], where_field=where_field)

