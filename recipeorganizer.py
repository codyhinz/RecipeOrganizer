"""
Recipe Organization System (Simplified)
---------------------------------------
A streamlined application for managing recipes and shopping lists.

Features:
- Recipe management (add, edit, view, search)
- Shopping list generation
- Recipe import/export
- Paper-like user interface

Author: Cody Hinz
Date: April 18, 2025
"""

import os
import sys
import json
import sqlite3
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkinter.scrolledtext import ScrolledText

class RecipeDatabase:
    """
    Handles all database operations for the Recipe Organization System.
    """
    
    def __init__(self, db_path='recipe_system.db'):
        """
        Initialize the database connection and create tables if they don't exist.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        # Store the database path
        self.db_path = db_path
        
        # Connect to the database
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        self._create_tables()
    
    def _create_tables(self):
        """
        Create all necessary tables for the application if they don't already exist.
        """
        # Create recipes table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            instructions TEXT,
            prep_time INTEGER,
            cook_time INTEGER,
            servings INTEGER,
            difficulty TEXT,
            source TEXT,
            notes TEXT,
            favorite BOOLEAN DEFAULT 0,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create categories table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
        ''')
        
        # Create recipe_categories table (many-to-many relationship)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_categories (
            recipe_id INTEGER,
            category_id INTEGER,
            PRIMARY KEY (recipe_id, category_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
        )
        ''')
        
        # Create tags table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
        ''')
        
        # Create recipe_tags table (many-to-many relationship)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_tags (
            recipe_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (recipe_id, tag_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
        )
        ''')
        
        # Create ingredients table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            category TEXT,
            unit TEXT
        )
        ''')
        
        # Create recipe_ingredients table (many-to-many relationship with quantity)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            recipe_id INTEGER,
            ingredient_id INTEGER,
            quantity REAL,
            unit TEXT,
            notes TEXT,
            PRIMARY KEY (recipe_id, ingredient_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE,
            FOREIGN KEY (ingredient_id) REFERENCES ingredients (id) ON DELETE CASCADE
        )
        ''')
        
        # Create shopping_lists table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS shopping_lists (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
        ''')
        
        # Create shopping_list_items table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS shopping_list_items (
            id INTEGER PRIMARY KEY,
            shopping_list_id INTEGER,
            ingredient_id INTEGER,
            quantity REAL,
            unit TEXT,
            checked BOOLEAN DEFAULT 0,
            notes TEXT,
            FOREIGN KEY (shopping_list_id) REFERENCES shopping_lists (id) ON DELETE CASCADE,
            FOREIGN KEY (ingredient_id) REFERENCES ingredients (id) ON DELETE SET NULL
        )
        ''')
        
        # Insert some default categories
        default_categories = [
            ('Breakfast',), ('Lunch',), ('Dinner',), ('Dessert',), 
            ('Appetizer',), ('Snack',), ('Soup',), ('Salad',),
            ('Main Course',), ('Side Dish',), ('Beverage',), ('Baked Goods',)
        ]
        
        self.cursor.executemany(
            'INSERT OR IGNORE INTO categories (name) VALUES (?)', 
            default_categories
        )
        
        # Insert some default tags
        default_tags = [
            ('Vegetarian',), ('Vegan',), ('Gluten-Free',), ('Dairy-Free',),
            ('Nut-Free',), ('Low-Carb',), ('High-Protein',), ('Quick',),
            ('Easy',), ('Budget-Friendly',), ('One-Pot',), ('Kid-Friendly',)
        ]
        
        self.cursor.executemany(
            'INSERT OR IGNORE INTO tags (name) VALUES (?)', 
            default_tags
        )
        
        # Commit changes
        self.conn.commit()
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    # Recipe CRUD operations
    def add_recipe(self, recipe_data):
        """
        Add a new recipe to the database.
        
        Args:
            recipe_data (dict): Dictionary containing recipe information
                Required keys: 'name', 'instructions'
                Optional keys: 'description', 'prep_time', 'cook_time', 'servings',
                               'difficulty', 'source', 'notes', 'favorite'
        
        Returns:
            int: ID of the newly added recipe
        """
        # Extract recipe data
        name = recipe_data.get('name')
        description = recipe_data.get('description', '')
        instructions = recipe_data.get('instructions', '')
        prep_time = recipe_data.get('prep_time', 0)
        cook_time = recipe_data.get('cook_time', 0)
        servings = recipe_data.get('servings', 1)
        difficulty = recipe_data.get('difficulty', 'Medium')
        source = recipe_data.get('source', '')
        notes = recipe_data.get('notes', '')
        favorite = 1 if recipe_data.get('favorite', False) else 0
        
        # Insert recipe into database
        self.cursor.execute('''
        INSERT INTO recipes (name, description, instructions, prep_time, cook_time, 
                           servings, difficulty, source, notes, favorite)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, instructions, prep_time, cook_time, 
              servings, difficulty, source, notes, favorite))
        
        # Get the ID of the newly inserted recipe
        recipe_id = self.cursor.lastrowid
        
        # Add categories if provided
        if 'categories' in recipe_data and recipe_data['categories']:
            for category_name in recipe_data['categories']:
                # Get or create category
                self.cursor.execute('SELECT id FROM categories WHERE name = ?', (category_name,))
                result = self.cursor.fetchone()
                
                if result:
                    category_id = result[0]
                else:
                    self.cursor.execute('INSERT INTO categories (name) VALUES (?)', (category_name,))
                    category_id = self.cursor.lastrowid
                
                # Link recipe to category
                self.cursor.execute('''
                INSERT OR IGNORE INTO recipe_categories (recipe_id, category_id)
                VALUES (?, ?)
                ''', (recipe_id, category_id))
        
        # Add tags if provided
        if 'tags' in recipe_data and recipe_data['tags']:
            for tag_name in recipe_data['tags']:
                # Get or create tag
                self.cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
                result = self.cursor.fetchone()
                
                if result:
                    tag_id = result[0]
                else:
                    self.cursor.execute('INSERT INTO tags (name) VALUES (?)', (tag_name,))
                    tag_id = self.cursor.lastrowid
                
                # Link recipe to tag
                self.cursor.execute('''
                INSERT OR IGNORE INTO recipe_tags (recipe_id, tag_id)
                VALUES (?, ?)
                ''', (recipe_id, tag_id))
        
        # Add ingredients if provided
        if 'ingredients' in recipe_data and recipe_data['ingredients']:
            for ingredient in recipe_data['ingredients']:
                ing_name = ingredient.get('name')
                ing_quantity = ingredient.get('quantity', 0)
                ing_unit = ingredient.get('unit', '')
                ing_notes = ingredient.get('notes', '')
                
                # Get or create ingredient
                self.cursor.execute('SELECT id FROM ingredients WHERE name = ?', (ing_name,))
                result = self.cursor.fetchone()
                
                if result:
                    ingredient_id = result[0]
                else:
                    ing_category = ingredient.get('category', '')
                    self.cursor.execute('''
                    INSERT INTO ingredients (name, category, unit)
                    VALUES (?, ?, ?)
                    ''', (ing_name, ing_category, ing_unit))
                    ingredient_id = self.cursor.lastrowid
                
                # Link recipe to ingredient with quantity
                self.cursor.execute('''
                INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, notes)
                VALUES (?, ?, ?, ?, ?)
                ''', (recipe_id, ingredient_id, ing_quantity, ing_unit, ing_notes))
        
        # Commit the transaction
        self.conn.commit()
        
        return recipe_id
    
    def get_recipe(self, recipe_id):
        """
        Retrieve a recipe by its ID.
        
        Args:
            recipe_id (int): ID of the recipe to retrieve
            
        Returns:
            dict: Recipe data including ingredients, categories, and tags
        """
        # Get recipe basic information
        self.cursor.execute('''
        SELECT id, name, description, instructions, prep_time, cook_time, 
               servings, difficulty, source, notes, favorite, date_added
        FROM recipes
        WHERE id = ?
        ''', (recipe_id,))
        
        recipe_row = self.cursor.fetchone()
        
        if not recipe_row:
            return None
        
        # Convert to dictionary
        recipe = {
            'id': recipe_row[0],
            'name': recipe_row[1],
            'description': recipe_row[2],
            'instructions': recipe_row[3],
            'prep_time': recipe_row[4],
            'cook_time': recipe_row[5],
            'servings': recipe_row[6],
            'difficulty': recipe_row[7],
            'source': recipe_row[8],
            'notes': recipe_row[9],
            'favorite': bool(recipe_row[10]),
            'date_added': recipe_row[11],
            'ingredients': [],
            'categories': [],
            'tags': []
        }
        
        # Get ingredients
        self.cursor.execute('''
        SELECT i.id, i.name, ri.quantity, ri.unit, ri.notes, i.category
        FROM recipe_ingredients ri
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE ri.recipe_id = ?
        ''', (recipe_id,))
        
        ingredients_rows = self.cursor.fetchall()
        
        for row in ingredients_rows:
            ingredient = {
                'id': row[0],
                'name': row[1],
                'quantity': row[2],
                'unit': row[3],
                'notes': row[4],
                'category': row[5]
            }
            recipe['ingredients'].append(ingredient)
        
        # Get categories
        self.cursor.execute('''
        SELECT c.name
        FROM recipe_categories rc
        JOIN categories c ON rc.category_id = c.id
        WHERE rc.recipe_id = ?
        ''', (recipe_id,))
        
        categories_rows = self.cursor.fetchall()
        recipe['categories'] = [row[0] for row in categories_rows]
        
        # Get tags
        self.cursor.execute('''
        SELECT t.name
        FROM recipe_tags rt
        JOIN tags t ON rt.tag_id = t.id
        WHERE rt.recipe_id = ?
        ''', (recipe_id,))
        
        tags_rows = self.cursor.fetchall()
        recipe['tags'] = [row[0] for row in tags_rows]
        
        return recipe
    
    def update_recipe(self, recipe_id, recipe_data):
        """
        Update an existing recipe.
        
        Args:
            recipe_id (int): ID of the recipe to update
            recipe_data (dict): Updated recipe information
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        # Check if recipe exists
        self.cursor.execute('SELECT id FROM recipes WHERE id = ?', (recipe_id,))
        if not self.cursor.fetchone():
            return False
        
        # Update recipe basic information
        self.cursor.execute('''
        UPDATE recipes SET
            name = ?,
            description = ?,
            instructions = ?,
            prep_time = ?,
            cook_time = ?,
            servings = ?,
            difficulty = ?,
            source = ?,
            notes = ?,
            favorite = ?
        WHERE id = ?
        ''', (
            recipe_data.get('name'),
            recipe_data.get('description', ''),
            recipe_data.get('instructions', ''),
            recipe_data.get('prep_time', 0),
            recipe_data.get('cook_time', 0),
            recipe_data.get('servings', 1),
            recipe_data.get('difficulty', 'Medium'),
            recipe_data.get('source', ''),
            recipe_data.get('notes', ''),
            1 if recipe_data.get('favorite', False) else 0,
            recipe_id
        ))
        
        # Update categories (delete all and reinsert)
        if 'categories' in recipe_data:
            # Remove existing categories
            self.cursor.execute('DELETE FROM recipe_categories WHERE recipe_id = ?', (recipe_id,))
            
            # Add new categories
            for category_name in recipe_data['categories']:
                # Get or create category
                self.cursor.execute('SELECT id FROM categories WHERE name = ?', (category_name,))
                result = self.cursor.fetchone()
                
                if result:
                    category_id = result[0]
                else:
                    self.cursor.execute('INSERT INTO categories (name) VALUES (?)', (category_name,))
                    category_id = self.cursor.lastrowid
                
                # Link recipe to category
                self.cursor.execute('''
                INSERT OR IGNORE INTO recipe_categories (recipe_id, category_id)
                VALUES (?, ?)
                ''', (recipe_id, category_id))
        
        # Update tags (delete all and reinsert)
        if 'tags' in recipe_data:
            # Remove existing tags
            self.cursor.execute('DELETE FROM recipe_tags WHERE recipe_id = ?', (recipe_id,))
            
            # Add new tags
            for tag_name in recipe_data['tags']:
                # Get or create tag
                self.cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
                result = self.cursor.fetchone()
                
                if result:
                    tag_id = result[0]
                else:
                    self.cursor.execute('INSERT INTO tags (name) VALUES (?)', (tag_name,))
                    tag_id = self.cursor.lastrowid
                
                # Link recipe to tag
                self.cursor.execute('''
                INSERT OR IGNORE INTO recipe_tags (recipe_id, tag_id)
                VALUES (?, ?)
                ''', (recipe_id, tag_id))
        
        # Update ingredients (delete all and reinsert)
        if 'ingredients' in recipe_data:
            # Remove existing ingredient links
            self.cursor.execute('DELETE FROM recipe_ingredients WHERE recipe_id = ?', (recipe_id,))
            
            # Add new ingredients
            for ingredient in recipe_data['ingredients']:
                ing_name = ingredient.get('name')
                ing_quantity = ingredient.get('quantity', 0)
                ing_unit = ingredient.get('unit', '')
                ing_notes = ingredient.get('notes', '')
                
                # Get or create ingredient
                self.cursor.execute('SELECT id FROM ingredients WHERE name = ?', (ing_name,))
                result = self.cursor.fetchone()
                
                if result:
                    ingredient_id = result[0]
                else:
                    ing_category = ingredient.get('category', '')
                    self.cursor.execute('''
                    INSERT INTO ingredients (name, category, unit)
                    VALUES (?, ?, ?)
                    ''', (ing_name, ing_category, ing_unit))
                    ingredient_id = self.cursor.lastrowid
                
                # Link recipe to ingredient with quantity
                self.cursor.execute('''
                INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, notes)
                VALUES (?, ?, ?, ?, ?)
                ''', (recipe_id, ingredient_id, ing_quantity, ing_unit, ing_notes))
        
        # Commit the transaction
        self.conn.commit()
        
        return True
    
    def delete_recipe(self, recipe_id):
        """
        Delete a recipe from the database.
        
        Args:
            recipe_id (int): ID of the recipe to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        # Check if recipe exists
        self.cursor.execute('SELECT id FROM recipes WHERE id = ?', (recipe_id,))
        if not self.cursor.fetchone():
            return False
        
        # Delete the recipe (foreign key constraints will handle related records)
        self.cursor.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
        
        # Commit the transaction
        self.conn.commit()
        
        return True
    
    def search_recipes(self, query=None, categories=None, tags=None, favorite=None):
        """
        Search for recipes based on various criteria.
        
        Args:
            query (str, optional): Search term for recipe name or description
            categories (list, optional): List of category names to filter by
            tags (list, optional): List of tag names to filter by
            favorite (bool, optional): Filter by favorite status
            
        Returns:
            list: List of recipe dictionaries matching the criteria
        """
        # Base query
        sql = '''
        SELECT DISTINCT r.id, r.name, r.description, r.prep_time, r.cook_time, 
               r.difficulty, r.favorite
        FROM recipes r
        '''
        
        # Conditions and parameters
        conditions = []
        params = []
        
        # Join tables if needed
        if categories:
            sql += '''
            JOIN recipe_categories rc ON r.id = rc.recipe_id
            JOIN categories c ON rc.category_id = c.id
            '''
            conditions.append('c.name IN ({})'.format(','.join(['?'] * len(categories))))
            params.extend(categories)
        
        if tags:
            sql += '''
            JOIN recipe_tags rt ON r.id = rt.recipe_id
            JOIN tags t ON rt.tag_id = t.id
            '''
            conditions.append('t.name IN ({})'.format(','.join(['?'] * len(tags))))
            params.extend(tags)
        
        # Add text search condition
        if query:
            conditions.append('(r.name LIKE ? OR r.description LIKE ? OR r.instructions LIKE ?)')
            search_term = f'%{query}%'
            params.extend([search_term, search_term, search_term])
        
        # Add favorite condition
        if favorite is not None:
            conditions.append('r.favorite = ?')
            params.append(1 if favorite else 0)
        
        # Add WHERE clause if there are conditions
        if conditions:
            sql += ' WHERE ' + ' AND '.join(conditions)
        
        # Execute the query
        self.cursor.execute(sql, params)
        
        # Process results
        recipes = []
        for row in self.cursor.fetchall():
            recipe = {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'prep_time': row[3],
                'cook_time': row[4],
                'difficulty': row[5],
                'favorite': bool(row[6])
            }
            recipes.append(recipe)
        
        return recipes
    
    def get_all_recipes(self):
        """
        Get all recipes in the database.
        
        Returns:
            list: List of all recipe dictionaries
        """
        self.cursor.execute('''
        SELECT id, name, description, prep_time, cook_time, difficulty, favorite
        FROM recipes
        ORDER BY name
        ''')
        
        recipes = []
        for row in self.cursor.fetchall():
            recipe = {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'prep_time': row[3],
                'cook_time': row[4],
                'difficulty': row[5],
                'favorite': bool(row[6])
            }
            recipes.append(recipe)
        
        return recipes
    
    # Category and tag operations
    def get_all_categories(self):
        """
        Get all categories.
        
        Returns:
            list: List of category name strings
        """
        self.cursor.execute('SELECT name FROM categories ORDER BY name')
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_all_tags(self):
        """
        Get all tags.
        
        Returns:
            list: List of tag name strings
        """
        self.cursor.execute('SELECT name FROM tags ORDER BY name')
        return [row[0] for row in self.cursor.fetchall()]
    
    # Shopping list operations
    def create_shopping_list(self, name, notes=''):
        """
        Create a new shopping list.
        
        Args:
            name (str): Shopping list name
            notes (str, optional): Additional notes
            
        Returns:
            int: ID of the newly created shopping list
        """
        self.cursor.execute('''
        INSERT INTO shopping_lists (name, notes)
        VALUES (?, ?)
        ''', (name, notes))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def add_shopping_list_item(self, shopping_list_id, ingredient_id, quantity, unit, notes=''):
        """
        Add an item to a shopping list.
        
        Args:
            shopping_list_id (int): ID of the shopping list
            ingredient_id (int): ID of the ingredient
            quantity (float): Quantity of the ingredient
            unit (str): Unit of measurement
            notes (str, optional): Additional notes
            
        Returns:
            int: ID of the newly added item
        """
        self.cursor.execute('''
        INSERT INTO shopping_list_items (shopping_list_id, ingredient_id, quantity, unit, notes)
        VALUES (?, ?, ?, ?, ?)
        ''', (shopping_list_id, ingredient_id, quantity, unit, notes))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_shopping_lists(self):
        """
        Get all shopping lists.
        
        Returns:
            list: List of shopping list dictionaries
        """
        self.cursor.execute('''
        SELECT id, name, date_created, notes
        FROM shopping_lists
        ORDER BY date_created DESC
        ''')
        
        shopping_lists = []
        for row in self.cursor.fetchall():
            shopping_list = {
                'id': row[0],
                'name': row[1],
                'date_created': row[2],
                'notes': row[3]
            }
            shopping_lists.append(shopping_list)
        
        return shopping_lists
    
    def get_shopping_list(self, shopping_list_id):
        """
        Get a shopping list by ID, including its items.
        
        Args:
            shopping_list_id (int): ID of the shopping list
            
        Returns:
            dict: Shopping list dictionary with items
        """
        # Get shopping list info
        self.cursor.execute('''
        SELECT id, name, date_created, notes
        FROM shopping_lists
        WHERE id = ?
        ''', (shopping_list_id,))
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        shopping_list = {
            'id': row[0],
            'name': row[1],
            'date_created': row[2],
            'notes': row[3],
            'items': []
        }
        
        # Get shopping list items
        self.cursor.execute('''
        SELECT sli.id, sli.ingredient_id, i.name, sli.quantity, sli.unit, 
               sli.checked, sli.notes, i.category
        FROM shopping_list_items sli
        JOIN ingredients i ON sli.ingredient_id = i.id
        WHERE sli.shopping_list_id = ?
        ORDER BY i.category, i.name
        ''', (shopping_list_id,))
        
        for row in self.cursor.fetchall():
            item = {
                'id': row[0],
                'ingredient_id': row[1],
                'name': row[2],
                'quantity': row[3],
                'unit': row[4],
                'checked': bool(row[5]),
                'notes': row[6],
                'category': row[7]
            }
            shopping_list['items'].append(item)
        
        return shopping_list
    
    def update_shopping_list_item(self, item_id, checked=None, quantity=None, notes=None):
        """
        Update a shopping list item.
        
        Args:
            item_id (int): ID of the item to update
            checked (bool, optional): Whether the item is checked off
            quantity (float, optional): Updated quantity
            notes (str, optional): Updated notes
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        # Prepare update fields
        update_fields = []
        params = []
        
        if checked is not None:
            update_fields.append('checked = ?')
            params.append(1 if checked else 0)
        
        if quantity is not None:
            update_fields.append('quantity = ?')
            params.append(quantity)
        
        if notes is not None:
            update_fields.append('notes = ?')
            params.append(notes)
        
        # If no fields to update, return
        if not update_fields:
            return False
        
        # Add item ID to params
        params.append(item_id)
        
        # Execute update
        sql = f"UPDATE shopping_list_items SET {', '.join(update_fields)} WHERE id = ?"
        self.cursor.execute(sql, params)
        
        self.conn.commit()
        return True
    
    def delete_shopping_list(self, shopping_list_id):
        """
        Delete a shopping list.
        
        Args:
            shopping_list_id (int): ID of the shopping list to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        self.cursor.execute('DELETE FROM shopping_lists WHERE id = ?', (shopping_list_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def generate_shopping_list_from_recipes(self, recipe_ids, name=None):
        """
        Generate a shopping list from selected recipes.
        
        Args:
            recipe_ids (list): List of recipe IDs
            name (str, optional): Name for the shopping list
            
        Returns:
            int: ID of the newly created shopping list
        """
        # Create default name if not provided
        if not name:
            name = f"Shopping list ({datetime.date.today().strftime('%Y-%m-%d')})"
        
        # Create shopping list
        shopping_list_id = self.create_shopping_list(name, f"Generated from selected recipes")
        
        # If no recipes, return empty shopping list
        if not recipe_ids:
            return shopping_list_id
        
        # Get all ingredients from these recipes
        # This query consolidates ingredients across recipes
        placeholders = ','.join(['?'] * len(recipe_ids))
        self.cursor.execute(f'''
        SELECT ri.ingredient_id, i.name, SUM(ri.quantity) as total_quantity, ri.unit, i.category
        FROM recipe_ingredients ri
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE ri.recipe_id IN ({placeholders})
        GROUP BY ri.ingredient_id, ri.unit
        ORDER BY i.category, i.name
        ''', recipe_ids)
        
        # Add ingredients to the shopping list
        for row in self.cursor.fetchall():
            ingredient_id = row[0]
            quantity = row[2]
            unit = row[3]
            
            self.add_shopping_list_item(shopping_list_id, ingredient_id, quantity, unit)
        
        return shopping_list_id
    
    # Recipe import/export operations
    def export_recipe_to_json(self, recipe_id):
        """
        Export a recipe to JSON format.
        
        Args:
            recipe_id (int): ID of the recipe to export
            
        Returns:
            str: JSON string representation of the recipe
        """
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return None
        
        return json.dumps(recipe, indent=2)
    
    def import_recipe_from_json(self, json_data):
        """
        Import a recipe from JSON format.
        
        Args:
            json_data (str): JSON string representation of the recipe
            
        Returns:
            int: ID of the imported recipe
        """
        try:
            recipe_data = json.loads(json_data)
            return self.add_recipe(recipe_data)
        except json.JSONDecodeError:
            return None


class RecipeApp:
    """
    Main application class for the Recipe Organization System.
    Handles the GUI and interaction with the database.
    """
    
    def __init__(self, root):
        """
        Initialize the Recipe Organization System application.
        
        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.root.title("Recipe Organization System")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Initialize database
        self.db = RecipeDatabase()
        
        # Set up theme
        self.setup_theme()
        
        # Create main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def setup_theme(self):
        """Set up the application theme and styling."""
        style = ttk.Style()
        
        # Configure theme
        style.configure("TFrame", background="#f5f5f5")
        style.configure("TLabel", background="#f5f5f5", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10))
        style.configure("TNotebook", background="#f5f5f5", tabposition="n")
        style.configure("TNotebook.Tab", padding=[10, 4], font=("Arial", 10))
        
        # Configure headings
        style.configure("Heading.TLabel", font=("Arial", 14, "bold"))
        style.configure("Subheading.TLabel", font=("Arial", 12, "bold"))
        
        # Configure list styles
        style.configure("RecipeList.TFrame", background="white", relief="solid", borderwidth=1)
        style.configure("RecipeListItem.TFrame", background="white")
        style.configure("RecipeListItem.TLabel", background="white", font=("Arial", 10))
        
        # Configure form styles
        style.configure("Form.TFrame", background="#f5f5f5", padding=10)
        style.configure("Form.TLabel", background="#f5f5f5", font=("Arial", 10))
        style.configure("Form.TEntry", font=("Arial", 10))
        
        # Configure recipe view styles
        style.configure("Recipe.TFrame", background="white", relief="solid", borderwidth=1, padding=10)
        style.configure("Recipe.TLabel", background="white", font=("Arial", 10))
        style.configure("RecipeTitle.TLabel", background="white", font=("Arial", 16, "bold"))
        
        # Configure favorite button
        style.configure("Favorite.TButton", font=("Arial", 12))
        
        # Configure shopping list styles
        style.configure("ShoppingList.TFrame", background="white", relief="solid", borderwidth=1)
        style.configure("ShoppingListItem.TFrame", background="white")
        style.configure("ShoppingListItem.TLabel", background="white", font=("Arial", 10))
        style.configure("ShoppingListSection.TLabel", background="white", font=("Arial", 11, "bold"))
    
    def create_widgets(self):
        """Create all the widgets for the application."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create recipe tab
        self.recipes_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.recipes_tab, text="Recipes")
        
        # Create shopping lists tab
        self.shopping_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.shopping_tab, text="Shopping Lists")
        
        # Create import/export tab
        self.import_export_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.import_export_tab, text="Import/Export")
        
        # Set up recipe tab
        self.setup_recipes_tab()
        
        # Set up shopping lists tab
        self.setup_shopping_tab()
        
        # Set up import/export tab
        self.setup_import_export_tab()
        
        # Create status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Ready")
    
    def setup_recipes_tab(self):
        """Set up the recipes tab with list and detail views."""
        # Create splitview: recipe list on left, recipe detail on right
        self.recipe_paned = ttk.PanedWindow(self.recipes_tab, orient=tk.HORIZONTAL)
        self.recipe_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create recipe list frame
        self.recipe_list_frame = ttk.Frame(self.recipe_paned)
        self.recipe_paned.add(self.recipe_list_frame, weight=1)
        
        # Create recipe detail frame
        self.recipe_detail_frame = ttk.Frame(self.recipe_paned)
        self.recipe_paned.add(self.recipe_detail_frame, weight=2)
        
        # Set up recipe list section
        self.setup_recipe_list()
        
        # Set up recipe detail section
        self.setup_recipe_detail()
    
    def setup_recipe_list(self):
        """Set up the recipe list part of the recipes tab."""
        # Create recipe list frame header
        list_header = ttk.Frame(self.recipe_list_frame)
        list_header.pack(fill=tk.X, padx=5, pady=5)
        
        # Create heading
        heading = ttk.Label(list_header, text="Recipes", style="Heading.TLabel")
        heading.pack(side=tk.LEFT, padx=5)
        
        # Create search box
        search_frame = ttk.Frame(list_header)
        search_frame.pack(side=tk.RIGHT, padx=5, pady=2)
        
        search_label = ttk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=2)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.search_recipes)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=15)
        search_entry.pack(side=tk.LEFT, padx=2)
        
        # Create filter frame
        filter_frame = ttk.Frame(self.recipe_list_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Create category filter
        category_label = ttk.Label(filter_frame, text="Category:")
        category_label.pack(side=tk.LEFT, padx=2)
        
        self.category_var = tk.StringVar()
        self.category_var.trace("w", self.search_recipes)
        # We'll populate categories later after DB is initialized
        self.category_var.set("All")
        category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var, width=12, state="readonly")
        category_combo.pack(side=tk.LEFT, padx=2)
        
        # Create tag filter
        tag_label = ttk.Label(filter_frame, text="Tag:")
        tag_label.pack(side=tk.LEFT, padx=2)
        
        self.tag_var = tk.StringVar()
        self.tag_var.trace("w", self.search_recipes)
        # We'll populate tags later after DB is initialized
        self.tag_var.set("All")
        tag_combo = ttk.Combobox(filter_frame, textvariable=self.tag_var, width=12, state="readonly")
        tag_combo.pack(side=tk.LEFT, padx=2)
        
        # Create favorites checkbox
        self.favorite_var = tk.BooleanVar()
        self.favorite_var.trace("w", self.search_recipes)
        favorite_check = ttk.Checkbutton(filter_frame, text="Favorites", variable=self.favorite_var)
        favorite_check.pack(side=tk.LEFT, padx=5)
        
        # Add recipe button
        add_recipe_btn = ttk.Button(self.recipe_list_frame, text="Add New Recipe", command=self.new_recipe)
        add_recipe_btn.pack(fill=tk.X, padx=5, pady=5)
        
        # Create scrollable frame for recipe list
        # Create canvas for scrollable recipe list
        self.recipe_canvas = tk.Canvas(self.recipe_list_frame, borderwidth=0, background="#ffffff")
        self.recipe_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar
        recipe_scrollbar = ttk.Scrollbar(self.recipe_list_frame, orient=tk.VERTICAL, command=self.recipe_canvas.yview)
        recipe_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.recipe_canvas.configure(yscrollcommand=recipe_scrollbar.set)
        
        # Create frame for recipe items inside canvas
        self.recipe_list_inner = ttk.Frame(self.recipe_canvas, style="RecipeList.TFrame")
        self.recipe_canvas_window = self.recipe_canvas.create_window(
            (0, 0), window=self.recipe_list_inner, anchor=tk.NW, tags="self.recipe_list_inner"
        )
        
        # Configure canvas to resize with frame
        self.recipe_list_inner.bind("<Configure>", self.on_recipe_list_configure)
        self.recipe_canvas.bind("<Configure>", self.on_recipe_canvas_configure)
        
        # Update the comboboxes with actual values
        try:
            # Try to populate categories and tags from database
            categories = ["All"] + self.db.get_all_categories()
            tags = ["All"] + self.db.get_all_tags()
            
            category_combo['values'] = categories
            tag_combo['values'] = tags
            category_combo.current(0)
            tag_combo.current(0)
        except:
            # If database isn't ready yet, we'll update these later
            pass
        
        # Load recipes
        self.load_recipe_list()
    
    def on_recipe_list_configure(self, event):
        """Handle recipe list inner frame configuration."""
        # Update the scrollregion to encompass the inner frame
        self.recipe_canvas.configure(scrollregion=self.recipe_canvas.bbox(tk.ALL))
    
    def on_recipe_canvas_configure(self, event):
        """Handle recipe canvas configuration."""
        # Update the width of the inner frame to fill the canvas
        self.recipe_canvas.itemconfig(self.recipe_canvas_window, width=event.width)
    
    def load_recipe_list(self):
        """Load recipes into the recipe list."""
        # Clear existing items
        for widget in self.recipe_list_inner.winfo_children():
            widget.destroy()
        
        # Get recipes based on search/filter
        search_term = self.search_var.get() if hasattr(self, 'search_var') else ""
        category = self.category_var.get() if hasattr(self, 'category_var') and self.category_var.get() != "All" else None
        tag = self.tag_var.get() if hasattr(self, 'tag_var') and self.tag_var.get() != "All" else None
        favorite = self.favorite_var.get() if hasattr(self, 'favorite_var') else None
        
        # Prepare filter parameters
        categories = [category] if category else None
        tags = [tag] if tag else None
        
        # Search for recipes
        recipes = self.db.search_recipes(search_term, categories, tags, favorite)
        
        if not recipes:
            # Show no recipes message
            no_recipes = ttk.Label(self.recipe_list_inner, text="No recipes found", style="RecipeListItem.TLabel")
            no_recipes.pack(fill=tk.X, padx=10, pady=10)
        else:
            # Add recipe items
            for recipe in recipes:
                self.create_recipe_list_item(recipe)
    
    def create_recipe_list_item(self, recipe):
        """Create a recipe list item widget."""
        # Create frame for recipe item
        recipe_frame = ttk.Frame(self.recipe_list_inner, style="RecipeListItem.TFrame")
        recipe_frame.pack(fill=tk.X, padx=2, pady=2)
        recipe_frame.bind("<Button-1>", lambda e, r=recipe: self.load_recipe_detail(r["id"]))
        
        # Create recipe item content
        name_label = ttk.Label(
            recipe_frame, 
            text=recipe["name"],
            style="RecipeListItem.TLabel",
            font=("Arial", 11, "bold" if recipe["favorite"] else "normal")
        )
        name_label.pack(anchor=tk.W, padx=5, pady=2)
        name_label.bind("<Button-1>", lambda e, r=recipe: self.load_recipe_detail(r["id"]))
        
        # Add recipe description if available
        if recipe["description"]:
            desc = recipe["description"]
            if len(desc) > 60:
                desc = desc[:57] + "..."
            desc_label = ttk.Label(recipe_frame, text=desc, style="RecipeListItem.TLabel")
            desc_label.pack(anchor=tk.W, padx=5)
            desc_label.bind("<Button-1>", lambda e, r=recipe: self.load_recipe_detail(r["id"]))
        
        # Add cooking time if available
        if recipe["prep_time"] or recipe["cook_time"]:
            total_time = (recipe["prep_time"] or 0) + (recipe["cook_time"] or 0)
            time_label = ttk.Label(
                recipe_frame, 
                text=f"{total_time} min • {recipe['difficulty']}",
                style="RecipeListItem.TLabel"
            )
            time_label.pack(anchor=tk.W, padx=5, pady=2)
            time_label.bind("<Button-1>", lambda e, r=recipe: self.load_recipe_detail(r["id"]))
        
        # Add separator
        ttk.Separator(self.recipe_list_inner, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=3)
    
    def setup_recipe_detail(self):
        """Set up the recipe detail part of the recipes tab."""
        # Create a frame for recipe editing form
        self.recipe_form_frame = ttk.Frame(self.recipe_detail_frame, style="Form.TFrame")
        self.recipe_form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initially hide the form
        self.recipe_form_frame.pack_forget()
        
        # Create view for recipe details
        self.recipe_view_frame = ttk.Frame(self.recipe_detail_frame, style="Recipe.TFrame")
        self.recipe_view_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initially show a welcome message in detail view
        welcome_label = ttk.Label(
            self.recipe_view_frame, 
            text="Welcome to Recipe Organization System",
            style="RecipeTitle.TLabel"
        )
        welcome_label.pack(pady=20)
        
        instruction_label = ttk.Label(
            self.recipe_view_frame,
            text="Select a recipe from the list on the left or create a new recipe.",
            style="Recipe.TLabel"
        )
        instruction_label.pack(pady=10)
    
    def search_recipes(self, *args):
        """Handle recipe search and filtering."""
        self.load_recipe_list()
    
    def new_recipe(self):
        """Create a new recipe."""
        # Clear the recipe detail view
        for widget in self.recipe_view_frame.winfo_children():
            widget.destroy()
        
        # Hide recipe view and show recipe form
        self.recipe_view_frame.pack_forget()
        self.recipe_form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Clear form
        for widget in self.recipe_form_frame.winfo_children():
            widget.destroy()
        
        # Create form header
        form_header = ttk.Frame(self.recipe_form_frame)
        form_header.pack(fill=tk.X, pady=5)
        
        heading = ttk.Label(form_header, text="New Recipe", style="Heading.TLabel")
        heading.pack(side=tk.LEFT, padx=5)
        
        # Create form content in a scrollable canvas
        canvas = tk.Canvas(self.recipe_form_frame, borderwidth=0, background="#f5f5f5")
        scrollbar = ttk.Scrollbar(self.recipe_form_frame, orient=tk.VERTICAL, command=canvas.yview)
        
        form_inner = ttk.Frame(canvas)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas_window = canvas.create_window((0, 0), window=form_inner, anchor=tk.NW)
        
        def on_form_configure(event):
            canvas.configure(scrollregion=canvas.bbox(tk.ALL))
            canvas.itemconfig(canvas_window, width=event.width)
        
        form_inner.bind("<Configure>", on_form_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        
        # Basic info section
        basic_frame = ttk.LabelFrame(form_inner, text="Basic Information")
        basic_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Name field
        name_frame = ttk.Frame(basic_frame)
        name_frame.pack(fill=tk.X, padx=5, pady=5)
        
        name_label = ttk.Label(name_frame, text="Recipe Name:")
        name_label.pack(side=tk.LEFT, padx=5)
        
        self.recipe_name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=self.recipe_name_var, width=40)
        name_entry.pack(side=tk.LEFT, padx=5)
        
        # Favorite checkbox
        self.recipe_favorite_var = tk.BooleanVar()
        favorite_check = ttk.Checkbutton(name_frame, text="Favorite", variable=self.recipe_favorite_var)
        favorite_check.pack(side=tk.LEFT, padx=5)
        
        # Description field
        desc_frame = ttk.Frame(basic_frame)
        desc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        desc_label = ttk.Label(desc_frame, text="Description:")
        desc_label.pack(anchor=tk.W, padx=5)
        
        self.recipe_desc_var = tk.StringVar()
        desc_entry = ttk.Entry(desc_frame, textvariable=self.recipe_desc_var, width=60)
        desc_entry.pack(fill=tk.X, padx=5, pady=2)
        
        # Time and servings frame
        time_frame = ttk.Frame(basic_frame)
        time_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Prep time
        prep_label = ttk.Label(time_frame, text="Prep Time (min):")
        prep_label.pack(side=tk.LEFT, padx=5)
        
        self.prep_time_var = tk.StringVar()
        prep_entry = ttk.Entry(time_frame, textvariable=self.prep_time_var, width=5)
        prep_entry.pack(side=tk.LEFT, padx=2)
        
        # Cook time
        cook_label = ttk.Label(time_frame, text="Cook Time (min):")
        cook_label.pack(side=tk.LEFT, padx=5)
        
        self.cook_time_var = tk.StringVar()
        cook_entry = ttk.Entry(time_frame, textvariable=self.cook_time_var, width=5)
        cook_entry.pack(side=tk.LEFT, padx=2)
        
        # Servings
        servings_label = ttk.Label(time_frame, text="Servings:")
        servings_label.pack(side=tk.LEFT, padx=5)
        
        self.servings_var = tk.StringVar()
        servings_entry = ttk.Entry(time_frame, textvariable=self.servings_var, width=5)
        servings_entry.pack(side=tk.LEFT, padx=2)
        
        # Difficulty
        difficulty_label = ttk.Label(time_frame, text="Difficulty:")
        difficulty_label.pack(side=tk.LEFT, padx=5)
        
        self.difficulty_var = tk.StringVar()
        difficulty_combo = ttk.Combobox(time_frame, textvariable=self.difficulty_var, 
                                      values=["Easy", "Medium", "Hard"], width=8, state="readonly")
        difficulty_combo.current(1)  # Default to Medium
        difficulty_combo.pack(side=tk.LEFT, padx=2)
        
        # Source
        source_frame = ttk.Frame(basic_frame)
        source_frame.pack(fill=tk.X, padx=5, pady=5)
        
        source_label = ttk.Label(source_frame, text="Source:")
        source_label.pack(side=tk.LEFT, padx=5)
        
        self.source_var = tk.StringVar()
        source_entry = ttk.Entry(source_frame, textvariable=self.source_var, width=40)
        source_entry.pack(side=tk.LEFT, padx=5)
        
        # Categories and Tags section
        cat_tag_frame = ttk.LabelFrame(form_inner, text="Categories and Tags")
        cat_tag_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Categories
        cat_frame = ttk.Frame(cat_tag_frame)
        cat_frame.pack(fill=tk.X, padx=5, pady=5)
        
        cat_label = ttk.Label(cat_frame, text="Categories:")
        cat_label.pack(side=tk.LEFT, padx=5)
        
        # Get all categories
        all_categories = self.db.get_all_categories()
        
        # Categories listbox with scrollbar
        cat_listbox_frame = ttk.Frame(cat_frame)
        cat_listbox_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.cat_listbox = tk.Listbox(cat_listbox_frame, selectmode=tk.MULTIPLE, height=4)
        cat_scrollbar = ttk.Scrollbar(cat_listbox_frame, orient=tk.VERTICAL, command=self.cat_listbox.yview)
        
        self.cat_listbox.configure(yscrollcommand=cat_scrollbar.set)
        
        self.cat_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        cat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate categories
        for category in all_categories:
            self.cat_listbox.insert(tk.END, category)
        
        # New category button
        new_cat_btn = ttk.Button(cat_frame, text="New Category", command=self.add_new_category)
        new_cat_btn.pack(side=tk.LEFT, padx=5)
        
        # Tags
        tag_frame = ttk.Frame(cat_tag_frame)
        tag_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tag_label = ttk.Label(tag_frame, text="Tags:")
        tag_label.pack(side=tk.LEFT, padx=5)
        
        # Get all tags
        all_tags = self.db.get_all_tags()
        
        # Tags listbox with scrollbar
        tag_listbox_frame = ttk.Frame(tag_frame)
        tag_listbox_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.tag_listbox = tk.Listbox(tag_listbox_frame, selectmode=tk.MULTIPLE, height=4)
        tag_scrollbar = ttk.Scrollbar(tag_listbox_frame, orient=tk.VERTICAL, command=self.tag_listbox.yview)
        
        self.tag_listbox.configure(yscrollcommand=tag_scrollbar.set)
        
        self.tag_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tag_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate tags
        for tag in all_tags:
            self.tag_listbox.insert(tk.END, tag)
        
        # New tag button
        new_tag_btn = ttk.Button(tag_frame, text="New Tag", command=self.add_new_tag)
        new_tag_btn.pack(side=tk.LEFT, padx=5)
        
        # Ingredients section
        ingredients_frame = ttk.LabelFrame(form_inner, text="Ingredients")
        ingredients_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Ingredients list
        self.ingredients_list_frame = ttk.Frame(ingredients_frame)
        self.ingredients_list_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Ingredient list will be populated here
        self.ingredients = []  # Store ingredient data
        
        # Add ingredient button
        add_ing_btn = ttk.Button(ingredients_frame, text="Add Ingredient", command=self.add_ingredient_row)
        add_ing_btn.pack(padx=5, pady=5)
        
        # Instructions section
        instr_frame = ttk.LabelFrame(form_inner, text="Instructions")
        instr_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.instructions_text = ScrolledText(instr_frame, height=10, width=50, wrap=tk.WORD)
        self.instructions_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Notes section
        notes_frame = ttk.LabelFrame(form_inner, text="Notes")
        notes_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.notes_text = ScrolledText(notes_frame, height=5, width=50, wrap=tk.WORD)
        self.notes_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Button frame
        btn_frame = ttk.Frame(form_inner)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Save button
        save_btn = ttk.Button(btn_frame, text="Save Recipe", command=self.save_new_recipe)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.cancel_recipe_edit)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Add a single ingredient row to start
        self.add_ingredient_row()
    
    def add_ingredient_row(self):
        """Add a new ingredient row to the form."""
        row_frame = ttk.Frame(self.ingredients_list_frame)
        row_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Quantity field
        quantity_var = tk.StringVar()
        quantity_entry = ttk.Entry(row_frame, textvariable=quantity_var, width=6)
        quantity_entry.pack(side=tk.LEFT, padx=2)
        
        # Unit field
        unit_var = tk.StringVar()
        unit_entry = ttk.Entry(row_frame, textvariable=unit_var, width=8)
        unit_entry.pack(side=tk.LEFT, padx=2)
        
        # Ingredient name field
        name_var = tk.StringVar()
        name_entry = ttk.Entry(row_frame, textvariable=name_var, width=30)
        name_entry.pack(side=tk.LEFT, padx=2)
        
        # Notes field
        notes_var = tk.StringVar()
        notes_entry = ttk.Entry(row_frame, textvariable=notes_var, width=20)
        notes_entry.pack(side=tk.LEFT, padx=2)
        
        # Remove button
        def remove_ingredient():
            row_frame.destroy()
            self.ingredients.remove(ingredient_data)
        
        remove_btn = ttk.Button(row_frame, text="X", width=2, command=remove_ingredient)
        remove_btn.pack(side=tk.LEFT, padx=2)
        
        # Store the ingredient data
        ingredient_data = {
            "row_frame": row_frame,
            "quantity_var": quantity_var,
            "unit_var": unit_var,
            "name_var": name_var,
            "notes_var": notes_var
        }
        
        self.ingredients.append(ingredient_data)
    
    def add_new_category(self):
        """Add a new category to the database."""
        new_category = simpledialog.askstring("New Category", "Enter new category name:")
        if new_category and new_category.strip():
            # Add to database
            self.cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (new_category,))
            self.conn.commit()
            
            # Add to list
            self.cat_listbox.insert(tk.END, new_category)
    
    def add_new_tag(self):
        """Add a new tag to the database."""
        new_tag = simpledialog.askstring("New Tag", "Enter new tag name:")
        if new_tag and new_tag.strip():
            # Add to database
            self.cursor.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (new_tag,))
            self.conn.commit()
            
            # Add to list
            self.tag_listbox.insert(tk.END, new_tag)
    
    def save_new_recipe(self):
        """Save a new recipe to the database."""
        # Validate required fields
        if not self.recipe_name_var.get().strip():
            messagebox.showerror("Error", "Recipe name is required")
            return
        
        # Gather recipe data
        recipe_data = {
            "name": self.recipe_name_var.get().strip(),
            "description": self.recipe_desc_var.get().strip(),
            "instructions": self.instructions_text.get("1.0", tk.END).strip(),
            "prep_time": int(self.prep_time_var.get() or 0),
            "cook_time": int(self.cook_time_var.get() or 0),
            "servings": int(self.servings_var.get() or 1),
            "difficulty": self.difficulty_var.get(),
            "source": self.source_var.get().strip(),
            "notes": self.notes_text.get("1.0", tk.END).strip(),
            "favorite": self.recipe_favorite_var.get(),
            "categories": [self.cat_listbox.get(idx) for idx in self.cat_listbox.curselection()],
            "tags": [self.tag_listbox.get(idx) for idx in self.tag_listbox.curselection()],
            "ingredients": []
        }
        
        # Process ingredients
        for ingredient in self.ingredients:
            # Skip empty ingredients
            if not ingredient["name_var"].get().strip():
                continue
                
            ingredient_data = {
                "name": ingredient["name_var"].get().strip(),
                "quantity": float(ingredient["quantity_var"].get() or 0),
                "unit": ingredient["unit_var"].get().strip(),
                "notes": ingredient["notes_var"].get().strip()
            }
            recipe_data["ingredients"].append(ingredient_data)
        
        # Add recipe to database
        recipe_id = self.db.add_recipe(recipe_data)
        
        if recipe_id:
            messagebox.showinfo("Success", "Recipe added successfully!")
            # Load the recipe detail view
            self.load_recipe_detail(recipe_id)
            # Refresh recipe list
            self.load_recipe_list()
        else:
            messagebox.showerror("Error", "Failed to add recipe")
    
    def cancel_recipe_edit(self):
        """Cancel recipe editing and go back to recipe list view."""
        # Clear form
        self.recipe_form_frame.pack_forget()
        
        # Show recipe view frame
        self.recipe_view_frame.pack(fill=tk.BOTH, expand=True)
        
        # If current recipe, reload it, otherwise show welcome message
        if hasattr(self, 'current_recipe_id'):
            self.load_recipe_detail(self.current_recipe_id)
        else:
            # Clear recipe view
            for widget in self.recipe_view_frame.winfo_children():
                widget.destroy()
            
            # Add welcome message
            welcome_label = ttk.Label(
                self.recipe_view_frame, 
                text="Welcome to Recipe Organization System",
                style="RecipeTitle.TLabel"
            )
            welcome_label.pack(pady=20)
            
            instruction_label = ttk.Label(
                self.recipe_view_frame,
                text="Select a recipe from the list on the left or create a new recipe.",
                style="Recipe.TLabel"
            )
            instruction_label.pack(pady=10)
    
    def load_recipe_detail(self, recipe_id):
        """
        Load and display recipe details.
        
        Args:
            recipe_id (int): ID of the recipe to display
        """
        # Store current recipe ID
        self.current_recipe_id = recipe_id
        
        # Get recipe data
        recipe = self.db.get_recipe(recipe_id)
        
        if not recipe:
            messagebox.showerror("Error", "Recipe not found")
            return
        
        # Clear recipe view
        for widget in self.recipe_view_frame.winfo_children():
            widget.destroy()
        
        # Hide recipe form and show recipe view
        self.recipe_form_frame.pack_forget()
        self.recipe_view_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a scrollable canvas for recipe content
        canvas = tk.Canvas(self.recipe_view_frame, borderwidth=0, background="white")
        scrollbar = ttk.Scrollbar(self.recipe_view_frame, orient=tk.VERTICAL, command=canvas.yview)
        
        content_frame = ttk.Frame(canvas, style="Recipe.TFrame")
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor=tk.NW)
        
        def on_content_configure(event):
            canvas.configure(scrollregion=canvas.bbox(tk.ALL))
            canvas.itemconfig(canvas_window, width=event.width)
        
        content_frame.bind("<Configure>", on_content_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        
        # Recipe header
        header_frame = ttk.Frame(content_frame, style="Recipe.TFrame")
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Recipe title
        title_label = ttk.Label(
            header_frame, 
            text=recipe["name"],
            style="RecipeTitle.TLabel"
        )
        title_label.pack(side=tk.LEFT, pady=5)
        
        # Star for favorite recipes
        if recipe["favorite"]:
            favorite_label = ttk.Label(
                header_frame,
                text="★",
                font=("Arial", 16),
                foreground="gold"
            )
            favorite_label.pack(side=tk.LEFT, padx=5)
        
        # Button frame
        btn_frame = ttk.Frame(header_frame, style="Recipe.TFrame")
        btn_frame.pack(side=tk.RIGHT)
        
        # Edit button
        edit_btn = ttk.Button(
            btn_frame, 
            text="Edit", 
            command=lambda: self.edit_recipe(recipe_id)
        )
        edit_btn.pack(side=tk.LEFT, padx=2)
        
        # Delete button
        delete_btn = ttk.Button(
            btn_frame, 
            text="Delete", 
            command=lambda: self.delete_recipe(recipe_id)
        )
        delete_btn.pack(side=tk.LEFT, padx=2)
        
        # Add to shopping list button
        add_to_shopping_btn = ttk.Button(
            btn_frame,
            text="Add to Shopping List",
            command=lambda: self.add_recipe_to_shopping_list(recipe_id)
        )
        add_to_shopping_btn.pack(side=tk.LEFT, padx=2)
        
        # Recipe description
        if recipe["description"]:
            desc_label = ttk.Label(
                content_frame,
                text=recipe["description"],
                style="Recipe.TLabel",
                wraplength=600
            )
            desc_label.pack(fill=tk.X, padx=10, pady=5)
        
        # Recipe meta information
        meta_frame = ttk.Frame(content_frame, style="Recipe.TFrame")
        meta_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Time and servings
        time_frame = ttk.Frame(meta_frame, style="Recipe.TFrame")
        time_frame.pack(side=tk.LEFT, padx=10)
        
        if recipe["prep_time"] or recipe["cook_time"]:
            prep_time = recipe["prep_time"] or 0
            cook_time = recipe["cook_time"] or 0
            total_time = prep_time + cook_time
            
            if prep_time > 0:
                prep_label = ttk.Label(
                    time_frame,
                    text=f"Prep time: {prep_time} min",
                    style="Recipe.TLabel"
                )
                prep_label.pack(anchor=tk.W)
            
            if cook_time > 0:
                cook_label = ttk.Label(
                    time_frame,
                    text=f"Cook time: {cook_time} min",
                    style="Recipe.TLabel"
                )
                cook_label.pack(anchor=tk.W)
            
            total_label = ttk.Label(
                time_frame,
                text=f"Total time: {total_time} min",
                style="Recipe.TLabel"
            )
            total_label.pack(anchor=tk.W)
        
        if recipe["servings"]:
            servings_label = ttk.Label(
                time_frame,
                text=f"Servings: {recipe['servings']}",
                style="Recipe.TLabel"
            )
            servings_label.pack(anchor=tk.W)
        
        difficulty_label = ttk.Label(
            time_frame,
            text=f"Difficulty: {recipe['difficulty']}",
            style="Recipe.TLabel"
        )
        difficulty_label.pack(anchor=tk.W)
        
        # Categories and tags
        tags_frame = ttk.Frame(meta_frame, style="Recipe.TFrame")
        tags_frame.pack(side=tk.LEFT, padx=10)
        
        if recipe["categories"]:
            cat_label = ttk.Label(
                tags_frame,
                text="Categories: " + ", ".join(recipe["categories"]),
                style="Recipe.TLabel"
            )
            cat_label.pack(anchor=tk.W)
        
        if recipe["tags"]:
            tags_label = ttk.Label(
                tags_frame,
                text="Tags: " + ", ".join(recipe["tags"]),
                style="Recipe.TLabel"
            )
            tags_label.pack(anchor=tk.W)
        
        # Separator
        ttk.Separator(content_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)
        
        # Ingredients section
        if recipe["ingredients"]:
            ing_frame = ttk.LabelFrame(content_frame, text="Ingredients", style="Recipe.TFrame")
            ing_frame.pack(fill=tk.X, padx=10, pady=5)
            
            for ingredient in recipe["ingredients"]:
                quantity = ingredient["quantity"] or ""
                unit = ingredient["unit"] or ""
                name = ingredient["name"]
                notes = ingredient["notes"] or ""
                
                ing_text = f"{quantity} {unit} {name}"
                if notes:
                    ing_text += f" ({notes})"
                
                ing_label = ttk.Label(
                    ing_frame,
                    text=ing_text,
                    style="Recipe.TLabel"
                )
                ing_label.pack(anchor=tk.W, padx=10, pady=2)
        
        # Instructions section
        if recipe["instructions"]:
            instr_frame = ttk.LabelFrame(content_frame, text="Instructions", style="Recipe.TFrame")
            instr_frame.pack(fill=tk.X, padx=10, pady=5)
            
            instr_text = ttk.Label(
                instr_frame,
                text=recipe["instructions"],
                style="Recipe.TLabel",
                wraplength=600,
                justify=tk.LEFT
            )
            instr_text.pack(fill=tk.X, padx=10, pady=5)
        
        # Notes section
        if recipe["notes"]:
            notes_frame = ttk.LabelFrame(content_frame, text="Notes", style="Recipe.TFrame")
            notes_frame.pack(fill=tk.X, padx=10, pady=5)
            
            notes_text = ttk.Label(
                notes_frame,
                text=recipe["notes"],
                style="Recipe.TLabel",
                wraplength=600,
                justify=tk.LEFT
            )
            notes_text.pack(fill=tk.X, padx=10, pady=5)
        
        # Source section
        if recipe["source"]:
            source_frame = ttk.Frame(content_frame, style="Recipe.TFrame")
            source_frame.pack(fill=tk.X, padx=10, pady=5)
            
            source_label = ttk.Label(
                source_frame,
                text=f"Source: {recipe['source']}",
                style="Recipe.TLabel"
            )
            source_label.pack(anchor=tk.W, padx=10, pady=2)
    
    def edit_recipe(self, recipe_id):
        """
        Edit an existing recipe.
        
        Args:
            recipe_id (int): ID of the recipe to edit
        """
        # Get recipe data
        recipe = self.db.get_recipe(recipe_id)
        
        if not recipe:
            messagebox.showerror("Error", "Recipe not found")
            return
        
        # Clear the recipe detail view
        for widget in self.recipe_view_frame.winfo_children():
            widget.destroy()
        
        # Hide recipe view and show recipe form
        self.recipe_view_frame.pack_forget()
        self.recipe_form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Clear form
        for widget in self.recipe_form_frame.winfo_children():
            widget.destroy()
        
        # Create form header
        form_header = ttk.Frame(self.recipe_form_frame)
        form_header.pack(fill=tk.X, pady=5)
        
        heading = ttk.Label(form_header, text=f"Edit Recipe: {recipe['name']}", style="Heading.TLabel")
        heading.pack(side=tk.LEFT, padx=5)
        
        # Create form content in a scrollable canvas
        canvas = tk.Canvas(self.recipe_form_frame, borderwidth=0, background="#f5f5f5")
        scrollbar = ttk.Scrollbar(self.recipe_form_frame, orient=tk.VERTICAL, command=canvas.yview)
        
        form_inner = ttk.Frame(canvas)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas_window = canvas.create_window((0, 0), window=form_inner, anchor=tk.NW)
        
        def on_form_configure(event):
            canvas.configure(scrollregion=canvas.bbox(tk.ALL))
            canvas.itemconfig(canvas_window, width=event.width)
        
        form_inner.bind("<Configure>", on_form_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        
        # Basic info section
        basic_frame = ttk.LabelFrame(form_inner, text="Basic Information")
        basic_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Name field
        name_frame = ttk.Frame(basic_frame)
        name_frame.pack(fill=tk.X, padx=5, pady=5)
        
        name_label = ttk.Label(name_frame, text="Recipe Name:")
        name_label.pack(side=tk.LEFT, padx=5)
        
        self.recipe_name_var = tk.StringVar(value=recipe["name"])
        name_entry = ttk.Entry(name_frame, textvariable=self.recipe_name_var, width=40)
        name_entry.pack(side=tk.LEFT, padx=5)
        
        # Favorite checkbox
        self.recipe_favorite_var = tk.BooleanVar(value=recipe["favorite"])
        favorite_check = ttk.Checkbutton(name_frame, text="Favorite", variable=self.recipe_favorite_var)
        favorite_check.pack(side=tk.LEFT, padx=5)
        
        # Description field
        desc_frame = ttk.Frame(basic_frame)
        desc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        desc_label = ttk.Label(desc_frame, text="Description:")
        desc_label.pack(anchor=tk.W, padx=5)
        
        self.recipe_desc_var = tk.StringVar(value=recipe["description"])
        desc_entry = ttk.Entry(desc_frame, textvariable=self.recipe_desc_var, width=60)
        desc_entry.pack(fill=tk.X, padx=5, pady=2)
        
        # Time and servings frame
        time_frame = ttk.Frame(basic_frame)
        time_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Prep time
        prep_label = ttk.Label(time_frame, text="Prep Time (min):")
        prep_label.pack(side=tk.LEFT, padx=5)
        
        self.prep_time_var = tk.StringVar(value=recipe["prep_time"])
        prep_entry = ttk.Entry(time_frame, textvariable=self.prep_time_var, width=5)
        prep_entry.pack(side=tk.LEFT, padx=2)
        
        # Cook time
        cook_label = ttk.Label(time_frame, text="Cook Time (min):")
        cook_label.pack(side=tk.LEFT, padx=5)
        
        self.cook_time_var = tk.StringVar(value=recipe["cook_time"])
        cook_entry = ttk.Entry(time_frame, textvariable=self.cook_time_var, width=5)
        cook_entry.pack(side=tk.LEFT, padx=2)
        
        # Servings
        servings_label = ttk.Label(time_frame, text="Servings:")
        servings_label.pack(side=tk.LEFT, padx=5)
        
        self.servings_var = tk.StringVar(value=recipe["servings"])
        servings_entry = ttk.Entry(time_frame, textvariable=self.servings_var, width=5)
        servings_entry.pack(side=tk.LEFT, padx=2)
        
        # Difficulty
        difficulty_label = ttk.Label(time_frame, text="Difficulty:")
        difficulty_label.pack(side=tk.LEFT, padx=5)
        
        self.difficulty_var = tk.StringVar(value=recipe["difficulty"])
        difficulty_combo = ttk.Combobox(time_frame, textvariable=self.difficulty_var, 
                                      values=["Easy", "Medium", "Hard"], width=8, state="readonly")
        difficulty_combo.pack(side=tk.LEFT, padx=2)
        
        # Source
        source_frame = ttk.Frame(basic_frame)
        source_frame.pack(fill=tk.X, padx=5, pady=5)
        
        source_label = ttk.Label(source_frame, text="Source:")
        source_label.pack(side=tk.LEFT, padx=5)
        
        self.source_var = tk.StringVar(value=recipe["source"])
        source_entry = ttk.Entry(source_frame, textvariable=self.source_var, width=40)
        source_entry.pack(side=tk.LEFT, padx=5)
        
        # Categories and Tags section
        cat_tag_frame = ttk.LabelFrame(form_inner, text="Categories and Tags")
        cat_tag_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Categories
        cat_frame = ttk.Frame(cat_tag_frame)
        cat_frame.pack(fill=tk.X, padx=5, pady=5)
        
        cat_label = ttk.Label(cat_frame, text="Categories:")
        cat_label.pack(side=tk.LEFT, padx=5)
        
        # Get all categories
        all_categories = self.db.get_all_categories()
        
        # Categories listbox with scrollbar
        cat_listbox_frame = ttk.Frame(cat_frame)
        cat_listbox_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.cat_listbox = tk.Listbox(cat_listbox_frame, selectmode=tk.MULTIPLE, height=4)
        cat_scrollbar = ttk.Scrollbar(cat_listbox_frame, orient=tk.VERTICAL, command=self.cat_listbox.yview)
        
        self.cat_listbox.configure(yscrollcommand=cat_scrollbar.set)
        
        self.cat_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        cat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate categories and select current ones
        for i, category in enumerate(all_categories):
            self.cat_listbox.insert(tk.END, category)
            if category in recipe["categories"]:
                self.cat_listbox.selection_set(i)
        
        # New category button
        new_cat_btn = ttk.Button(cat_frame, text="New Category", command=self.add_new_category)
        new_cat_btn.pack(side=tk.LEFT, padx=5)
        
        # Tags
        tag_frame = ttk.Frame(cat_tag_frame)
        tag_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tag_label = ttk.Label(tag_frame, text="Tags:")
        tag_label.pack(side=tk.LEFT, padx=5)
        
        # Get all tags
        all_tags = self.db.get_all_tags()
        
        # Tags listbox with scrollbar
        tag_listbox_frame = ttk.Frame(tag_frame)
        tag_listbox_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.tag_listbox = tk.Listbox(tag_listbox_frame, selectmode=tk.MULTIPLE, height=4)
        tag_scrollbar = ttk.Scrollbar(tag_listbox_frame, orient=tk.VERTICAL, command=self.tag_listbox.yview)
        
        self.tag_listbox.configure(yscrollcommand=tag_scrollbar.set)
        
        self.tag_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tag_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate tags and select current ones
        for i, tag in enumerate(all_tags):
            self.tag_listbox.insert(tk.END, tag)
            if tag in recipe["tags"]:
                self.tag_listbox.selection_set(i)
        
        # New tag button
        new_tag_btn = ttk.Button(tag_frame, text="New Tag", command=self.add_new_tag)
        new_tag_btn.pack(side=tk.LEFT, padx=5)
        
        # Ingredients section
        ingredients_frame = ttk.LabelFrame(form_inner, text="Ingredients")
        ingredients_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Ingredients list
        self.ingredients_list_frame = ttk.Frame(ingredients_frame)
        self.ingredients_list_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Ingredient list will be populated here
        self.ingredients = []  # Store ingredient data
        
        # Add existing ingredients
        for ingredient in recipe["ingredients"]:
            self.add_ingredient_row(
                quantity=ingredient["quantity"],
                unit=ingredient["unit"],
                name=ingredient["name"],
                notes=ingredient["notes"]
            )
        
        # Add ingredient button
        add_ing_btn = ttk.Button(ingredients_frame, text="Add Ingredient", command=self.add_ingredient_row)
        add_ing_btn.pack(padx=5, pady=5)
        
        # Instructions section
        instr_frame = ttk.LabelFrame(form_inner, text="Instructions")
        instr_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.instructions_text = ScrolledText(instr_frame, height=10, width=50, wrap=tk.WORD)
        self.instructions_text.pack(fill=tk.X, padx=5, pady=5)
        self.instructions_text.insert(tk.END, recipe["instructions"])
        
        # Notes section
        notes_frame = ttk.LabelFrame(form_inner, text="Notes")
        notes_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.notes_text = ScrolledText(notes_frame, height=5, width=50, wrap=tk.WORD)
        self.notes_text.pack(fill=tk.X, padx=5, pady=5)
        self.notes_text.insert(tk.END, recipe["notes"])
        
        # Button frame
        btn_frame = ttk.Frame(form_inner)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Save button
        save_btn = ttk.Button(
            btn_frame, 
            text="Save Changes", 
            command=lambda: self.save_recipe_changes(recipe_id)
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.cancel_recipe_edit)
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def add_ingredient_row(self, quantity="", unit="", name="", notes=""):
        """
        Add a new ingredient row to the form.
        
        Args:
            quantity (float, optional): Ingredient quantity
            unit (str, optional): Ingredient unit
            name (str, optional): Ingredient name
            notes (str, optional): Ingredient notes
        """
        row_frame = ttk.Frame(self.ingredients_list_frame)
        row_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Quantity field
        quantity_var = tk.StringVar(value=quantity)
        quantity_entry = ttk.Entry(row_frame, textvariable=quantity_var, width=6)
        quantity_entry.pack(side=tk.LEFT, padx=2)
        
        # Unit field
        unit_var = tk.StringVar(value=unit)
        unit_entry = ttk.Entry(row_frame, textvariable=unit_var, width=8)
        unit_entry.pack(side=tk.LEFT, padx=2)
        
        # Ingredient name field
        name_var = tk.StringVar(value=name)
        name_entry = ttk.Entry(row_frame, textvariable=name_var, width=30)
        name_entry.pack(side=tk.LEFT, padx=2)
        
        # Notes field
        notes_var = tk.StringVar(value=notes)
        notes_entry = ttk.Entry(row_frame, textvariable=notes_var, width=20)
        notes_entry.pack(side=tk.LEFT, padx=2)
        
        # Remove button
        def remove_ingredient():
            row_frame.destroy()
            self.ingredients.remove(ingredient_data)
        
        remove_btn = ttk.Button(row_frame, text="X", width=2, command=remove_ingredient)
        remove_btn.pack(side=tk.LEFT, padx=2)
        
        # Store the ingredient data
        ingredient_data = {
            "row_frame": row_frame,
            "quantity_var": quantity_var,
            "unit_var": unit_var,
            "name_var": name_var,
            "notes_var": notes_var
        }
        
        self.ingredients.append(ingredient_data)
        
        return ingredient_data
    
    def save_recipe_changes(self, recipe_id):
        """
        Save changes to an existing recipe.
        
        Args:
            recipe_id (int): ID of the recipe to update
        """
        # Validate required fields
        if not self.recipe_name_var.get().strip():
            messagebox.showerror("Error", "Recipe name is required")
            return
        
        # Gather recipe data
        recipe_data = {
            "name": self.recipe_name_var.get().strip(),
            "description": self.recipe_desc_var.get().strip(),
            "instructions": self.instructions_text.get("1.0", tk.END).strip(),
            "prep_time": int(self.prep_time_var.get() or 0),
            "cook_time": int(self.cook_time_var.get() or 0),
            "servings": int(self.servings_var.get() or 1),
            "difficulty": self.difficulty_var.get(),
            "source": self.source_var.get().strip(),
            "notes": self.notes_text.get("1.0", tk.END).strip(),
            "favorite": self.recipe_favorite_var.get(),
            "categories": [self.cat_listbox.get(idx) for idx in self.cat_listbox.curselection()],
            "tags": [self.tag_listbox.get(idx) for idx in self.tag_listbox.curselection()],
            "ingredients": []
        }
        
        # Process ingredients
        for ingredient in self.ingredients:
            # Skip empty ingredients
            if not ingredient["name_var"].get().strip():
                continue
                
            ingredient_data = {
                "name": ingredient["name_var"].get().strip(),
                "quantity": float(ingredient["quantity_var"].get() or 0),
                "unit": ingredient["unit_var"].get().strip(),
                "notes": ingredient["notes_var"].get().strip()
            }
            recipe_data["ingredients"].append(ingredient_data)
        
        # Update recipe in database
        success = self.db.update_recipe(recipe_id, recipe_data)
        
        if success:
            messagebox.showinfo("Success", "Recipe updated successfully!")
            # Load the recipe detail view
            self.load_recipe_detail(recipe_id)
            # Refresh recipe list
            self.load_recipe_list()
        else:
            messagebox.showerror("Error", "Failed to update recipe")
    
    def delete_recipe(self, recipe_id):
        """
        Delete a recipe.
        
        Args:
            recipe_id (int): ID of the recipe to delete
        """
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion", 
            "Are you sure you want to delete this recipe? This cannot be undone."
        )
        
        if not confirm:
            return
        
        # Delete recipe from database
        success = self.db.delete_recipe(recipe_id)
        
        if success:
            messagebox.showinfo("Success", "Recipe deleted successfully!")
            # Clear current recipe ID
            if hasattr(self, 'current_recipe_id'):
                delattr(self, 'current_recipe_id')
            
            # Clear recipe detail view
            for widget in self.recipe_view_frame.winfo_children():
                widget.destroy()
            
            # Show welcome message
            welcome_label = ttk.Label(
                self.recipe_view_frame, 
                text="Welcome to Recipe Organization System",
                style="RecipeTitle.TLabel"
            )
            welcome_label.pack(pady=20)
            
            instruction_label = ttk.Label(
                self.recipe_view_frame,
                text="Select a recipe from the list on the left or create a new recipe.",
                style="Recipe.TLabel"
            )
            instruction_label.pack(pady=10)
            
            # Refresh recipe list
            self.load_recipe_list()
        else:
            messagebox.showerror("Error", "Failed to delete recipe.")
    
    def setup_shopping_tab(self):
        """Set up the shopping lists tab."""
        # Create splitview: list on left, detail on right
        self.shopping_paned = ttk.PanedWindow(self.shopping_tab, orient=tk.HORIZONTAL)
        self.shopping_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create shopping list frame
        self.shopping_list_frame = ttk.Frame(self.shopping_paned)
        self.shopping_paned.add(self.shopping_list_frame, weight=1)
        
        # Create shopping detail frame
        self.shopping_detail_frame = ttk.Frame(self.shopping_paned)
        self.shopping_paned.add(self.shopping_detail_frame, weight=2)
        
        # Set up shopping list section
        self.setup_shopping_list()
        
        # Set up shopping detail section
        self.setup_shopping_detail()
    
    def setup_shopping_list(self):
        """Set up the shopping list part of the shopping tab."""
        # Create list frame header
        list_header = ttk.Frame(self.shopping_list_frame)
        list_header.pack(fill=tk.X, padx=5, pady=5)
        
        # Create heading
        heading = ttk.Label(list_header, text="Shopping Lists", style="Heading.TLabel")
        heading.pack(side=tk.LEFT, padx=5)
        
        # Create shopping list buttons
        btn_frame = ttk.Frame(self.shopping_list_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # New shopping list button
        new_list_btn = ttk.Button(btn_frame, text="New Shopping List", command=self.new_shopping_list)
        new_list_btn.pack(side=tk.LEFT, padx=5)
        
        # Generate from recipes button
        gen_list_btn = ttk.Button(btn_frame, text="Generate from Recipes", command=self.generate_from_recipes)
        gen_list_btn.pack(side=tk.LEFT, padx=5)
        
        # Create canvas for scrollable shopping list
        self.shopping_canvas = tk.Canvas(self.shopping_list_frame, borderwidth=0, background="#ffffff")
        self.shopping_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar
        shopping_scrollbar = ttk.Scrollbar(self.shopping_canvas, orient=tk.VERTICAL, command=self.shopping_canvas.yview)
        self.shopping_canvas.configure(yscrollcommand=shopping_scrollbar.set)
        shopping_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create frame for shopping list items inside canvas
        self.shopping_list_inner = ttk.Frame(self.shopping_canvas, style="ShoppingList.TFrame")
        self.shopping_canvas_window = self.shopping_canvas.create_window(
            (0, 0), window=self.shopping_list_inner, anchor=tk.NW, tags="self.shopping_list_inner"
        )
        
        # Configure canvas to resize with frame
        self.shopping_list_inner.bind("<Configure>", self.on_shopping_list_configure)
        self.shopping_canvas.bind("<Configure>", self.on_shopping_canvas_configure)
        
        # Load shopping lists
        self.load_shopping_lists()
    
    def on_shopping_list_configure(self, event):
        """Handle shopping list inner frame configuration."""
        # Update the scrollregion to encompass the inner frame
        self.shopping_canvas.configure(scrollregion=self.shopping_canvas.bbox(tk.ALL))
    
    def on_shopping_canvas_configure(self, event):
        """Handle shopping canvas configuration."""
        # Update the width of the inner frame to fill the canvas
        self.shopping_canvas.itemconfig(self.shopping_canvas_window, width=event.width)
    
    def load_shopping_lists(self):
        """Load shopping lists into the list view."""
        # Clear existing items
        for widget in self.shopping_list_inner.winfo_children():
            widget.destroy()
        
        # Get shopping lists
        shopping_lists = self.db.get_shopping_lists()
        
        if not shopping_lists:
            # Show no lists message
            no_lists = ttk.Label(self.shopping_list_inner, text="No shopping lists found", style="ShoppingListItem.TLabel")
            no_lists.pack(fill=tk.X, padx=10, pady=10)
        else:
            # Add shopping list items
            for shopping_list in shopping_lists:
                self.create_shopping_list_item(shopping_list)
    
    def create_shopping_list_item(self, shopping_list):
        """Create a shopping list item widget."""
        # Create frame for shopping list item
        list_frame = ttk.Frame(self.shopping_list_inner, style="ShoppingListItem.TFrame")
        list_frame.pack(fill=tk.X, padx=2, pady=2)
        list_frame.bind("<Button-1>", lambda e, l=shopping_list: self.load_shopping_list_detail(l["id"]))
        
        # Create list item content
        name_label = ttk.Label(
            list_frame, 
            text=shopping_list["name"],
            style="ShoppingListItem.TLabel",
            font=("Arial", 11, "bold")
        )
        name_label.pack(anchor=tk.W, padx=5, pady=2)
        name_label.bind("<Button-1>", lambda e, l=shopping_list: self.load_shopping_list_detail(l["id"]))
        
        # Add date if available
        if shopping_list["date_created"]:
            try:
                date_obj = datetime.datetime.strptime(shopping_list["date_created"], "%Y-%m-%d %H:%M:%S")
                date_str = date_obj.strftime("%b %d, %Y")
            except:
                date_str = shopping_list["date_created"]
                
            date_label = ttk.Label(list_frame, text=date_str, style="ShoppingListItem.TLabel")
            date_label.pack(anchor=tk.W, padx=5)
            date_label.bind("<Button-1>", lambda e, l=shopping_list: self.load_shopping_list_detail(l["id"]))
        
        # Add notes if available
        if shopping_list["notes"]:
            notes = shopping_list["notes"]
            if len(notes) > 60:
                notes = notes[:57] + "..."
            notes_label = ttk.Label(list_frame, text=notes, style="ShoppingListItem.TLabel")
            notes_label.pack(anchor=tk.W, padx=5, pady=2)
            notes_label.bind("<Button-1>", lambda e, l=shopping_list: self.load_shopping_list_detail(l["id"]))
        
        # Add separator
        ttk.Separator(self.shopping_list_inner, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=3)
    
    def setup_shopping_detail(self):
        """Set up the shopping list detail part of the shopping tab."""
        # Create view for shopping list details
        self.shopping_view_frame = ttk.Frame(self.shopping_detail_frame, style="Recipe.TFrame")
        self.shopping_view_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initially show a welcome message in detail view
        welcome_label = ttk.Label(
            self.shopping_view_frame, 
            text="Shopping Lists",
            style="RecipeTitle.TLabel"
        )
        welcome_label.pack(pady=20)
        
        instruction_label = ttk.Label(
            self.shopping_view_frame,
            text="Select a shopping list from the left or create a new one.",
            style="Recipe.TLabel"
        )
        instruction_label.pack(pady=10)
    
    def new_shopping_list(self):
        """Create a new shopping list."""
        # Prompt for name
        name = simpledialog.askstring("New Shopping List", "Enter a name for the shopping list:")
        if not name:
            return
        
        # Create shopping list
        shopping_list_id = self.db.create_shopping_list(name)
        
        # Refresh lists and load the new one
        self.load_shopping_lists()
        self.load_shopping_list_detail(shopping_list_id)
    
    def generate_from_recipes(self):
        """Generate a shopping list from recipes."""
        # Create recipe selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Recipes")
        dialog.geometry("400x500")
        dialog.minsize(400, 400)
        dialog.grab_set()  # Make dialog modal
        
        # Create frame for recipe list
        recipe_frame = ttk.Frame(dialog)
        recipe_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create heading
        heading = ttk.Label(recipe_frame, text="Select Recipes for Shopping List", style="Heading.TLabel")
        heading.pack(pady=10)
        
        # Create listbox with scrollbar
        list_frame = ttk.Frame(recipe_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        recipe_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE)
        recipe_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=recipe_listbox.yview)
        
        recipe_listbox.configure(yscrollcommand=recipe_scrollbar.set)
        
        recipe_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        recipe_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Get all recipes
        recipes = self.db.get_all_recipes()
        
        # Populate listbox with recipes
        for recipe in recipes:
            recipe_listbox.insert(tk.END, recipe["name"])
        
        # Store recipe IDs for later
        recipe_ids = [recipe["id"] for recipe in recipes]
        
        # Name field
        name_frame = ttk.Frame(recipe_frame)
        name_frame.pack(fill=tk.X, pady=5)
        
        name_label = ttk.Label(name_frame, text="Shopping List Name:")
        name_label.pack(side=tk.LEFT, padx=5)
        
        name_var = tk.StringVar()
        name_var.set(f"Shopping List ({datetime.date.today().strftime('%Y-%m-%d')})")
        name_entry = ttk.Entry(name_frame, textvariable=name_var, width=30)
        name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Button frame
        btn_frame = ttk.Frame(recipe_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # Function to generate list and close dialog
        def create_list():
            selected_indices = recipe_listbox.curselection()
            
            if not selected_indices:
                messagebox.showwarning("No Recipes Selected", "Please select at least one recipe.")
                return
            
            selected_recipe_ids = [recipe_ids[idx] for idx in selected_indices]
            name = name_var.get().strip() or f"Shopping List ({datetime.date.today().strftime('%Y-%m-%d')})"
            
            shopping_list_id = self.db.generate_shopping_list_from_recipes(selected_recipe_ids, name)
            
            dialog.destroy()
            
            # Refresh lists and load the new one
            self.load_shopping_lists()
            self.load_shopping_list_detail(shopping_list_id)
        
        # Create generate button
        generate_btn = ttk.Button(btn_frame, text="Generate Shopping List", command=create_list)
        generate_btn.pack(side=tk.LEFT, padx=5)
        
        # Create cancel button
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def load_shopping_list_detail(self, shopping_list_id):
        """Load shopping list details into the detail view."""
        # Clear current view
        for widget in self.shopping_view_frame.winfo_children():
            widget.destroy()
        
        # Get shopping list details
        shopping_list = self.db.get_shopping_list(shopping_list_id)
        
        if not shopping_list:
            messagebox.showerror("Error", "Shopping list not found")
            return
        
        # Store current shopping list ID
        self.current_shopping_list_id = shopping_list_id
        
        # Create header frame
        header_frame = ttk.Frame(self.shopping_view_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Shopping list title
        title = ttk.Label(header_frame, text=shopping_list["name"], style="RecipeTitle.TLabel")
        title.pack(side=tk.LEFT, padx=5)
        
        # Actions frame on right
        actions_frame = ttk.Frame(header_frame)
        actions_frame.pack(side=tk.RIGHT, padx=5)
        
        # Print button
        print_btn = ttk.Button(actions_frame, text="Print", command=lambda: self.print_shopping_list(shopping_list_id))
        print_btn.pack(side=tk.LEFT, padx=2)
        
        # Delete button
        delete_btn = ttk.Button(actions_frame, text="Delete", command=lambda: self.delete_shopping_list(shopping_list_id))
        delete_btn.pack(side=tk.LEFT, padx=2)
        
        # Created date if available
        if shopping_list["date_created"]:
            try:
                date_obj = datetime.datetime.strptime(shopping_list["date_created"], "%Y-%m-%d %H:%M:%S")
                date_str = date_obj.strftime("%B %d, %Y")
            except:
                date_str = shopping_list["date_created"]
                
            date_label = ttk.Label(self.shopping_view_frame, text=f"Created: {date_str}", style="Recipe.TLabel")
            date_label.pack(anchor=tk.W, padx=10, pady=2)
        
        # Notes if available
        if shopping_list["notes"]:
            notes_label = ttk.Label(self.shopping_view_frame, text=f"Notes: {shopping_list['notes']}", style="Recipe.TLabel", wraplength=500)
            notes_label.pack(anchor=tk.W, padx=10, pady=2)
        
        # Create canvas for scrollable items list
        canvas = tk.Canvas(self.shopping_view_frame, borderwidth=0, background="#ffffff")
        scrollbar = ttk.Scrollbar(self.shopping_view_frame, orient=tk.VERTICAL, command=canvas.yview)
        
        inner_frame = ttk.Frame(canvas, style="ShoppingList.TFrame")
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor=tk.NW)
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox(tk.ALL))
            canvas.itemconfig(canvas_window, width=event.width)
        
        inner_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        
        # Group items by category
        categorized_items = {}
        
        for item in shopping_list["items"]:
            category = item["category"] or "Uncategorized"
            if category not in categorized_items:
                categorized_items[category] = []
            categorized_items[category].append(item)
        
        # Create items by category
        for category, items in categorized_items.items():
            # Category heading
            category_label = ttk.Label(inner_frame, text=category, style="ShoppingListSection.TLabel")
            category_label.pack(anchor=tk.W, padx=10, pady=5)
            
            # Add items
            for item in items:
                self.create_shopping_item_row(inner_frame, item)
            
            # Add separator after each category
            ttk.Separator(inner_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)
    
    def create_shopping_item_row(self, parent, item):
        """Create a shopping list item row."""
        row_frame = ttk.Frame(parent, style="ShoppingListItem.TFrame")
        row_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Checkbox
        checked_var = tk.BooleanVar(value=item["checked"])
        
        def update_checked():
            self.db.update_shopping_list_item(item["id"], checked=checked_var.get())
        
        check = ttk.Checkbutton(row_frame, variable=checked_var, command=update_checked)
        check.pack(side=tk.LEFT)
        
        # Item name with quantity and unit
        quantity_str = f"{item['quantity']} " if item["quantity"] else ""
        unit_str = f"{item['unit']} " if item["unit"] else ""
        
        item_text = f"{quantity_str}{unit_str}{item['name']}"
        if item["notes"]:
            item_text += f" ({item['notes']})"
        
        item_label = ttk.Label(row_frame, text=item_text, style="ShoppingListItem.TLabel")
        item_label.pack(side=tk.LEFT, padx=5)
    
    def print_shopping_list(self, shopping_list_id):
        """Print a shopping list."""
        # Get shopping list details
        shopping_list = self.db.get_shopping_list(shopping_list_id)
        
        if not shopping_list:
            messagebox.showerror("Error", "Shopping list not found")
            return
        
        # Create print dialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt")],
            initialfile=f"{shopping_list['name']}.txt"
        )
        
        if not filename:
            return
        
        # Generate text file
        try:
            with open(filename, 'w') as f:
                # Write header
                f.write(f"{shopping_list['name']}\n")
                f.write(f"Created: {shopping_list['date_created']}\n")
                if shopping_list["notes"]:
                    f.write(f"Notes: {shopping_list['notes']}\n")
                f.write("\n")
                
                # Group items by category
                categorized_items = {}
                
                for item in shopping_list["items"]:
                    category = item["category"] or "Uncategorized"
                    if category not in categorized_items:
                        categorized_items[category] = []
                    categorized_items[category].append(item)
                
                # Write items by category
                for category, items in categorized_items.items():
                    f.write(f"{category}\n")
                    f.write("-" * len(category) + "\n")
                    
                    for item in items:
                        # Format item
                        quantity_str = f"{item['quantity']} " if item["quantity"] else ""
                        unit_str = f"{item['unit']} " if item["unit"] else ""
                        
                        item_text = f"{quantity_str}{unit_str}{item['name']}"
                        if item["notes"]:
                            item_text += f" ({item['notes']})"
                        
                        # Add checkbox
                        checkbox = "[X]" if item["checked"] else "[ ]"
                        
                        f.write(f"{checkbox} {item_text}\n")
                    
                    f.write("\n")
            
            messagebox.showinfo("Success", f"Shopping list saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save shopping list: {str(e)}")
    
    def delete_shopping_list(self, shopping_list_id):
        """Delete a shopping list."""
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion", 
            "Are you sure you want to delete this shopping list? This cannot be undone."
        )
        
        if not confirm:
            return
        
        # Delete shopping list from database
        success = self.db.delete_shopping_list(shopping_list_id)
        
        if success:
            messagebox.showinfo("Success", "Shopping list deleted successfully!")
            # Clear current shopping list ID
            if hasattr(self, 'current_shopping_list_id'):
                delattr(self, 'current_shopping_list_id')
            
            # Clear shopping detail view
            for widget in self.shopping_view_frame.winfo_children():
                widget.destroy()
            
            # Show welcome message
            welcome_label = ttk.Label(
                self.shopping_view_frame, 
                text="Shopping Lists",
                style="RecipeTitle.TLabel"
            )
            welcome_label.pack(pady=20)
            
            instruction_label = ttk.Label(
                self.shopping_view_frame,
                text="Select a shopping list from the left or create a new one.",
                style="Recipe.TLabel"
            )
            instruction_label.pack(pady=10)
            
            # Refresh shopping lists
            self.load_shopping_lists()
        else:
            messagebox.showerror("Error", "Failed to delete shopping list.")
    
    def setup_import_export_tab(self):
        """Set up the import/export tab."""
        # Create main frame
        main_frame = ttk.Frame(self.import_export_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create heading
        heading = ttk.Label(main_frame, text="Import and Export Recipes", style="Heading.TLabel")
        heading.pack(pady=10)
        
        # Create import section
        import_frame = ttk.LabelFrame(main_frame, text="Import Recipe")
        import_frame.pack(fill=tk.X, pady=10)
        
        import_label = ttk.Label(import_frame, text="Import a recipe from a JSON file.")
        import_label.pack(padx=10, pady=5)
        
        import_btn = ttk.Button(import_frame, text="Import from File", command=self.import_recipe)
        import_btn.pack(padx=10, pady=10)
        
        # Create export section
        export_frame = ttk.LabelFrame(main_frame, text="Export Recipe")
        export_frame.pack(fill=tk.X, pady=10)
        
        export_label = ttk.Label(export_frame, text="Select a recipe to export to a JSON file.")
        export_label.pack(padx=10, pady=5)
        
        # Get all recipes
        recipes = self.db.get_all_recipes()
        recipe_names = [recipe["name"] for recipe in recipes]
        
        # Store recipe IDs for use in export
        self.export_recipe_ids = [recipe["id"] for recipe in recipes]
        
        # Recipe selection combobox
        self.export_recipe_var = tk.StringVar()
        export_combo = ttk.Combobox(export_frame, textvariable=self.export_recipe_var, 
                                  values=recipe_names, width=40, state="readonly")
        export_combo.pack(padx=10, pady=5)
        
        export_btn = ttk.Button(export_frame, text="Export to File", command=self.export_recipe)
        export_btn.pack(padx=10, pady=10)
        
        # Create backup section
        backup_frame = ttk.LabelFrame(main_frame, text="Database Backup")
        backup_frame.pack(fill=tk.X, pady=10)
        
        backup_label = ttk.Label(backup_frame, text="Backup or restore the entire recipe database.")
        backup_label.pack(padx=10, pady=5)
        
        backup_btn_frame = ttk.Frame(backup_frame)
        backup_btn_frame.pack(padx=10, pady=10)
        
        backup_db_btn = ttk.Button(backup_btn_frame, text="Backup Database", command=self.backup_database)
        backup_db_btn.pack(side=tk.LEFT, padx=5)
        
        restore_db_btn = ttk.Button(backup_btn_frame, text="Restore Database", command=self.restore_database)
        restore_db_btn.pack(side=tk.LEFT, padx=5)
    
    def import_recipe(self):
        """Import a recipe from a JSON file."""
        # Open file dialog
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            # Read the file
            with open(filename, 'r') as f:
                json_data = f.read()
            
            # Import recipe
            recipe_id = self.db.import_recipe_from_json(json_data)
            
            if recipe_id:
                messagebox.showinfo("Success", "Recipe imported successfully!")
                # Refresh recipe list
                self.load_recipe_list()
                # Load the new recipe
                self.load_recipe_detail(recipe_id)
                # Switch to recipes tab
                self.notebook.select(self.recipes_tab)
            else:
                messagebox.showerror("Error", "Failed to import recipe. Invalid format.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import recipe: {str(e)}")
    
    def export_recipe(self):
        """Export a recipe to a JSON file."""
        # Check if a recipe is selected
        recipe_name = self.export_recipe_var.get()
        if not recipe_name:
            messagebox.showwarning("No Recipe Selected", "Please select a recipe to export.")
            return
        
        # Get the recipe ID
        recipe_index = self.export_recipe_var.get()
        if recipe_index not in self.export_recipe_ids:
            for i, name in enumerate(self.export_recipe_var["values"]):
                if name == recipe_name:
                    recipe_id = self.export_recipe_ids[i]
                    break
            else:
                messagebox.showerror("Error", "Recipe not found.")
                return
        
        # Open file dialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"{recipe_name}.json"
        )
        
        if not filename:
            return
        
        # Export recipe
        json_data = self.db.export_recipe_to_json(recipe_id)
        
        if json_data:
            try:
                # Write to file
                with open(filename, 'w') as f:
                    f.write(json_data)
                
                messagebox.showinfo("Success", f"Recipe exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export recipe: {str(e)}")
        else:
            messagebox.showerror("Error", "Failed to export recipe.")
    
    def backup_database(self):
        """Backup the entire database to a file."""
        # Open file dialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")],
            initialfile=f"recipe_system_backup_{datetime.date.today().strftime('%Y%m%d')}.db"
        )
        
        if not filename:
            return
        
        try:
            # Close database connection
            self.db.close()
            
            # Copy database file
            import shutil
            shutil.copy2(self.db.db_path, filename)
            
            # Reopen database
            self.db = RecipeDatabase()
            
            messagebox.showinfo("Success", f"Database backed up to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to backup database: {str(e)}")
            # Ensure database is reopened even if error occurs
            self.db = RecipeDatabase()
    
    def restore_database(self):
        """Restore the database from a backup file."""
        # Confirm restoration
        confirm = messagebox.askyesno(
            "Confirm Restore", 
            "Restoring will replace your current database. This cannot be undone. Continue?"
        )
        
        if not confirm:
            return
        
        # Open file dialog
        filename = filedialog.askopenfilename(
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            # Close database connection
            self.db.close()
            
            # Copy backup to database file
            import shutil
            shutil.copy2(filename, self.db.db_path)
            
            # Reopen database
            self.db = RecipeDatabase()
            
            messagebox.showinfo("Success", "Database restored successfully!")
            
            # Refresh UI
            self.load_recipe_list()
            self.load_shopping_lists()
            
            # Clear detail views
            for widget in self.recipe_view_frame.winfo_children():
                widget.destroy()
                
            welcome_label = ttk.Label(
                self.recipe_view_frame, 
                text="Welcome to Recipe Organization System",
                style="RecipeTitle.TLabel"
            )
            welcome_label.pack(pady=20)
            
            for widget in self.shopping_view_frame.winfo_children():
                widget.destroy()
                
            shopping_welcome = ttk.Label(
                self.shopping_view_frame, 
                text="Shopping Lists",
                style="RecipeTitle.TLabel"
            )
            shopping_welcome.pack(pady=20)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore database: {str(e)}")
            # Ensure database is reopened even if error occurs
            self.db = RecipeDatabase()
    
    def run(self):
        """Run the application."""
        # Create widgets
        self.create_widgets()
        
        # Start main loop
        self.root.mainloop()
        
        # Close database when app closes
        self.db.close()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = RecipeApp(root)
    app.run()

if __name__ == "__main__":
    main()