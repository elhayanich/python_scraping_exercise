DROP DATABASE IF EXISTS books;
Create DATABASE books;
USE  books;
CREATE TABLE book (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    title VARCHAR(255) NOT NULL, 
    price DECIMAL(10, 2) NOT NULL,  
    product_description TEXT, 
    stock INT NOT NULL, 
    review DECIMAL(2, 1), 
    picture VARCHAR(255)
);

CREATE TABLE category ( 
    id INT AUTO_INCREMENT PRIMARY KEY, 
    name VARCHAR(255) NOT NULL 
);

CREATE TABLE book_category ( 
    id INT AUTO_INCREMENT PRIMARY KEY, 
    id_book INT NOT NULL, 
    id_category INT NOT NULL, 
    FOREIGN KEY (id_book) REFERENCES book(id), 
    FOREIGN KEY (id_category) REFERENCES category(id) 
);
