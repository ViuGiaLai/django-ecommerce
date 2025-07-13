# django-ecommerce-viu

## Brief Description
This is an e-commerce website project built with Django, providing essential features for an online shop such as product management, shopping cart, ordering, payment, and user administration.

## Main Features
- User registration, login, and account management
- Product management: add, edit, delete, and categorize products
- Product search and filtering
- Shopping cart and order placement
- Order payment
- Admin dashboard
- Order management and delivery status tracking
- Support for product image uploads
- Custom templates with Django Template Tags

## Technologies Used
- Python 3
- Django
- PostgreSQL 
- HTML, CSS, JavaScript (may include TailwindCSS)
- Django Template Engine
- Additional libraries: (listed in requirements.txt)
## 📸 Screenshots
<p align="center">
  <img width="30%" src="https://github.com/user-attachments/assets/8b1a2ee5-cd64-4e3d-9f7f-ab0aa1550f09" />
  <img width="30%" src="https://github.com/user-attachments/assets/4a0d3254-e6fb-4ece-bfe0-545fe0356045" />
  <img width="30%" src="https://github.com/user-attachments/assets/cd75c720-2baa-4e04-a219-80bc8f076e69" />
</p>

<p align="center">
  <img width="30%" src="https://github.com/user-attachments/assets/298bf0c4-88e7-40b0-9c78-7e34903aaf91" />
  <img width="30%" src="https://github.com/user-attachments/assets/0762ae45-9577-4296-9e82-93b834e5ca89" />
  <img width="30%" src="https://github.com/user-attachments/assets/1f0e6928-7198-4333-a8f3-0ccf13e4cb62" />
</p>

<p align="center">
  <img width="30%" src="https://github.com/user-attachments/assets/a661ca22-f494-40a8-a583-782d4cd8cc64" />
  <img width="30%" src="https://github.com/user-attachments/assets/e3132b26-e856-4e2f-9c88-d162e6c6d113" />
  <img width="30%" src="https://github.com/user-attachments/assets/b0fe298c-0541-435e-9b71-919d7f07ba30" />
</p>

<p align="center">
  <strong>Admin:</strong><br/>
  <img width="50%" src="https://github.com/user-attachments/assets/11fba1d6-50aa-4968-a2a1-6c3e30f81ad1" />
</p>


## Installation / Running the Project

1. **Clone the source code**
   ```bash
   git clone https://github.com/ViuGiaLai/django-ecommerce.git
   cd django-ecommerce-viu-main
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv env
   env\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

3. **Apply database migrations**
   ```bash
   python manage.py migrate
   ```

4. **Create admin account**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the server**
   ```bash
   python manage.py runserver
   ```

6. **Access the website**
   - User: https://viu-shop-ecommerce.onrender.com/
   - Admin: https://viu-shop-ecommerce.onrender.com/admin/
