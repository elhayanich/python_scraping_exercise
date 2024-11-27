import requests
from bs4 import BeautifulSoup
import mysql.connector
import time


conn = mysql.connector.connect(
    host='localhost',
    user='chaymae',
    password='chay',
    database='books'
)
cursor = conn.cursor()

def scrape_all_books():
    """
    Scrape toutes les pages de livres disponibles sur le site et retourne les données collectées.
    """
    base_url = 'https://books.toscrape.com/catalogue/page-{}.html'
    page_num = 1
    all_books = []  
    
    while True:
        print(f"Scraping la page {page_num}")
        url = base_url.format(page_num)
        response = requests.get(url)

        if response.status_code != 200:
            print("Toutes les pages ont été scrappées.")
            break
        
    
        books_on_page = scrape_books_page(url)
        all_books.extend(books_on_page)
        page_num += 1
        time.sleep(1)  
    
    return all_books  


def scrape_books_page(url):
    """
    Scrape une page contenant des livres et retourne une liste de dictionnaires avec les données.
    """
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    books = soup.find_all('article', class_='product_pod')
    books_data = []
    
    for book in books:
        title = book.find('h3').find('a')['title']
        price_text = book.find('p', class_='price_color').text.strip()
        price_text = price_text.encode('ascii', errors='ignore').decode()  
        price = float(price_text.replace('£', '').strip())
        stock_text = book.find('p', class_='instock availability').text.strip()
        stock = 1 if 'In stock' in stock_text else 0
        picture = 'https://books.toscrape.com/' + book.find('img')['src']
        rating_text = book.find('p', class_='star-rating')['class'][1]
        review = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}.get(rating_text, 0)
        product_page_url = 'https://books.toscrape.com/catalogue/' + book.find('h3').find('a')['href']
        product_description, category_name = scrape_product_details(product_page_url)
        
        books_data.append({
            'title': title,
            'price': price,
            'product_description': product_description,
            'stock': stock,
            'review': review,
            'picture': picture,
            'category': category_name
        })
    
    return books_data  

def scrape_product_details(product_page_url):
    """
    Scrape la description et la catégorie d'un produit depuis sa page.
    Retourne la description et le nom de la catégorie.
    """
    response = requests.get(product_page_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    description_element = soup.find('meta', attrs={'name': 'description'})
    product_description = description_element['content'].strip() if description_element else "Description not available."
    
    breadcrumb = soup.find('ul', class_='breadcrumb')
    category_name = breadcrumb.find_all('li')[2].find('a').text.strip() if breadcrumb else "Unknown"
    
    return product_description, category_name

# base de données
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

def insert_book(title, price, product_description, stock, review, picture):
    """
    Insère un livre dans la table 'book'.
    Retourne l'ID du livre inséré.
    """
    cursor.execute("""
        INSERT INTO book (title, price, product_description, stock, review, picture)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (title, price, product_description, stock, review, picture))
    conn.commit()
    return cursor.lastrowid

def insert_book_category(book_id, category_id):
    """
    Lie un livre à une catégorie dans la table 'book_category'.
    """
    cursor.execute("""
        INSERT INTO book_category (id_book, id_category)
        VALUES (%s, %s)
    """, (book_id, category_id))
    conn.commit()


def insert_all_books(all_books):
    """
    Insère une liste de livres dans la base de données.
    """
    for book in all_books:
        category_id = insert_category(book['category'])
        
        book_id = insert_book(
            book['title'],
            book['price'],
            book['product_description'],
            book['stock'],
            book['review'],
            book['picture']
        )

        insert_book_category(book_id, category_id)
        print(f'Livre "{book["title"]}" inséré avec succès.')

if __name__ == '__main__':
    try:
        #  Scraper toutes les données
        print("Scraping des livres...")
        all_books = scrape_all_books()
        print(f"{len(all_books)} livres collectés.")
        
        # Insérer dans la base de données
        print("Insertion des données dans la base de données")
        insert_all_books(all_books)
    finally:
        cursor.close()
        conn.close()
        print("Connexion à la base de données fermée.")

