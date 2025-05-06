"""
Simplified Recipe Organization System
A streamlined application for managing recipes and shopping lists.

Author: Cody Hinz
Date: May 5th, 2025
"""

import os
import sys
import sqlite3
import datetime
import customtkinter as ctk
from tkinter import messagebox, simpledialog
import tkinter.filedialog as filedialog
import tkinter as tk
from customtkinter import CTkScrollableFrame, CTkTextbox
import json

# Configure appearance mode and color theme
ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

class RecipeDatabase:
    """
    Handles all database operations for the Recipe Organization System.
    """
    
    def __init__(self, db_path='recipe_system.db'):
        """Initialize the database connection and create tables if they don't exist."""
        # Store the database path
        self.db_path = db_path
        
        # Connect to the database
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        self._create_tables()
    
    def _create_tables(self):
        """Create all necessary tables for the application if they don't already exist."""
        # Create recipes table (simplified)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            instructions TEXT,
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
        
        # Create ingredients table (simplified to just a string)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            id INTEGER PRIMARY KEY,
            recipe_id INTEGER,
            ingredient_text TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
        )
        ''')
        
        # Create shopping_lists table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS shopping_lists (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create shopping_list_items table (simplified)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS shopping_list_items (
            id INTEGER PRIMARY KEY,
            shopping_list_id INTEGER,
            item_text TEXT,
            checked BOOLEAN DEFAULT 0,
            FOREIGN KEY (shopping_list_id) REFERENCES shopping_lists (id) ON DELETE CASCADE
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
        
        # Commit changes
        self.conn.commit()
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    # Recipe CRUD operations
    def add_recipe(self, recipe_data):
        """Add a new recipe to the database."""
        # Extract recipe data
        name = recipe_data.get('name')
        instructions = recipe_data.get('instructions', '')
        favorite = 1 if recipe_data.get('favorite', False) else 0
        
        # Insert recipe into database
        self.cursor.execute('''
        INSERT INTO recipes (name, instructions, favorite)
        VALUES (?, ?, ?)
        ''', (name, instructions, favorite))
        
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
        
        # Add ingredients if provided
        if 'ingredients' in recipe_data and recipe_data['ingredients']:
            for ingredient_text in recipe_data['ingredients']:
                # Skip empty ingredients
                if not ingredient_text.strip():
                    continue
                
                # Add ingredient
                self.cursor.execute('''
                INSERT INTO recipe_ingredients (recipe_id, ingredient_text)
                VALUES (?, ?)
                ''', (recipe_id, ingredient_text.strip()))
        
        # Commit the transaction
        self.conn.commit()
        
        return recipe_id
    
    def get_recipe(self, recipe_id):
        """Retrieve a recipe by its ID."""
        # Get recipe basic information
        self.cursor.execute('''
        SELECT id, name, instructions, favorite, date_added
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
            'instructions': recipe_row[2],
            'favorite': bool(recipe_row[3]),
            'date_added': recipe_row[4],
            'ingredients': [],
            'categories': []
        }
        
        # Get ingredients
        self.cursor.execute('''
        SELECT ingredient_text
        FROM recipe_ingredients
        WHERE recipe_id = ?
        ''', (recipe_id,))
        
        ingredients_rows = self.cursor.fetchall()
        recipe['ingredients'] = [row[0] for row in ingredients_rows]
        
        # Get categories
        self.cursor.execute('''
        SELECT c.name
        FROM recipe_categories rc
        JOIN categories c ON rc.category_id = c.id
        WHERE rc.recipe_id = ?
        ''', (recipe_id,))
        
        categories_rows = self.cursor.fetchall()
        recipe['categories'] = [row[0] for row in categories_rows]
        
        return recipe
    
    def update_recipe(self, recipe_id, recipe_data):
        """Update an existing recipe."""
        # Check if recipe exists
        self.cursor.execute('SELECT id FROM recipes WHERE id = ?', (recipe_id,))
        if not self.cursor.fetchone():
            return False
        
        # Update recipe basic information
        self.cursor.execute('''
        UPDATE recipes SET
            name = ?,
            instructions = ?,
            favorite = ?
        WHERE id = ?
        ''', (
            recipe_data.get('name'),
            recipe_data.get('instructions', ''),
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
        
        # Update ingredients (delete all and reinsert)
        if 'ingredients' in recipe_data:
            # Remove existing ingredients
            self.cursor.execute('DELETE FROM recipe_ingredients WHERE recipe_id = ?', (recipe_id,))
            
            # Add new ingredients
            for ingredient_text in recipe_data['ingredients']:
                # Skip empty ingredients
                if not ingredient_text.strip():
                    continue
                
                # Add ingredient
                self.cursor.execute('''
                INSERT INTO recipe_ingredients (recipe_id, ingredient_text)
                VALUES (?, ?)
                ''', (recipe_id, ingredient_text.strip()))
        
        # Commit the transaction
        self.conn.commit()
        
        return True
    def delete_recipe(self, recipe_id):
        """Delete a recipe from the database."""
        # Check if recipe exists
        self.cursor.execute('SELECT id FROM recipes WHERE id = ?', (recipe_id,))
        if not self.cursor.fetchone():
            return False
        
        # Delete the recipe (foreign key constraints will handle related records)
        self.cursor.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
        
        # Commit the transaction
        self.conn.commit()
        
        return True
    
    def search_recipes(self, query=None, categories=None, favorite=None):
        """Search for recipes based on various criteria."""
        # Base query
        sql = '''
        SELECT DISTINCT r.id, r.name, r.favorite
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
        
        # Add text search condition - ONLY SEARCH RECIPE NAMES
        if query:
            conditions.append('r.name LIKE ?')
            search_term = f'%{query}%'
            params.append(search_term)
        
        # Add favorite condition
        if favorite:
            conditions.append('r.favorite = 1')
        
        # Add WHERE clause if there are conditions
        if conditions:
            sql += ' WHERE ' + ' AND '.join(conditions)
        
        # Add ORDER BY
        sql += ' ORDER BY r.name'
        
        # Execute the query
        self.cursor.execute(sql, params)
        
        # Process results
        recipes = []
        recipe_ids = set()  # To avoid duplicates from joins
        
        for row in self.cursor.fetchall():
            recipe_id = row[0]
            if recipe_id not in recipe_ids:
                recipe_ids.add(recipe_id)
                recipe = {
                    'id': recipe_id,
                    'name': row[1],
                    'favorite': bool(row[2])
                }
                recipes.append(recipe)
        
        return recipes
    
    def get_all_recipes(self):
        """Get all recipes in the database."""
        self.cursor.execute('''
        SELECT id, name, favorite
        FROM recipes
        ORDER BY name
        ''')
        
        recipes = []
        for row in self.cursor.fetchall():
            recipe = {
                'id': row[0],
                'name': row[1],
                'favorite': bool(row[2])
            }
            recipes.append(recipe)
        
        return recipes
    
    def get_all_categories(self):
        """Get all categories."""
        self.cursor.execute('SELECT name FROM categories ORDER BY name')
        return [row[0] for row in self.cursor.fetchall()]
    
    # Shopping list operations
    def create_shopping_list(self, name):
        """Create a new shopping list."""
        self.cursor.execute('''
        INSERT INTO shopping_lists (name)
        VALUES (?)
        ''', (name,))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def add_shopping_list_item(self, shopping_list_id, item_text):
        """Add an item to a shopping list."""
        self.cursor.execute('''
        INSERT INTO shopping_list_items (shopping_list_id, item_text)
        VALUES (?, ?)
        ''', (shopping_list_id, item_text))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_shopping_lists(self):
        """Get all shopping lists."""
        self.cursor.execute('''
        SELECT id, name, date_created
        FROM shopping_lists
        ORDER BY date_created DESC
        ''')
        
        shopping_lists = []
        for row in self.cursor.fetchall():
            shopping_list = {
                'id': row[0],
                'name': row[1],
                'date_created': row[2]
            }
            shopping_lists.append(shopping_list)
        
        return shopping_lists
    
    def get_shopping_list(self, shopping_list_id):
        """Get a shopping list by ID, including its items."""
        # Get shopping list info
        self.cursor.execute('''
        SELECT id, name, date_created
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
            'items': []
        }
        
        # Get shopping list items
        self.cursor.execute('''
        SELECT id, item_text, checked
        FROM shopping_list_items
        WHERE shopping_list_id = ?
        ORDER BY id
        ''', (shopping_list_id,))
        
        for row in self.cursor.fetchall():
            item = {
                'id': row[0],
                'item_text': row[1],
                'checked': bool(row[2])
            }
            shopping_list['items'].append(item)
        
        return shopping_list
    
    def update_shopping_list_item(self, item_id, checked=None, item_text=None):
        """Update a shopping list item."""
        # Prepare update fields
        update_fields = []
        params = []
        
        if checked is not None:
            update_fields.append('checked = ?')
            params.append(1 if checked else 0)
        
        if item_text is not None:
            update_fields.append('item_text = ?')
            params.append(item_text)
        
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
    
    def delete_shopping_list_item(self, item_id):
        """Delete a shopping list item."""
        self.cursor.execute('DELETE FROM shopping_list_items WHERE id = ?', (item_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def delete_shopping_list(self, shopping_list_id):
        """Delete a shopping list."""
        self.cursor.execute('DELETE FROM shopping_lists WHERE id = ?', (shopping_list_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def generate_shopping_list_from_recipes(self, recipe_ids, name=None):
        """Generate a shopping list from selected recipes."""
        # Create default name if not provided
        if not name:
            name = f"Shopping list ({datetime.date.today().strftime('%Y-%m-%d')})"
        
        # Create a new shopping list
        shopping_list_id = self.create_shopping_list(name)
        
        # If no recipes, return empty shopping list
        if not recipe_ids:
            return shopping_list_id
        
        # Get all ingredients from the selected recipes
        placeholders = ','.join(['?'] * len(recipe_ids))
        self.cursor.execute(f'''
        SELECT ingredient_text
        FROM recipe_ingredients
        WHERE recipe_id IN ({placeholders})
        ''', recipe_ids)
        
        # Add each ingredient as a shopping list item
        for row in self.cursor.fetchall():
            self.add_shopping_list_item(shopping_list_id, row[0])
        
        return shopping_list_id
    
    def export_recipe_to_json(self, recipe_id):
        """Export a recipe to JSON format."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return None
    
    # Return recipe data as a dictionary (ready for JSON conversion)
        return recipe

    def export_recipes_to_json(self, recipe_ids=None):
        """Export multiple recipes to JSON format."""
        if recipe_ids is None:
            # Get all recipes if no IDs provided
            recipes = self.get_all_recipes()
            recipe_ids = [recipe['id'] for recipe in recipes]
        
        result = []
        for recipe_id in recipe_ids:
            recipe = self.export_recipe_to_json(recipe_id)
            if recipe:
                result.append(recipe)
        
        return result

    def import_recipe_from_json(self, recipe_data):
        """Import a recipe from JSON data."""
        # Ensure required fields are present
        if 'name' not in recipe_data:
            return None
        
        # Extract recipe ID if present (for update vs. insert)
        recipe_id = recipe_data.get('id')
        
        # Check if recipe already exists
        if recipe_id:
            self.cursor.execute('SELECT id FROM recipes WHERE id = ?', (recipe_id,))
            if self.cursor.fetchone():
                # Update existing recipe
                return self.update_recipe(recipe_id, recipe_data)
        
        # Insert new recipe
        return self.add_recipe(recipe_data)

    def export_shopping_list_to_json(self, shopping_list_id):
        """Export a shopping list to JSON format."""
        shopping_list = self.get_shopping_list(shopping_list_id)
        if not shopping_list:
            return None
        
        # Return shopping list data as a dictionary (ready for JSON conversion)
        return shopping_list

    def export_shopping_lists_to_json(self, shopping_list_ids=None):
        """Export multiple shopping lists to JSON format."""
        if shopping_list_ids is None:
            # Get all shopping lists if no IDs provided
            shopping_lists = self.get_shopping_lists()
            shopping_list_ids = [sl['id'] for sl in shopping_lists]
        
        result = []
        for shopping_list_id in shopping_list_ids:
            shopping_list = self.export_shopping_list_to_json(shopping_list_id)
            if shopping_list:
                result.append(shopping_list)
        
        return result

    def import_shopping_list_from_json(self, shopping_list_data):
        """Import a shopping list from JSON data."""
        # Ensure required fields are present
        if 'name' not in shopping_list_data:
            return None
        
        # Extract shopping list ID if present (for update vs. insert)
        shopping_list_id = shopping_list_data.get('id')
        
        # Create new shopping list
        if not shopping_list_id or not self.get_shopping_list(shopping_list_id):
            shopping_list_id = self.create_shopping_list(shopping_list_data['name'])
        
        # Add items if present
        if 'items' in shopping_list_data and shopping_list_data['items']:
            for item in shopping_list_data['items']:
                # Skip if the item doesn't have text
                if 'item_text' not in item:
                    continue
                
                item_id = self.add_shopping_list_item(shopping_list_id, item['item_text'])
                
                # Update checked status if present
                if 'checked' in item and item_id:
                    self.update_shopping_list_item(item_id, checked=item['checked'])
        
        return shopping_list_id
    
class RecipeApp:
    """
    Main application class for the Recipe Organization System.
    Handles the GUI and interaction with the database.
    """
    
    def __init__(self, root):
        """Initialize the Recipe Organization System application."""
        self.root = root
        self.root.title("Recipe Organization System")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Initialize database
        self.db = RecipeDatabase()
        
        # Create main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_theme(self):
        """Set up the application theme and styling."""
        # Custom styling is handled by CustomTkinter through themes
        # Most styling is now applied directly to widgets
        pass
    
    def create_widgets(self):
        """Create all the widgets for the application."""
        # Create notebook for tabs
        self.notebook = ctk.CTkTabview(self.main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Create tabs
        self.recipes_tab = self.notebook.add("Recipes")
        self.shopping_tab = self.notebook.add("Shopping Lists")
        self.import_export_tab = self.notebook.add("Import/Export")
        
        # Set up import/export tab
        self.setup_import_export_tab()
        
        # Set up recipe tab
        self.setup_recipes_tab()
        
        # Set up shopping lists tab
        self.setup_shopping_tab()
        
        # Create status bar
        self.status_var = ctk.StringVar()
        self.status_bar = ctk.CTkLabel(
            self.root, 
            textvariable=self.status_var, 
            height=25,
            anchor="w", 
            fg_color=("gray85", "gray30"),  # Light mode, dark mode
            corner_radius=0
        )
        self.status_bar.pack(side="bottom", fill="x")
        self.status_var.set("Ready")


    def setup_recipes_tab(self):
        """Set up the recipes tab with list and detail views."""
        # Create splitview: recipe list on left, recipe detail on right
        # Use Frame instead of CTkPanedWindow
        self.recipe_frame = ctk.CTkFrame(self.recipes_tab)
        self.recipe_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create recipe list frame
        self.recipe_list_frame = ctk.CTkFrame(self.recipe_frame, width=300)
        self.recipe_list_frame.pack(side="left", fill="y", padx=5, pady=5)
        
        # Create recipe detail frame
        self.recipe_detail_frame = ctk.CTkFrame(self.recipe_frame)
        self.recipe_detail_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Set up recipe list section
        self.setup_recipe_list()
        
        # Set up recipe detail section
        self.setup_recipe_detail()
    
    def setup_recipe_list(self):
        """Set up the recipe list part of the recipes tab."""
        # Create recipe list frame header
        list_header = ctk.CTkFrame(self.recipe_list_frame)
        list_header.pack(fill="x", padx=10, pady=10)
        
        # Create heading
        heading = ctk.CTkLabel(
            list_header, 
            text="Recipes", 
            font=("Arial", 16, "bold")
        )
        heading.pack(side="left", padx=10)
        
        # Create search box
        search_frame = ctk.CTkFrame(list_header)
        search_frame.pack(side="right", padx=10, pady=5)
        
        search_label = ctk.CTkLabel(search_frame, text="Search:")
        search_label.pack(side="left", padx=5)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.search_recipes)
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=150)
        search_entry.pack(side="left", padx=5)
        
        # Create filter frame
        filter_frame = ctk.CTkFrame(self.recipe_list_frame)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        # Create category filter
        category_label = ctk.CTkLabel(filter_frame, text="Category:")
        category_label.pack(side="left", padx=5)
        
        self.category_var = ctk.StringVar(value="All")
        self.category_var.trace("w", self.search_recipes)
        
        # Get categories from database
        try:
            categories = ["All"] + self.db.get_all_categories()
        except:
            categories = ["All"]
            
        category_combo = ctk.CTkComboBox(
            filter_frame, 
            variable=self.category_var,
            values=categories,
            width=150
        )
        category_combo.pack(side="left", padx=5)
        
        # Create favorites checkbox
        self.favorite_var = ctk.BooleanVar()
        self.favorite_var.trace("w", self.search_recipes)
        favorite_check = ctk.CTkCheckBox(
            filter_frame, 
            text="Favorites",
            variable=self.favorite_var
        )
        favorite_check.pack(side="left", padx=10)
        
        # Add recipe button
        add_recipe_btn = ctk.CTkButton(
            self.recipe_list_frame, 
            text="Add New Recipe",
            command=self.new_recipe
        )
        add_recipe_btn.pack(fill="x", padx=10, pady=10)
        
        # Create scrollable frame for recipe list - replacing Canvas + Scrollbar setup
        self.recipe_list_scrollable = ctk.CTkScrollableFrame(
            self.recipe_list_frame,
            label_text="Available Recipes"
        )
        self.recipe_list_scrollable.pack(fill="both", expand=True, padx=10, pady=10)
        
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

    def load_recipe_list(self, recipes=None):
        """Load recipes into the recipe list."""
        # Clear existing items
        for widget in self.recipe_list_scrollable.winfo_children():
            widget.destroy()
        
        # If no recipes passed, get all recipes
        if recipes is None:
            search_term = self.search_var.get() if hasattr(self, 'search_var') else ""
            category = self.category_var.get() if hasattr(self, 'category_var') and self.category_var.get() != "All" else None
            favorite = self.favorite_var.get() if hasattr(self, 'favorite_var') and self.favorite_var.get() else None
            categories = [category] if category else None
            recipes = self.db.search_recipes(search_term, categories, favorite)
        
        if not recipes:
            # Show no recipes message - REPLACE ttk WITH ctk HERE
            no_recipes = ctk.CTkLabel(
                self.recipe_list_scrollable, 
                text="No recipes found",
                font=("Arial", 12)
            )
            no_recipes.pack(fill="x", padx=10, pady=10)
        else:
            # Add recipe items
            for recipe in recipes:
                self.create_recipe_list_item(recipe)
    
    # In the create_recipe_list_item method, add a tag to identify selected recipes:
    def create_recipe_list_item(self, recipe):
        # Create frame for recipe item with modern styling
        recipe_frame = ctk.CTkFrame(self.recipe_list_scrollable)
        recipe_frame.pack(fill="x", padx=5, pady=5)
        
        # Store the recipe ID in the frame for later reference
        recipe_frame.recipe_id = recipe["id"]
        
        # Use a lambda to bind click event to the whole frame
        recipe_frame.bind("<Button-1>", lambda e, r=recipe: self.select_recipe(r["id"], recipe_frame))
        
        # Create recipe item content with modern styling
        name_font = ("Arial", 14, "bold") if recipe["favorite"] else ("Arial", 14)
        
        name_label = ctk.CTkLabel(
            recipe_frame, 
            text=recipe["name"],
            font=name_font
        )
        name_label.pack(fill="x", padx=10, pady=5)
        name_label.bind("<Button-1>", lambda e, r=recipe: self.select_recipe(r["id"], recipe_frame))
        
        # Add favorite star if recipe is favorite
        if recipe["favorite"]:
            star_label = ctk.CTkLabel(
                recipe_frame,
                text="★",
                font=("Arial", 14),
                text_color=("gold", "gold")  # Same color for light/dark mode
            )
            star_label.place(relx=0.95, rely=0.5, anchor="e")
        
        # Add separator (thin frame instead of ttk.Separator)
        separator = ctk.CTkFrame(self.recipe_list_scrollable, height=1, fg_color=("gray80", "gray30"))
        separator.pack(fill="x", padx=10, pady=2)
    
    def select_recipe(self, recipe_id, selected_frame):
        """Handle recipe selection and highlighting."""
        # Load the recipe detail
        self.load_recipe_detail(recipe_id)
        
        # Remove highlight from all recipe frames
        for child in self.recipe_list_scrollable.winfo_children():
            if isinstance(child, ctk.CTkFrame) and hasattr(child, 'recipe_id'):
                child.configure(fg_color=("gray90", "gray20"))  # Reset to default color
        
        # Highlight the selected frame
        selected_frame.configure(fg_color=("lightblue", "navy"))  # Highlight color

    def setup_recipe_detail(self):
        """Set up the recipe detail part of the recipes tab."""
        # Create a frame for recipe editing form
        self.recipe_form_frame = ctk.CTkFrame(self.recipe_detail_frame)
        self.recipe_form_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Initially hide the form
        self.recipe_form_frame.pack_forget()
        
        # Create scrollable frame for recipe details
        self.recipe_view_frame = ctk.CTkScrollableFrame(
            self.recipe_detail_frame,
            label_text="Recipe Details"
        )
        self.recipe_view_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Initially show a welcome message in detail view
        welcome_label = ctk.CTkLabel(
            self.recipe_view_frame, 
            text="Welcome to Recipe Organization System",
            font=("Arial", 20, "bold")
        )
        welcome_label.pack(pady=20)
        
        instruction_label = ctk.CTkLabel(
            self.recipe_view_frame,
            text="Select a recipe from the list on the left or create a new recipe.",
            font=("Arial", 14)
        )
        instruction_label.pack(pady=10)
    
    def search_recipes(self, *args):
        """Handle recipe search and filtering."""
        # Get search parameters
        search_term = self.search_var.get() if hasattr(self, 'search_var') else ""
        category = self.category_var.get() if hasattr(self, 'category_var') and self.category_var.get() != "All" else None
        favorite = self.favorite_var.get() if hasattr(self, 'favorite_var') else None
        
        # Prepare filter parameters
        categories = [category] if category else None
        
        # Search for recipes
        recipes = self.db.search_recipes(search_term, categories, favorite)
        
        # Update the recipe list with the search results
        self.load_recipe_list(recipes)

    def load_recipe_list(self, recipes=None):
        """Load recipes into the recipe list."""
        # Clear existing items
        for widget in self.recipe_list_scrollable.winfo_children():
            widget.destroy()
        
        # If no recipes passed, get all recipes
        if recipes is None:
            search_term = self.search_var.get() if hasattr(self, 'search_var') else ""
            category = self.category_var.get() if hasattr(self, 'category_var') and self.category_var.get() != "All" else None
            favorite = self.favorite_var.get() if hasattr(self, 'favorite_var') and self.favorite_var.get() else None
            categories = [category] if category else None
            recipes = self.db.search_recipes(search_term, categories, favorite)
        
        if not recipes:
            # Show no recipes message
            no_recipes = ctk.CTkLabel(
                self.recipe_list_scrollable, 
                text="No recipes found",
                font=("Arial", 12)
            )
            no_recipes.pack(fill="x", padx=10, pady=10)
        else:
            # Add recipe items
            for recipe in recipes:
                self.create_recipe_list_item(recipe)

    def new_recipe(self):
        """Create a new recipe."""
        # Clear the recipe detail view
        for widget in self.recipe_view_frame.winfo_children():
            widget.destroy()
        
        # Hide recipe view and show recipe form
        self.recipe_view_frame.pack_forget()
        
        # Clear form frame and recreate as scrollable frame
        for widget in self.recipe_form_frame.winfo_children():
            widget.destroy()
        
        self.recipe_form_frame = ctk.CTkScrollableFrame(
            self.recipe_detail_frame,
            label_text="New Recipe"
        )
        self.recipe_form_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # IMPORTANT: Reset the ingredients list to empty
        self.ingredients = []

        # Create form header with large title
        heading = ctk.CTkLabel(
            self.recipe_form_frame, 
            text="New Recipe", 
            font=("Arial", 20, "bold")
        )
        heading.pack(pady=10)
        
        # Basic info section
        basic_frame = ctk.CTkFrame(self.recipe_form_frame)
        basic_frame.pack(fill="x", padx=10, pady=5)
        
        basic_label = ctk.CTkLabel(basic_frame, text="Basic Information", font=("Arial", 14, "bold"))
        basic_label.pack(anchor="w", padx=5, pady=5)
        
        # Name field
        name_frame = ctk.CTkFrame(basic_frame)
        name_frame.pack(fill="x", padx=5, pady=5)
        
        name_label = ctk.CTkLabel(name_frame, text="Recipe Name:")
        name_label.pack(side="left", padx=5)
        
        self.recipe_name_var = ctk.StringVar()
        name_entry = ctk.CTkEntry(name_frame, textvariable=self.recipe_name_var, width=300)
        name_entry.pack(side="left", padx=5)
        
        # Favorite checkbox
        self.recipe_favorite_var = ctk.BooleanVar()
        favorite_check = ctk.CTkCheckBox(name_frame, text="Favorite", variable=self.recipe_favorite_var)
        favorite_check.pack(side="left", padx=5)
        
        # Categories section
        cat_frame = ctk.CTkFrame(self.recipe_form_frame)
        cat_frame.pack(fill="x", padx=10, pady=10)
        
        cat_label = ctk.CTkLabel(cat_frame, text="Categories", font=("Arial", 14, "bold"))
        cat_label.pack(anchor="w", padx=5, pady=5)
        
        # Replace the tk.Listbox with a scrollable frame containing checkboxes
        self.categories_scrollable = ctk.CTkScrollableFrame(cat_frame, height=150)
        self.categories_scrollable.pack(fill="x", padx=5, pady=5)
        
        # Get all categories
        all_categories = self.db.get_all_categories()
        
        # Dictionary to store category checkbox variables
        self.category_vars = {}
        
        # Create a checkbox for each category
        for category in all_categories:
            var = ctk.BooleanVar(value=False)
            self.category_vars[category] = var
            checkbox = ctk.CTkCheckBox(self.categories_scrollable, text=category, variable=var)
            checkbox.pack(anchor="w", padx=5, pady=2)
        
        # Frame for the new category button
        cat_btn_frame = ctk.CTkFrame(cat_frame)
        cat_btn_frame.pack(fill="x", padx=5, pady=5)
        
        # New category button
        new_cat_btn = ctk.CTkButton(
            cat_btn_frame, 
            text="New Category", 
            command=self.add_new_category
        )
        new_cat_btn.pack(side="left", padx=5)
        
        # Ingredients section
        ingredients_frame = ctk.CTkFrame(self.recipe_form_frame)
        ingredients_frame.pack(fill="x", padx=10, pady=10)
        
        ing_label = ctk.CTkLabel(ingredients_frame, text="Ingredients", font=("Arial", 14, "bold"))
        ing_label.pack(anchor="w", padx=5, pady=5)
        
        # Ingredients list
        self.ingredients_list_frame = ctk.CTkFrame(ingredients_frame)
        self.ingredients_list_frame.pack(fill="x", padx=5, pady=5)
        
        # Ingredient list will be populated here
        self.ingredients = []  # Store ingredient data
        
        # Add ingredient button
        add_ing_btn = ctk.CTkButton(
            ingredients_frame, 
            text="Add Ingredient", 
            command=self.add_ingredient_row
        )
        add_ing_btn.pack(padx=5, pady=5)
        
        # Instructions section
        instr_frame = ctk.CTkFrame(self.recipe_form_frame)
        instr_frame.pack(fill="x", padx=10, pady=10)
        
        instr_label = ctk.CTkLabel(instr_frame, text="Instructions", font=("Arial", 14, "bold"))
        instr_label.pack(anchor="w", padx=5, pady=5)
        
        self.instructions_text = ctk.CTkTextbox(instr_frame, height=150, wrap="word")
        self.instructions_text.pack(fill="x", padx=5, pady=5)
        
        # Button frame
        btn_frame = ctk.CTkFrame(self.recipe_form_frame)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        # Save button
        save_btn = ctk.CTkButton(
            btn_frame, 
            text="Save Recipe", 
            command=self.save_new_recipe
        )
        save_btn.pack(side="left", padx=5)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            btn_frame, 
            text="Cancel", 
            command=self.cancel_recipe_edit
        )
        cancel_btn.pack(side="left", padx=5)
        
        # Add a single ingredient row to start
        self.add_ingredient_row()
    
    def add_ingredient_row(self):
        """Add a new ingredient row to the form."""
        row_frame = ctk.CTkFrame(self.ingredients_list_frame)
        row_frame.pack(fill="x", padx=5, pady=2)
        
        # Ingredient text field
        ingredient_var = ctk.StringVar()
        ingredient_entry = ctk.CTkEntry(row_frame, textvariable=ingredient_var, width=300)
        ingredient_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # Remove button
        def remove_ingredient():
            row_frame.destroy()
            self.ingredients.remove(ingredient_data)
        
        remove_btn = ctk.CTkButton(row_frame, text="X", width=30, command=remove_ingredient)
        remove_btn.pack(side="left", padx=2)
        
        # Store the ingredient data
        ingredient_data = {
            "row_frame": row_frame,
            "ingredient_var": ingredient_var
        }
        
        self.ingredients.append(ingredient_data)
        
        return ingredient_data
        
    def add_new_category(self):
        """Add a new category to the database."""
        new_category = simpledialog.askstring("New Category", "Enter new category name:")
        if new_category and new_category.strip():
            # Add to database
            self.db.cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (new_category,))
            self.db.conn.commit()
            
            # Add to UI as a checkbox
            var = ctk.BooleanVar(value=True)
            self.category_vars[new_category] = var
            checkbox = ctk.CTkCheckBox(self.categories_scrollable, text=new_category, variable=var)
            checkbox.pack(anchor="w", padx=5, pady=2)
    
    def save_new_recipe(self):
        """Save a new recipe to the database."""
        # Validate required fields
        if not self.recipe_name_var.get().strip():
            messagebox.showerror("Error", "Recipe name is required")
            return
        
        # Gather recipe data
        recipe_data = {
            "name": self.recipe_name_var.get().strip(),
            "instructions": self.instructions_text.get("1.0", tk.END).strip(),
            "favorite": self.recipe_favorite_var.get(),
            "categories": [cat for cat, var in self.category_vars.items() if var.get()],
            "ingredients": []
        }
        
        # Process ingredients
        for ingredient in self.ingredients:
            # Skip empty ingredients
            if not ingredient["ingredient_var"].get().strip():
                continue
                
            ingredient_text = ingredient["ingredient_var"].get().strip()
            recipe_data["ingredients"].append(ingredient_text)
        
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
        
        # Reset ingredients list
        self.ingredients = []
        
        # Show recipe view frame
        self.recipe_view_frame.pack(fill="both", expand=True)

        # If current recipe, reload it, otherwise show welcome message
        if hasattr(self, 'current_recipe_id'):
            self.load_recipe_detail(self.current_recipe_id)
        else:
            # Clear recipe view
            for widget in self.recipe_view_frame.winfo_children():
                widget.destroy()
            
            # Add welcome message
            welcome_label = ctk.CTkLabel(
                self.recipe_view_frame, 
                text="Welcome to Recipe Organization System",
                font=("Arial", 20, "bold")
            )
            welcome_label.pack(pady=20)
            
            instruction_label = ctk.CTkLabel(
                self.recipe_view_frame,
                text="Select a recipe from the list on the left or create a new recipe.",
                font=("Arial", 14)
            )
            instruction_label.pack(pady=10)

    def load_recipe_detail(self, recipe_id):
        """Load and display recipe details."""
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
        self.recipe_view_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Recipe header (for buttons)
        header_frame = ctk.CTkFrame(self.recipe_view_frame)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        # Title frame for recipe name
        title_frame = ctk.CTkFrame(self.recipe_view_frame)
        title_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        # Recipe title
        title_label = ctk.CTkLabel(
            title_frame, 
            text=recipe["name"],
            font=("Arial", 20, "bold")
        )
        title_label.pack(side="left", pady=5)
        
        # Star for favorite recipes
        if recipe["favorite"]:
            favorite_label = ctk.CTkLabel(
                title_frame,
                text="★",
                font=("Arial", 18),
                text_color=("gold", "gold")
            )
            favorite_label.pack(side="left", padx=5)
        
        # Button frame (now in the header_frame)
        btn_frame = ctk.CTkFrame(header_frame)
        btn_frame.pack(fill="x")
        
        # Edit button
        edit_btn = ctk.CTkButton(
            btn_frame, 
            text="Edit", 
            command=lambda: self.edit_recipe(recipe_id)
        )
        edit_btn.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        
        # Delete button
        delete_btn = ctk.CTkButton(
            btn_frame, 
            text="Delete", 
            command=lambda: self.delete_recipe(recipe_id)
        )
        delete_btn.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        
        # Add to shopping list button
        add_to_shopping_btn = ctk.CTkButton(
            btn_frame,
            text="Add to Shopping List",
            command=lambda: self.add_recipe_to_shopping_list(recipe_id)
        )
        add_to_shopping_btn.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        
        # Categories if available
        if recipe["categories"]:
            cat_frame = ctk.CTkFrame(self.recipe_view_frame)
            cat_frame.pack(fill="x", padx=10, pady=5)
            
            cat_label = ctk.CTkLabel(
                cat_frame,
                text="Categories: " + ", ".join(recipe["categories"]),
                font=("Arial", 12)
            )
            cat_label.pack(anchor="w")
        
        # Separator
        separator = ctk.CTkFrame(self.recipe_view_frame, height=1, fg_color=("gray80", "gray30"))
        separator.pack(fill="x", padx=10, pady=10)
        
        # Ingredients section
        if recipe["ingredients"]:
            ing_frame = ctk.CTkFrame(self.recipe_view_frame)
            ing_frame.pack(fill="x", padx=10, pady=5)
            
            ing_title = ctk.CTkLabel(ing_frame, text="Ingredients", font=("Arial", 16, "bold"))
            ing_title.pack(anchor="w", padx=10, pady=5)
            
            for ingredient in recipe["ingredients"]:
                ing_label = ctk.CTkLabel(
                    ing_frame,
                    text=ingredient,
                    anchor="w"
                )
                ing_label.pack(fill="x", padx=10, pady=2)
        
        # Instructions section
        if recipe["instructions"]:
            instr_frame = ctk.CTkFrame(self.recipe_view_frame)
            instr_frame.pack(fill="x", padx=10, pady=5)
            
            instr_title = ctk.CTkLabel(instr_frame, text="Instructions", font=("Arial", 16, "bold"))
            instr_title.pack(anchor="w", padx=10, pady=5)
            
            instr_text = ctk.CTkLabel(
                instr_frame,
                text=recipe["instructions"],
                wraplength=600,
                justify="left"
            )
            instr_text.pack(fill="x", padx=10, pady=5)
    
    def edit_recipe(self, recipe_id):
        """Edit an existing recipe."""
        # Get recipe data
        recipe = self.db.get_recipe(recipe_id)
        
        if not recipe:
            messagebox.showerror("Error", "Recipe not found")
            return
        
        # Clear the recipe detail view
        for widget in self.recipe_view_frame.winfo_children():
            widget.destroy()
        
        # Hide recipe view and show recipe form frame
        self.recipe_view_frame.pack_forget()
        
        # Clear form frame and recreate as scrollable frame
        for widget in self.recipe_form_frame.winfo_children():
            widget.destroy()
        
        self.recipe_form_frame = ctk.CTkScrollableFrame(
            self.recipe_detail_frame,
            label_text=f"Edit Recipe: {recipe['name']}"
        )
        self.recipe_form_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # IMPORTANT: Reset the ingredients list to empty
        self.ingredients = []
        
        # Create form header with large title
        heading = ctk.CTkLabel(
            self.recipe_form_frame, 
            text=f"Edit Recipe: {recipe['name']}", 
            font=("Arial", 20, "bold")
        )
        heading.pack(pady=10)
        
        # Basic info section
        basic_frame = ctk.CTkFrame(self.recipe_form_frame)
        basic_frame.pack(fill="x", padx=10, pady=5)
        
        basic_label = ctk.CTkLabel(basic_frame, text="Basic Information", font=("Arial", 14, "bold"))
        basic_label.pack(anchor="w", padx=5, pady=5)
        
        # Name field
        name_frame = ctk.CTkFrame(basic_frame)
        name_frame.pack(fill="x", padx=5, pady=5)
        
        name_label = ctk.CTkLabel(name_frame, text="Recipe Name:")
        name_label.pack(side="left", padx=5)
        
        self.recipe_name_var = ctk.StringVar(value=recipe["name"])
        name_entry = ctk.CTkEntry(name_frame, textvariable=self.recipe_name_var, width=300)
        name_entry.pack(side="left", padx=5)
        
        # Favorite checkbox
        self.recipe_favorite_var = ctk.BooleanVar(value=recipe["favorite"])
        favorite_check = ctk.CTkCheckBox(name_frame, text="Favorite", variable=self.recipe_favorite_var)
        favorite_check.pack(side="left", padx=5)
        
        # Categories section
        cat_frame = ctk.CTkFrame(self.recipe_form_frame)
        cat_frame.pack(fill="x", padx=10, pady=10)
        
        cat_label = ctk.CTkLabel(cat_frame, text="Categories", font=("Arial", 14, "bold"))
        cat_label.pack(anchor="w", padx=5, pady=5)
        
        # Replace the tk.Listbox with a scrollable frame containing checkboxes
        self.categories_scrollable = ctk.CTkScrollableFrame(cat_frame, height=150)
        self.categories_scrollable.pack(fill="x", padx=5, pady=5)
        
        # Get all categories
        all_categories = self.db.get_all_categories()
        
        # Dictionary to store category checkbox variables
        self.category_vars = {}
        
        # Create a checkbox for each category, check those that belong to the recipe
        for category in all_categories:
            var = ctk.BooleanVar(value=category in recipe["categories"])
            self.category_vars[category] = var
            checkbox = ctk.CTkCheckBox(self.categories_scrollable, text=category, variable=var)
            checkbox.pack(anchor="w", padx=5, pady=2)
        
        # New category button
        new_cat_btn = ctk.CTkButton(
            cat_selection_frame, 
            text="New Category", 
            command=self.add_new_category
        )
        new_cat_btn.pack(side="left", padx=5)
        
        # Ingredients section
        ingredients_frame = ctk.CTkFrame(self.recipe_form_frame)
        ingredients_frame.pack(fill="x", padx=10, pady=10)
        
        ing_label = ctk.CTkLabel(ingredients_frame, text="Ingredients", font=("Arial", 14, "bold"))
        ing_label.pack(anchor="w", padx=5, pady=5)
        
        # Ingredients list
        self.ingredients_list_frame = ctk.CTkFrame(ingredients_frame)
        self.ingredients_list_frame.pack(fill="x", padx=5, pady=5)
        
        # Add existing ingredients
        for ingredient_text in recipe["ingredients"]:
            self.add_ingredient_row_with_text(ingredient_text)
        
        # Add ingredient button
        add_ing_btn = ctk.CTkButton(
            ingredients_frame, 
            text="Add Ingredient", 
            command=self.add_ingredient_row
        )
        add_ing_btn.pack(padx=5, pady=5)
        
        # Instructions section
        instr_frame = ctk.CTkFrame(self.recipe_form_frame)
        instr_frame.pack(fill="x", padx=10, pady=10)
        
        instr_label = ctk.CTkLabel(instr_frame, text="Instructions", font=("Arial", 14, "bold"))
        instr_label.pack(anchor="w", padx=5, pady=5)
        
        self.instructions_text = ctk.CTkTextbox(instr_frame, height=150, wrap="word")
        self.instructions_text.pack(fill="x", padx=5, pady=5)
        self.instructions_text.insert("1.0", recipe["instructions"])
        
        # Button frame
        btn_frame = ctk.CTkFrame(self.recipe_form_frame)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        # Save button
        save_btn = ctk.CTkButton(
            btn_frame, 
            text="Save Changes", 
            command=lambda: self.save_recipe_changes(recipe_id)
        )
        save_btn.pack(side="left", padx=5)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            btn_frame, 
            text="Cancel", 
            command=self.cancel_recipe_edit
        )
        cancel_btn.pack(side="left", padx=5)
    
    def add_ingredient_row_with_text(self, ingredient_text):
        """Add a new ingredient row with provided text."""
        row_frame = ctk.CTkFrame(self.ingredients_list_frame)
        row_frame.pack(fill="x", padx=5, pady=2)
        
        # Ingredient text field
        ingredient_var = ctk.StringVar(value=ingredient_text)
        ingredient_entry = ctk.CTkEntry(row_frame, textvariable=ingredient_var, width=300)
        ingredient_entry.pack(side="left", padx=2, fill="x", expand=True)
        
        # Remove button
        def remove_ingredient():
            row_frame.destroy()
            self.ingredients.remove(ingredient_data)
        
        remove_btn = ctk.CTkButton(row_frame, text="X", width=30, command=remove_ingredient)
        remove_btn.pack(side="left", padx=2)
        
        # Store the ingredient data
        ingredient_data = {
            "row_frame": row_frame,
            "ingredient_var": ingredient_var
        }
        
        self.ingredients.append(ingredient_data)
        
        return ingredient_data
    
    def save_recipe_changes(self, recipe_id):
        """Save changes to an existing recipe."""
        # Validate required fields
        if not self.recipe_name_var.get().strip():
            messagebox.showerror("Error", "Recipe name is required")
            return
        
        # Gather recipe data
        recipe_data = {
            "name": self.recipe_name_var.get().strip(),
            "instructions": self.instructions_text.get("1.0", "end-1c").strip(),
            "favorite": self.recipe_favorite_var.get(),
            "categories": [self.cat_listbox.get(idx) for idx in self.cat_listbox.curselection()],
            "ingredients": []
        }
        
        # Process ingredients
        for ingredient in self.ingredients:
            # Skip empty ingredients
            if not ingredient["ingredient_var"].get().strip():
                continue
                
            ingredient_text = ingredient["ingredient_var"].get().strip()
            recipe_data["ingredients"].append(ingredient_text)
        
        # Update recipe in database
        success = self.db.update_recipe(recipe_id, recipe_data)
        
        if success:
            messagebox.showinfo("Success", "Recipe updated successfully!")
            # Reset ingredients list after successful save
            self.ingredients = []
            # Load the recipe detail view
            self.load_recipe_detail(recipe_id)
            # Refresh recipe list
            self.load_recipe_list()
        else:
            messagebox.showerror("Error", "Failed to update recipe")

    def save_new_recipe(self):
        """Save a new recipe to the database."""
        # Validate required fields
        if not self.recipe_name_var.get().strip():
            messagebox.showerror("Error", "Recipe name is required")
            return
        
        # Gather recipe data
        recipe_data = {
            "name": self.recipe_name_var.get().strip(),
            "instructions": self.instructions_text.get("1.0", tk.END).strip(),
            "favorite": self.recipe_favorite_var.get(),
            "categories": [self.cat_listbox.get(idx) for idx in self.cat_listbox.curselection()],
            "ingredients": []
        }
        
        # Process ingredients
        for ingredient in self.ingredients:
            # Skip empty ingredients
            if not ingredient["ingredient_var"].get().strip():
                continue
                
            ingredient_text = ingredient["ingredient_var"].get().strip()
            recipe_data["ingredients"].append(ingredient_text)
        
        # Add recipe to database
        recipe_id = self.db.add_recipe(recipe_data)
        
        if recipe_id:
            messagebox.showinfo("Success", "Recipe added successfully!")
            # Reset ingredients list after successful save
            self.ingredients = []
            # Load the recipe detail view
            self.load_recipe_detail(recipe_id)
            # Refresh recipe list
            self.load_recipe_list()
        else:
            messagebox.showerror("Error", "Failed to add recipe")
    
    def delete_recipe(self, recipe_id):
        """Delete a recipe."""
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
            
            # Reset ingredients list
            self.ingredients = []
            
            # Show welcome message
            welcome_label = ctk.CTkLabel(
                self.recipe_view_frame, 
                text="Welcome to Recipe Organization System",
                font=("Arial", 20, "bold")
            )
            welcome_label.pack(pady=20)
            
            instruction_label = ctk.CTkLabel(
                self.recipe_view_frame,
                text="Select a recipe from the list on the left or create a new recipe.",
                font=("Arial", 14)
            )
            instruction_label.pack(pady=10)
            
            # Refresh recipe list
            self.load_recipe_list()
        else:
            messagebox.showerror("Error", "Failed to delete recipe.")
    
    def add_recipe_to_shopping_list(self, recipe_id):
        """Add a recipe's ingredients to a shopping list."""
        import tkinter as tk
        
        # Get recipe data
        recipe = self.db.get_recipe(recipe_id)
        
        if not recipe:
            messagebox.showerror("Error", "Recipe not found")
            return
        
        # Get existing shopping lists
        existing_lists = self.db.get_shopping_lists()
        
        # Create options: create new list or add to existing
        options = ["Create new shopping list"]
        
        # Add existing lists as options if there are any
        if existing_lists:
            options.append("Add to existing shopping list")
            for shopping_list in existing_lists:
                options.append(f"Add to: {shopping_list['name']}")
        
        # Create a dialog with customtkinter
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add to Shopping List")
        dialog.geometry("400x300")
        dialog.minsize(300, 200)
        dialog.grab_set()  # Make dialog modal
        
        # Create frame
        frame = ctk.CTkFrame(dialog, fg_color=("gray95", "gray15"))
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Label
        label = ctk.CTkLabel(frame, text="Choose an option:", font=("Arial", 12))
        label.pack(pady=5)
        
        # Listbox with scrollbar - using regular tkinter Listbox
        listbox_frame = ctk.CTkFrame(frame)
        listbox_frame.pack(fill="both", expand=True, pady=5)
        
        listbox = tk.Listbox(listbox_frame)
        scrollbar = ctk.CTkScrollbar(listbox_frame, command=listbox.yview)
        
        listbox.configure(yscrollcommand=scrollbar.set)
        
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate options
        for option in options:
            listbox.insert("end", option)
        
        # Select first option by default
        listbox.selection_set(0)
        
        # Result variable
        result = [None]  # Use a list so it can be modified from inside the function
        
        # Function to handle option selection
        def on_ok():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("No Selection", "Please select an option.")
                return
            
            result[0] = options[selected_indices[0]]
            dialog.destroy()
        
        # Button frame
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill="x", pady=10)
        
        # OK button
        ok_btn = ctk.CTkButton(btn_frame, text="OK", command=on_ok)
        ok_btn.pack(side="left", padx=5)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            btn_frame, 
            text="Cancel", 
            command=dialog.destroy,
            fg_color="gray40",
            hover_color="gray30"
        )
        cancel_btn.pack(side="left", padx=5)
        
        # Wait for dialog to close
        dialog.wait_window()
        
        # If no selection, return
        if result[0] is None:
            return
        
        choice = result[0]
        
        if choice == "Create new shopping list":
            # Create new shopping list
            list_name = simpledialog.askstring(
                "New Shopping List",
                "Enter a name for the new shopping list:",
                initialvalue=f"{recipe['name']} ingredients"
            )
            
            if not list_name:
                return
            
            shopping_list_id = self.db.create_shopping_list(list_name)
            
            # Add ingredients
            for ingredient in recipe["ingredients"]:
                self.db.add_shopping_list_item(shopping_list_id, ingredient)
            
            messagebox.showinfo("Success", f"Created new shopping list: {list_name}")
            
        elif choice == "Add to existing shopping list":
            # Create another dialog to select the shopping list
            list_dialog = ctk.CTkToplevel(self.root)
            list_dialog.title("Select Shopping List")
            list_dialog.geometry("400x300")
            list_dialog.minsize(300, 200)
            list_dialog.grab_set()  # Make dialog modal
            
            # Create frame
            list_frame = ctk.CTkFrame(list_dialog)
            list_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Label
            list_label = ctk.CTkLabel(list_frame, text="Choose a shopping list:")
            list_label.pack(pady=5)
            
            # Listbox with scrollbar
            list_listbox_frame = ctk.CTkFrame(list_frame)
            list_listbox_frame.pack(fill="both", expand=True, pady=5)
            
            list_listbox = tk.Listbox(list_listbox_frame)
            list_scrollbar = ctk.CTkScrollbar(list_listbox_frame, command=list_listbox.yview)
            
            list_listbox.configure(yscrollcommand=list_scrollbar.set)
            
            list_listbox.pack(side="left", fill="both", expand=True)
            list_scrollbar.pack(side="right", fill="y")
            
            # Populate options
            for shopping_list in existing_lists:
                list_listbox.insert("end", shopping_list["name"])
            
            # Select first option by default
            if existing_lists:
                list_listbox.selection_set(0)
            
            # Result variable
            list_result = [None]  # Use a list so it can be modified from inside function
            
            # Function to handle list selection
            def on_list_ok():
                selected_indices = list_listbox.curselection()
                if not selected_indices:
                    messagebox.showwarning("No Selection", "Please select a shopping list.")
                    return
                
                list_result[0] = selected_indices[0]
                list_dialog.destroy()
            
            # Button frame
            list_btn_frame = ctk.CTkFrame(list_frame)
            list_btn_frame.pack(fill="x", pady=10)
            
            # OK button
            list_ok_btn = ctk.CTkButton(list_btn_frame, text="OK", command=on_list_ok)
            list_ok_btn.pack(side="left", padx=5)
            
            # Cancel button
            list_cancel_btn = ctk.CTkButton(
                list_btn_frame, 
                text="Cancel", 
                command=list_dialog.destroy,
                fg_color="gray40",
                hover_color="gray30"
            )
            list_cancel_btn.pack(side="left", padx=5)
            
            # Wait for dialog to close
            list_dialog.wait_window()
            
            # If no selection, return
            if list_result[0] is None:
                return
            
            # Get selected shopping list
            selected_index = list_result[0]
            selected_list = existing_lists[selected_index]
            shopping_list_id = selected_list["id"]
            
            # Add ingredients
            for ingredient in recipe["ingredients"]:
                self.db.add_shopping_list_item(shopping_list_id, ingredient)
            
            messagebox.showinfo("Success", f"Added ingredients to: {selected_list['name']}")
        
        elif choice.startswith("Add to: "):
            # Extract list name and find matching shopping list
            list_name = choice[8:]  # Remove "Add to: " prefix
            
            # Find the shopping list with matching name
            shopping_list_id = None
            for sl in existing_lists:
                if sl["name"] == list_name:
                    shopping_list_id = sl["id"]
                    break
            
            if not shopping_list_id:
                # Debug information
                print(f"Looking for list: '{list_name}'")
                print("Available lists:")
                for sl in existing_lists:
                    print(f"  '{sl['name']}'")
                    
                messagebox.showerror("Error", "Shopping list not found")
                return
            
            # Add ingredients
            for ingredient in recipe["ingredients"]:
                self.db.add_shopping_list_item(shopping_list_id, ingredient)
            
            messagebox.showinfo("Success", f"Added ingredients to: {list_name}")
        
        # Refresh shopping lists
        self.load_shopping_lists()
        
        # Switch to shopping lists tab
        self.notebook.set("Shopping Lists")

    def setup_shopping_tab(self):
        """Set up the shopping lists tab."""
        # Create splitview: list on left, detail on right
        self.shopping_frame = ctk.CTkFrame(self.shopping_tab)
        self.shopping_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create shopping list frame
        self.shopping_list_frame = ctk.CTkFrame(self.shopping_frame, width=300)
        self.shopping_list_frame.pack(side="left", fill="y", padx=5, pady=5)
        
        # Create shopping detail frame
        self.shopping_detail_frame = ctk.CTkFrame(self.shopping_frame)
        self.shopping_detail_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Set up shopping list section
        self.setup_shopping_list()
        
        # Set up shopping detail section
        self.setup_shopping_detail()

    def setup_shopping_list(self):
        """Set up the shopping list part of the shopping tab."""
        # Create list frame header
        list_header = ctk.CTkFrame(self.shopping_list_frame)
        list_header.pack(fill="x", padx=5, pady=5)
        
        # Create heading
        heading = ctk.CTkLabel(
            list_header, 
            text="Shopping Lists", 
            font=("Arial", 16, "bold")
        )
        heading.pack(side="left", padx=5)
        
        # Create shopping list buttons
        btn_frame = ctk.CTkFrame(self.shopping_list_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        # New shopping list button
        new_list_btn = ctk.CTkButton(
            btn_frame, 
            text="New Shopping List", 
            command=self.new_shopping_list
        )
        new_list_btn.pack(side="left", padx=5)
        
        # Generate from recipes button
        gen_list_btn = ctk.CTkButton(
            btn_frame, 
            text="Generate from Recipes", 
            command=self.generate_from_recipes
        )
        gen_list_btn.pack(side="left", padx=5)
        
        # Create scrollable frame for shopping lists instead of canvas
        self.shopping_lists_scrollable = ctk.CTkScrollableFrame(
            self.shopping_list_frame,
            label_text="Your Shopping Lists"
        )
        self.shopping_lists_scrollable.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Load shopping lists
        self.load_shopping_lists()

    def load_shopping_lists(self):
        """Load shopping lists into the list view."""
        # Clear existing items
        for widget in self.shopping_lists_scrollable.winfo_children():
            widget.destroy()
        
        # Get shopping lists
        shopping_lists = self.db.get_shopping_lists()
        
        if not shopping_lists:
            # Show no lists message
            no_lists = ctk.CTkLabel(
                self.shopping_lists_scrollable, 
                text="No shopping lists found",
                font=("Arial", 12)
            )
            no_lists.pack(fill="x", padx=10, pady=10)
        else:
            # Add shopping list items
            for shopping_list in shopping_lists:
                self.create_shopping_list_item(shopping_list)

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

    def create_shopping_list_item(self, shopping_list):
        # Create frame for shopping list item
        list_frame = ctk.CTkFrame(self.shopping_lists_scrollable)
        list_frame.pack(fill="x", padx=5, pady=5)
        list_frame.shopping_list_id = shopping_list["id"]
        list_frame.bind("<Button-1>", lambda e, l=shopping_list: self.select_shopping_list(l["id"], list_frame))
        
        # Create list item content
        name_label = ctk.CTkLabel(
            list_frame, 
            text=shopping_list["name"],
            font=("Arial", 14, "bold")
        )
        name_label.pack(anchor="w", padx=5, pady=2)
        name_label.bind("<Button-1>", lambda e, l=shopping_list: self.select_shopping_list(l["id"], list_frame))
    
        
        # Add date if available
        if shopping_list["date_created"]:
            try:
                date_obj = datetime.datetime.strptime(shopping_list["date_created"], "%Y-%m-%d %H:%M:%S")
                date_str = date_obj.strftime("%b %d, %Y")
            except:
                date_str = shopping_list["date_created"]
                
            date_label = ctk.CTkLabel(
                list_frame, 
                text=date_str,
                text_color=("gray50", "gray70")  # Subdued color
            )
            date_label.pack(anchor="w", padx=5)
            date_label.bind("<Button-1>", lambda e, l=shopping_list: self.load_shopping_list_detail(l["id"]))
        
        # Add separator
        separator = ctk.CTkFrame(self.shopping_lists_scrollable, height=1, fg_color=("gray80", "gray30"))
        separator.pack(fill="x", padx=10, pady=2)
    
    def select_shopping_list(self, shopping_list_id, selected_frame):
        """Handle shopping list selection and highlighting."""
        # Load the shopping list detail
        self.load_shopping_list_detail(shopping_list_id)
        
        # Remove highlight from all shopping list frames
        for child in self.shopping_lists_scrollable.winfo_children():
            if isinstance(child, ctk.CTkFrame) and hasattr(child, 'shopping_list_id'):
                child.configure(fg_color=("gray90", "gray20"))  # Reset to default color
        
        # Highlight the selected frame
        selected_frame.configure(fg_color=("lightblue", "navy"))  # Highlight color

    def setup_shopping_detail(self):
        """Set up the shopping list detail part of the shopping tab."""
        # Create view for shopping list details
        self.shopping_view_frame = ctk.CTkScrollableFrame(
            self.shopping_detail_frame,
            label_text="Shopping List Details"
        )
        self.shopping_view_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Initially show a welcome message in detail view
        welcome_label = ctk.CTkLabel(
            self.shopping_view_frame, 
            text="Shopping Lists",
            font=("Arial", 20, "bold")
        )
        welcome_label.pack(pady=20)
        
        instruction_label = ctk.CTkLabel(
            self.shopping_view_frame,
            text="Select a shopping list from the left or create a new one.",
            font=("Arial", 14)
        )
        instruction_label.pack(pady=10)

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
        header_frame = ctk.CTkFrame(self.shopping_view_frame)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        # Shopping list title
        title = ctk.CTkLabel(
            header_frame, 
            text=shopping_list["name"], 
            font=("Arial", 18, "bold")
        )
        title.pack(side="left", padx=5)
        
        # Actions frame on right
        actions_frame = ctk.CTkFrame(header_frame)
        actions_frame.pack(side="right", padx=5)
        
        # Add item button
        add_item_btn = ctk.CTkButton(
            actions_frame, 
            text="Add Item", 
            command=lambda: self.add_shopping_list_item(shopping_list_id)
        )
        add_item_btn.pack(side="left", padx=2)
        
        # Delete button
        delete_btn = ctk.CTkButton(
            actions_frame, 
            text="Delete List", 
            command=lambda: self.delete_shopping_list(shopping_list_id),
            fg_color="darkred",
            hover_color="red"
        )
        delete_btn.pack(side="left", padx=2)
        
        # Created date if available
        if shopping_list["date_created"]:
            try:
                date_obj = datetime.datetime.strptime(shopping_list["date_created"], "%Y-%m-%d %H:%M:%S")
                date_str = date_obj.strftime("%B %d, %Y")
            except:
                date_str = shopping_list["date_created"]
                
            date_label = ctk.CTkLabel(
                self.shopping_view_frame, 
                text=f"Created: {date_str}",
                text_color=("gray50", "gray70")
            )
            date_label.pack(anchor="w", padx=10, pady=2)
        
        # Create items container
        items_frame = ctk.CTkFrame(self.shopping_view_frame)
        items_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add items
        if not shopping_list["items"]:
            no_items = ctk.CTkLabel(
                items_frame, 
                text="No items in this shopping list",
                font=("Arial", 12)
            )
            no_items.pack(fill="x", padx=10, pady=10)
        else:
            for item in shopping_list["items"]:
                self.create_shopping_item_row(items_frame, item)

    def create_shopping_item_row(self, parent, item):
        """Create a shopping list item row."""
        row_frame = ctk.CTkFrame(parent)
        row_frame.pack(fill="x", padx=5, pady=2)
        
        # Checkbox
        checked_var = ctk.BooleanVar(value=item["checked"])
        
        def update_checked():
            self.db.update_shopping_list_item(item["id"], checked=checked_var.get())
        
        check = ctk.CTkCheckBox(
            row_frame, 
            text="",
            variable=checked_var, 
            command=update_checked
        )
        check.pack(side="left")
        
        # Item text (editable)
        item_var = ctk.StringVar(value=item["item_text"])
        item_entry = ctk.CTkEntry(
            row_frame, 
            textvariable=item_var, 
            width=300
        )
        item_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Update function for the entry
        def update_item_text(event=None):
            new_text = item_var.get().strip()
            if new_text:
                self.db.update_shopping_list_item(item["id"], item_text=new_text)
        
        # Bind update to Return key and focus out event
        item_entry.bind("<Return>", update_item_text)
        item_entry.bind("<FocusOut>", update_item_text)
        
        # Delete button
        def delete_item():
            self.db.delete_shopping_list_item(item["id"])
            row_frame.destroy()
        
        delete_btn = ctk.CTkButton(
            row_frame, 
            text="X", 
            width=30,
            command=delete_item,
            fg_color="darkred",
            hover_color="red"
        )
        delete_btn.pack(side="left", padx=2)

    def add_shopping_list_item(self, shopping_list_id):
        """Add an item to the shopping list."""
        # Prompt for item text
        item_text = simpledialog.askstring("New Item", "Enter item text:")
        if not item_text or not item_text.strip():
            return
        
        # Add item to database
        self.db.add_shopping_list_item(shopping_list_id, item_text.strip())
        
        # Reload shopping list
        self.load_shopping_list_detail(shopping_list_id)
    
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
            welcome_label = ctk.CTkLabel(
                self.shopping_view_frame, 
                text="Shopping Lists",
                font=("Arial", 20, "bold")
            )
            welcome_label.pack(pady=20)
            
            instruction_label = ctk.CTkLabel(
                self.shopping_view_frame,
                text="Select a shopping list from the left or create a new one.",
                font=("Arial", 14)
            )
            instruction_label.pack(pady=10)
            
            # Refresh shopping lists
            self.load_shopping_lists()
        else:
            messagebox.showerror("Error", "Failed to delete shopping list.")
    
    def export_all_recipes(self):
        """Export all recipes to a JSON file."""
        import json
        import tkinter.filedialog as filedialog
        
        # Get all recipes
        recipes = self.db.export_recipes_to_json()
        
        if not recipes:
            messagebox.showinfo("Export Recipes", "No recipes to export.")
            return
        
        # Ask user for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Recipes"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(recipes, f, indent=4)
            
            messagebox.showinfo("Export Successful", f"Successfully exported {len(recipes)} recipes to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting recipes: {str(e)}")

    def export_selected_recipes(self):
        """Export selected recipes to a JSON file."""
        import json
        import tkinter as tk
        
        # Create a dialog to select recipes
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Select Recipes to Export")
        dialog.geometry("400x500")
        dialog.minsize(400, 400)
        dialog.grab_set()  # Make dialog modal
        
        # Create frame for recipe list
        recipe_frame = ctk.CTkFrame(dialog)
        recipe_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create heading
        heading = ctk.CTkLabel(
            recipe_frame, 
            text="Select Recipes to Export", 
            font=("Arial", 16, "bold")
        )
        heading.pack(pady=10)
        
        # Create listbox with scrollbar
        list_frame = ctk.CTkFrame(recipe_frame)
        list_frame.pack(fill="both", expand=True, pady=5)
        
        # Note: We keep tk.Listbox for multi-select functionality
        recipe_listbox = tk.Listbox(list_frame, selectmode="multiple")
        recipe_scrollbar = ctk.CTkScrollbar(list_frame, command=recipe_listbox.yview)
        
        recipe_listbox.configure(yscrollcommand=recipe_scrollbar.set)
        
        recipe_listbox.pack(side="left", fill="both", expand=True)
        recipe_scrollbar.pack(side="right", fill="y")
        
        # Get all recipes
        recipes = self.db.get_all_recipes()
        
        # Populate listbox with recipes
        for recipe in recipes:
            recipe_listbox.insert("end", recipe["name"])
        
        # Store recipe IDs for later
        recipe_ids = [recipe["id"] for recipe in recipes]
        
        # Button frame
        btn_frame = ctk.CTkFrame(recipe_frame)
        btn_frame.pack(fill="x", pady=10)
        
        # Variable to store selected recipe IDs
        selected_recipe_ids = []
        
        # Function to handle recipe selection
        def export_selected():
            nonlocal selected_recipe_ids
            selected_indices = recipe_listbox.curselection()
            
            if not selected_indices:
                messagebox.showwarning("No Selection", "Please select at least one recipe.")
                return
            
            selected_recipe_ids = [recipe_ids[idx] for idx in selected_indices]
            dialog.destroy()
            
            # Continue with export process
            if selected_recipe_ids:
                # Ask user for file location
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    title="Export Selected Recipes"
                )
                
                if not file_path:
                    return  # User cancelled
                
                try:
                    # Export selected recipes
                    recipes_to_export = self.db.export_recipes_to_json(selected_recipe_ids)
                    
                    # Write to file
                    with open(file_path, 'w') as f:
                        json.dump(recipes_to_export, f, indent=4)
                    
                    messagebox.showinfo(
                        "Export Successful", 
                        f"Successfully exported {len(recipes_to_export)} recipes to {file_path}"
                    )
                except Exception as e:
                    messagebox.showerror("Export Error", f"Error exporting recipes: {str(e)}")
        
        # Export button
        export_btn = ctk.CTkButton(
            btn_frame, 
            text="Export Selected", 
            command=export_selected
        )
        export_btn.pack(side="left", padx=5)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            btn_frame, 
            text="Cancel", 
            command=dialog.destroy,
            fg_color="gray40",
            hover_color="gray30"
        )
        cancel_btn.pack(side="left", padx=5)
        
        # Wait for dialog to close
        dialog.wait_window()

    def setup_import_export_tab(self):
        """Set up the import/export tab."""
        # Create main container frame
        main_frame = ctk.CTkFrame(self.import_export_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create heading
        heading = ctk.CTkLabel(
            main_frame, 
            text="Import and Export Data", 
            font=("Arial", 20, "bold")
        )
        heading.pack(pady=10)
        
        # Create recipes section
        recipes_frame = ctk.CTkFrame(main_frame)
        recipes_frame.pack(fill="x", pady=10)
        
        recipes_label = ctk.CTkLabel(
            recipes_frame, 
            text="Recipes", 
            font=("Arial", 16, "bold")
        )
        recipes_label.pack(anchor="w", padx=10, pady=5)
        
        # Recipes export options
        recipe_export_frame = ctk.CTkFrame(recipes_frame)
        recipe_export_frame.pack(fill="x", pady=5, padx=10)
        
        export_recipe_label = ctk.CTkLabel(recipe_export_frame, text="Export Recipes:")
        export_recipe_label.pack(side="left", padx=5)
        
        # Export all recipes button
        export_all_recipes_btn = ctk.CTkButton(
            recipe_export_frame, 
            text="Export All Recipes", 
            command=self.export_all_recipes
        )
        export_all_recipes_btn.pack(side="left", padx=5)
        
        # Export selected recipes button
        export_selected_recipes_btn = ctk.CTkButton(
            recipe_export_frame, 
            text="Export Selected Recipes", 
            command=self.export_selected_recipes
        )
        export_selected_recipes_btn.pack(side="left", padx=5)
        
        # Recipes import options
        recipe_import_frame = ctk.CTkFrame(recipes_frame)
        recipe_import_frame.pack(fill="x", pady=5, padx=10)
        
        import_recipe_label = ctk.CTkLabel(recipe_import_frame, text="Import Recipes:")
        import_recipe_label.pack(side="left", padx=5)
        
        import_recipes_btn = ctk.CTkButton(
            recipe_import_frame, 
            text="Import Recipes from JSON", 
            command=self.import_recipes
        )
        import_recipes_btn.pack(side="left", padx=5)
        
        # Create shopping lists section
        lists_frame = ctk.CTkFrame(main_frame)
        lists_frame.pack(fill="x", pady=10)
        
        lists_label = ctk.CTkLabel(
            lists_frame, 
            text="Shopping Lists", 
            font=("Arial", 16, "bold")
        )
        lists_label.pack(anchor="w", padx=10, pady=5)
        
        # Shopping lists export options
        list_export_frame = ctk.CTkFrame(lists_frame)
        list_export_frame.pack(fill="x", pady=5, padx=10)
        
        export_list_label = ctk.CTkLabel(list_export_frame, text="Export Shopping Lists:")
        export_list_label.pack(side="left", padx=5)
        
        # Export all shopping lists button
        export_all_lists_btn = ctk.CTkButton(
            list_export_frame, 
            text="Export All Shopping Lists", 
            command=self.export_all_shopping_lists
        )
        export_all_lists_btn.pack(side="left", padx=5)
        
        # Export selected shopping lists button
        export_selected_lists_btn = ctk.CTkButton(
            list_export_frame, 
            text="Export Selected Shopping Lists", 
            command=self.export_selected_shopping_lists
        )
        export_selected_lists_btn.pack(side="left", padx=5)
        
        # Shopping lists import options
        list_import_frame = ctk.CTkFrame(lists_frame)
        list_import_frame.pack(fill="x", pady=5, padx=10)
        
        import_list_label = ctk.CTkLabel(list_import_frame, text="Import Shopping Lists:")
        import_list_label.pack(side="left", padx=5)
        
        import_lists_btn = ctk.CTkButton(
            list_import_frame, 
            text="Import Shopping Lists from JSON", 
            command=self.import_shopping_lists
        )
        import_lists_btn.pack(side="left", padx=5)
        
        # Information section
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", pady=10)
        
        info_label = ctk.CTkLabel(
            info_frame, 
            text="Information", 
            font=("Arial", 16, "bold")
        )
        info_label.pack(anchor="w", padx=10, pady=5)
        
        info_text = """
        JSON Import/Export allows you to:
        • Back up your recipes and shopping lists
        • Share recipes with friends
        • Import recipes from other sources
        
        Exported files are standard JSON format and can be edited with any text editor.
        """
        
        info_content = ctk.CTkLabel(
            info_frame, 
            text=info_text,
            justify="left", 
            wraplength=600,
            anchor="w"
        )
        info_content.pack(fill="x", padx=10, pady=5)

    def generate_from_recipes(self):
        """Generate a shopping list from recipes."""
        import tkinter as tk
        
        # Create recipe selection dialog using CTk
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Select Recipes")
        dialog.geometry("400x500")
        dialog.minsize(400, 400)
        dialog.grab_set()  # Make dialog modal
        
        # Create frame for recipe list
        recipe_frame = ctk.CTkFrame(dialog)
        recipe_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create heading
        heading = ctk.CTkLabel(
            recipe_frame, 
            text="Select Recipes for Shopping List", 
            font=("Arial", 16, "bold")
        )
        heading.pack(pady=10)
        
        # Create listbox with scrollbar
        list_frame = ctk.CTkFrame(recipe_frame)
        list_frame.pack(fill="both", expand=True, pady=5)
        
        # We'll use a normal tk Listbox for multi-selection capability
        recipe_listbox = tk.Listbox(list_frame, selectmode="multiple", height=15)
        recipe_scrollbar = ctk.CTkScrollbar(list_frame, command=recipe_listbox.yview)
        
        recipe_listbox.configure(yscrollcommand=recipe_scrollbar.set)
        
        recipe_listbox.pack(side="left", fill="both", expand=True)
        recipe_scrollbar.pack(side="right", fill="y")
        
        # Get all recipes
        recipes = self.db.get_all_recipes()
        
        # Populate listbox with recipes
        for recipe in recipes:
            recipe_listbox.insert("end", recipe["name"])
        
        # Store recipe IDs for later
        recipe_ids = [recipe["id"] for recipe in recipes]
        
        # Name field
        name_frame = ctk.CTkFrame(recipe_frame)
        name_frame.pack(fill="x", pady=5)
        
        name_label = ctk.CTkLabel(name_frame, text="Shopping List Name:")
        name_label.pack(side="left", padx=5)
        
        name_var = ctk.StringVar()
        name_var.set(f"Shopping List ({datetime.date.today().strftime('%Y-%m-%d')})")
        name_entry = ctk.CTkEntry(name_frame, textvariable=name_var, width=200)
        name_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Button frame
        btn_frame = ctk.CTkFrame(recipe_frame)
        btn_frame.pack(fill="x", pady=10)
        
        # Function to generate list and close dialog
        def create_list():
            selected_indices = recipe_listbox.curselection()
            
            if not selected_indices:
                messagebox.showwarning("No Selection", "Please select at least one recipe.")
                return
            
            selected_recipe_ids = [recipe_ids[idx] for idx in selected_indices]
            name = name_var.get().strip() or f"Shopping List ({datetime.date.today().strftime('%Y-%m-%d')})"
            
            shopping_list_id = self.db.generate_shopping_list_from_recipes(selected_recipe_ids, name)
            
            dialog.destroy()
            
            # Refresh lists and load the new one
            self.load_shopping_lists()
            self.load_shopping_list_detail(shopping_list_id)
        
        # Create generate button
        generate_btn = ctk.CTkButton(
            btn_frame, 
            text="Generate Shopping List", 
            command=create_list
        )
        generate_btn.pack(side="left", padx=5)
        
        # Create cancel button
        cancel_btn = ctk.CTkButton(
            btn_frame, 
            text="Cancel", 
            command=dialog.destroy,
            fg_color="gray40",
            hover_color="gray30"
        )
        cancel_btn.pack(side="left", padx=5)

    def export_all_shopping_lists(self):
        """Export all shopping lists to a JSON file."""
        import json
        import tkinter.filedialog as filedialog
        
        # Get all shopping lists
        shopping_lists = self.db.export_shopping_lists_to_json()
        
        if not shopping_lists:
            messagebox.showinfo("Export Shopping Lists", "No shopping lists to export.")
            return
        
        # Ask user for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Shopping Lists"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(shopping_lists, f, indent=4)
            
            messagebox.showinfo(
                "Export Successful", 
                f"Successfully exported {len(shopping_lists)} shopping lists to {file_path}"
            )
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting shopping lists: {str(e)}")

    def export_selected_shopping_lists(self):
        """Export selected shopping lists to a JSON file."""
        import json
        import tkinter as tk
        
        # Create a dialog to select shopping lists
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Select Shopping Lists to Export")
        dialog.geometry("400x500")
        dialog.minsize(400, 400)
        dialog.grab_set()  # Make dialog modal
        
        # Create frame for shopping list selection
        list_frame = ctk.CTkFrame(dialog)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create heading
        heading = ctk.CTkLabel(
            list_frame, 
            text="Select Shopping Lists to Export", 
            font=("Arial", 16, "bold")
        )
        heading.pack(pady=10)
        
        # Create listbox with scrollbar
        listbox_frame = ctk.CTkFrame(list_frame)
        listbox_frame.pack(fill="both", expand=True, pady=5)
        
        # Continue to use tk.Listbox for multi-selection
        list_listbox = tk.Listbox(listbox_frame, selectmode="multiple", height=15)
        list_scrollbar = ctk.CTkScrollbar(listbox_frame, command=list_listbox.yview)
        
        list_listbox.configure(yscrollcommand=list_scrollbar.set)
        
        list_listbox.pack(side="left", fill="both", expand=True)
        list_scrollbar.pack(side="right", fill="y")
        
        # Get all shopping lists
        shopping_lists = self.db.get_shopping_lists()
        
        # Populate listbox with shopping lists
        for shopping_list in shopping_lists:
            list_listbox.insert("end", shopping_list["name"])
        
        # Store shopping list IDs for later
        list_ids = [shopping_list["id"] for shopping_list in shopping_lists]
        
        # Button frame
        btn_frame = ctk.CTkFrame(list_frame)
        btn_frame.pack(fill="x", pady=10)
        
        # Variable to store selected shopping list IDs
        selected_list_ids = []
        
        # Function to handle shopping list selection
        def export_selected():
            nonlocal selected_list_ids
            selected_indices = list_listbox.curselection()
            
            if not selected_indices:
                messagebox.showwarning("No Selection", "Please select at least one shopping list.")
                return
            
            selected_list_ids = [list_ids[idx] for idx in selected_indices]
            dialog.destroy()
            
            # Continue with export process
            if selected_list_ids:
                # Ask user for file location
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    title="Export Selected Shopping Lists"
                )
                
                if not file_path:
                    return  # User cancelled
                
                try:
                    # Export selected shopping lists
                    lists_to_export = self.db.export_shopping_lists_to_json(selected_list_ids)
                    
                    # Write to file
                    with open(file_path, 'w') as f:
                        json.dump(lists_to_export, f, indent=4)
                    
                    messagebox.showinfo(
                        "Export Successful", 
                        f"Successfully exported {len(lists_to_export)} shopping lists to {file_path}"
                    )
                except Exception as e:
                    messagebox.showerror("Export Error", f"Error exporting shopping lists: {str(e)}")
        
        # Export button
        export_btn = ctk.CTkButton(
            btn_frame, 
            text="Export Selected", 
            command=export_selected
        )
        export_btn.pack(side="left", padx=5)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            btn_frame, 
            text="Cancel", 
            command=dialog.destroy,
            fg_color="gray40",
            hover_color="gray30"
        )
        cancel_btn.pack(side="left", padx=5)
        
        # Wait for dialog to close
        dialog.wait_window()

    def import_recipes(self):
        """Import recipes from a JSON file."""
        import json
        import tkinter.filedialog as filedialog
        
        # Ask user for file location
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Import Recipes"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Read from file
            with open(file_path, 'r') as f:
                recipes_data = json.load(f)
            
            # Validate data is a list
            if not isinstance(recipes_data, list):
                messagebox.showerror("Import Error", "Invalid JSON format. Expected a list of recipes.")
                return
            
            # Import recipes
            imported_count = 0
            for recipe_data in recipes_data:
                if self.db.import_recipe_from_json(recipe_data):
                    imported_count += 1
            
            messagebox.showinfo(
                "Import Successful", 
                f"Successfully imported {imported_count} of {len(recipes_data)} recipes."
            )
            
            # Refresh recipe list
            self.load_recipe_list()
            
        except json.JSONDecodeError:
            messagebox.showerror("Import Error", "Invalid JSON file. Could not parse file content.")
        except Exception as e:
            messagebox.showerror("Import Error", f"Error importing recipes: {str(e)}")

    def import_shopping_lists(self):
        """Import shopping lists from a JSON file."""
        import json
        import tkinter.filedialog as filedialog
        
        # Ask user for file location
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Import Shopping Lists"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Read from file
            with open(file_path, 'r') as f:
                lists_data = json.load(f)
            
            # Validate data is a list
            if not isinstance(lists_data, list):
                messagebox.showerror("Import Error", "Invalid JSON format. Expected a list of shopping lists.")
                return
            
            # Import shopping lists
            imported_count = 0
            for list_data in lists_data:
                if self.db.import_shopping_list_from_json(list_data):
                    imported_count += 1
            
            messagebox.showinfo(
                "Import Successful", 
                f"Successfully imported {imported_count} of {len(lists_data)} shopping lists."
            )
            
            # Refresh shopping list
            self.load_shopping_lists()
            
        except json.JSONDecodeError:
            messagebox.showerror("Import Error", "Invalid JSON file. Could not parse file content.")
        except Exception as e:
            messagebox.showerror("Import Error", f"Error importing shopping lists: {str(e)}")

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
    ctk.set_appearance_mode("System")  # Use system theme
    ctk.set_default_color_theme("blue")  # Blue theme
    
    root = ctk.CTk()  # Use CustomTkinter's root window
    app = RecipeApp(root)
    app.run()

if __name__ == "__main__":
    main()