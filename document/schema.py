import graphene
import datetime
from graphene_django.types import DjangoObjectType
from .models import Document
import psycopg2
import os
import json
from .utils import transform_text_to_pgsql_command
import google.generativeai as genai
from decouple import config

genai.configure(api_key=config('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

class DocumentType(DjangoObjectType):
    class Meta:
        model = Document
        fields = '__all__'


class CommandResponse(graphene.ObjectType):
    query = graphene.String()
    response = graphene.String()


class Query(graphene.ObjectType):
    execute_command = graphene.Field(
        CommandResponse,
        command=graphene.String(required=True),
    )

    def resolve_execute_command(self, info, command):
        content_response = transform_text_to_pgsql_command(command)
        connection = None
        cursor = None

        try:
            # Access the candidates list
            sql_content = content_response
            # Remove any markdown formatting (like '```sql' and '```') if present
            sql_command = sql_content.strip("```sql\n").strip("```").strip()

            # Connect to the PostgreSQL database and execute the query
            connection = psycopg2.connect(
                dbname=config("DB_NAME"),
                user=config("DB_USER"),
                password=config("DB_PASSWORD"),
                host=config("DB_HOST"),
                port=config("DB_PORT"),
            )
            cursor = connection.cursor()

            # Execute the query
            cursor.execute(sql_command)
            rows = cursor.fetchall()

                # Convert rows with datetime objects to JSON serializable format
            def convert_dates(o):
                if isinstance(o, datetime.datetime):
                    return o.isoformat()  # Converts to ISO 8601 format
                raise TypeError("Type not serializable")

            response_data = json.dumps(rows, default=convert_dates)
            prompt = (
                f"this is the answer for this question: {command}, answer is: {response_data}, make a short human answer"
            )
            structured_response = model.generate_content(prompt).candidates[0].content.parts[0].text

            return CommandResponse(
                query=sql_command,
                response=structured_response,
            )
        except Exception as gemini_error:
            return CommandResponse(
                query="",
                response=f"Error generating or executing SQL command: {str(gemini_error)}",
            )
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    # Create the schema
schema = graphene.Schema(query=Query)
