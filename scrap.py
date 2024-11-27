import requests
from bs4 import BeautifulSoup
import mysql.connector
import time

# Étape 1 : Connexion à la base de données
conn = mysql.connector.connect(
    host='localhost',
    user='chaymae',
    password='chay',
    database='books'
)
cursor = conn.cursor()

# Étape 2 : Fonction pour insérer une catégorie
def insert_category(name):
    """
    Insère une catégorie dans la table 'category' si elle n'existe pas.
    Retourne l'ID de la catégorie.
    """
    cursor.execute("SELECT id FROM category WHERE name = %s", (name,))
    result = cursor.fetchone()
    if not result:
        cursor.execute("INSERT INTO category (name) VALUES (%s)", (name,))
        conn.commit()
        return cursor.lastrowid
    return result[0]

# Étape 3 : Fonction pour insérer un livre
def insert_book(title, price, product_description, stock, review, picture):
    """
    Insère un livre dans la table 'book' et retourne son ID.
    """
    cursor.execute("""
        INSERT INTO book (title, price, product_description, stock, review, picture)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (title, price, product_description, stock, review, picture))
    conn.commit()
    return cursor.lastrowid

# Étape 4 : Fonction pour lier un livre à une catégorie
def insert_book_category(book_id, category_id):
    """
    Lie un livre à une catégorie dans la table 'book_category'.
    """
    cursor.execute("""
        INSERT INTO book_category (id_book, id_category)
        VALUES (%s, %s)
    """, (book_id, category_id))
    conn.commit()

# Étape 5 : Scraper une page de produit pour obtenir la catégorie et la description
def scrape_product_details(product_page_url):
    """
    Scrape les détails du produit (catégorie et description) depuis sa page individuelle.
    """
    response = requests.get(product_page_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Récupérer la description
    description_element = soup.find('meta', attrs={'name': 'description'})
    product_description = description_element['content'].strip() if description_element else "Description not available."
    
    # Récupérer la catégorie
    category_element = soup.find('ul', class_='breadcrumb').find_all('a')
    if len(category_element) > 2:  # Assurer qu'il y a au moins une catégorie
        category_name = category_element[-1].text.strip()  # Dernier lien est souvent la catégorie
    else:
        category_name = "Unknown"
    
    return product_description, category_name

# Étape 6 : Fonction principale pour scraper les livres d'une page
def scrape_books_page(url):
    """
    Scrape une page contenant des livres, récupère les informations, et insère dans la BDD.
    """
    response = requests.get(url)
    response.encoding = 'utf-8'  # Ensure correct decoding
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Récupérer tous les livres sur la page
    books = soup.find_all('article', class_='product_pod')
    
    for book in books:
        # Scraper le titre
        title = book.find('h3').find('a')['title']
        
        # Scraper le prix
        price_text = book.find('p', class_='price_color').text.strip()
        try:
            price_text = price_text.encode('ascii', errors='ignore').decode()  # Remove unexpected characters
            price = float(price_text.replace('£', '').strip())
        except ValueError:
            print(f"Invalid price format: {price_text}")
            price = 0.0  # Default value for invalid prices
        
        # Stocker la disponibilité
        stock_text = book.find('p', class_='instock availability').text.strip()
        stock = 1 if 'In stock' in stock_text else 0
        
        # Scraper l'image
        picture = book.find('img')['src']
        picture = 'https://books.toscrape.com/' + picture
        
        # Note (étoiles)
        rating_text = book.find('p', class_='star-rating')['class'][1]
        review = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}.get(rating_text, 0)
        
        # Scraper la description et la catégorie depuis la page produit
        product_page_url = 'https://books.toscrape.com/catalogue/' + book.find('h3').find('a')['href']
        product_description, category_name = scrape_product_details(product_page_url)
        
        # Insérer le livre dans la base de données
        book_id = insert_book(title, price, product_description, stock, review, picture)
        
        # Insérer ou récupérer l'ID de la catégorie
        category_id = insert_category(category_name)
        
        # Lier le livre à la catégorie
        insert_book_category(book_id, category_id)
        
        print(f'Livre "{title}" inséré avec succès dans la base de données.')

# Étape 7 : Scraper toutes les pages de livres
def scrape_all_books():
    """
    Scrape toutes les pages de livres disponibles sur le site.
    """
    base_url = 'https://books.toscrape.com/catalogue/page-{}.html'
    page_num = 1
    
    while True:
        print(f"Scraping la page {page_num}...")
        url = base_url.format(page_num)
        response = requests.get(url)
        
        # Vérifier si la page existe
        if response.status_code != 200:
            print("Toutes les pages ont été scrappées.")
            break
        
        # Scraper la page actuelle
        scrape_books_page(url)
        page_num += 1
        time.sleep(1)  # Pause pour éviter de surcharger le serveur

# Étape 8 : Exécuter le script
if __name__ == '__main__':
    try:
        scrape_all_books()
    finally:
        cursor.close()
        conn.close()
        print("Connexion à la base de données fermée.")

