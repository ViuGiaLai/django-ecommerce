# utils/supabase_client.py
from supabase import create_client, Client

# Cấu hình thông tin Supabase
url = "https://vlgsgoqjfifshsnodavc.supabase.co"  # URL của Supabase project
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZsZ3Nnb3FqZmlmc2hzbm9kYXZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUwNzYwMjUsImV4cCI6MjA2MDY1MjAyNX0.-IJn0q1xqYEDXYL-ZUQrOrR7UmDL5YuOnua34RyVxJQ"  # API key của Supabase project

# Tạo client Supabase
supabase: Client = create_client(url, key)
