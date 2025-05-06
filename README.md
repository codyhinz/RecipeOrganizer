# Recipe Organization System

A desktop application for managing recipes and shopping lists, designed to simplify meal planning and grocery shopping for home cooks.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Recipe Management](#recipe-management)
  - [Shopping Lists](#shopping-lists)
  - [Import/Export](#importexport)
- [JSON Format](#json-format)
- [Technical Details](#technical-details)
- [Future Enhancements](#future-enhancements)
- [Troubleshooting](#troubleshooting)
- [Credits](#credits)

## Overview

The Recipe Organization System is a Python desktop application that helps home cooks organize their recipes and streamline meal planning. The application addresses common challenges faced by home cooks, including scattered recipe storage, inefficient meal planning, and cumbersome grocery shopping.

## Features

### Recipe Management
- Store all recipes in one accessible location
- Categorize recipes by cuisine, course type, and more
- Mark favorite recipes for quick access
- Search recipes by name
- Filter recipes by category and favorite status
- Add, edit, and delete recipes with full details (ingredients, instructions)

### Shopping Lists
- Create multiple shopping lists
- Generate shopping lists automatically from selected recipes
- Add, edit, and delete shopping list items
- Mark items as checked while shopping
- Delete entire shopping lists

### Import/Export
- Export all or selected recipes to JSON format
- Export all or selected shopping lists to JSON format
- Import recipes from JSON files
- Import shopping lists from JSON files

## Installation

### Prerequisites
- Python 3.6 or higher
- Tkinter (usually included with Python)
- SQLite3 (included with Python)

### Steps
1. Clone or download the project files:
   ```
   git clone https://github.com/yourusername/recipe-organization-system.git
   ```
   Or download and extract the ZIP file

2. Navigate to the project directory:
   ```
   cd recipe-organization-system
   ```

3. Run the application:
   ```
   python recipeorganizer.py
   ```

The application will automatically create a database file (`recipe_system.db`) in the same directory during first run.

## Usage

### Recipe Management

#### Adding a New Recipe
1. In the Recipes tab, click "Add New Recipe"
2. Fill in the recipe details:
   - Recipe Name (required)
   - Categories (optional, select from list or add new)
   - Ingredients (add as many as needed)
   - Instructions (optional)
   - Favorite status (optional checkbox)
3. Click "Save Recipe"

#### Searching and Filtering Recipes
- Use the search box to search by recipe name
- Use the category dropdown to filter by category
- Check the "Favorites" checkbox to show only favorite recipes

#### Viewing and Editing Recipes
- Click on a recipe in the list to view its details
- Click "Edit" to modify the recipe
- Click "Delete" to remove the recipe
- Click "Add to Shopping List" to add the recipe's ingredients to a shopping list

### Shopping Lists

#### Creating a Shopping List
- Click "New Shopping List" and enter a name
- Or click "Generate from Recipes" to create a list from selected recipes

#### Managing Shopping Lists
- Click on a shopping list to view its items
- Click "Add Item" to add a new item
- Check the checkbox next to an item to mark it as complete
- Click "X" next to an item to delete it
- Click "Delete List" to remove the entire shopping list

### Import/Export

#### Exporting Recipes/Shopping Lists
1. Go to the Import/Export tab
2. Click "Export All Recipes" or "Export Selected Recipes"
3. Choose a location to save the JSON file
4. For selected recipes/lists, select the items you want to export

#### Importing Recipes/Shopping Lists
1. Go to the Import/Export tab
2. Click "Import Recipes from JSON" or "Import Shopping Lists from JSON"
3. Select the JSON file to import
4. The system will import the data and display a success message

## JSON Format

### Important Warning

**NEVER include `id` fields in your import JSON files!** 

Including `id` fields during import will cause the system to attempt to overwrite existing recipes or shopping lists with the same IDs, potentially leading to data loss.

### Recipe JSON Format

```json
[
  {
    "name": "Chocolate Chip Cookies",
    "instructions": "1. Preheat oven to 375°F.\n2. Mix ingredients...",
    "favorite": true,
    "categories": [
      "Dessert",
      "Baked Goods"
    ],
    "ingredients": [
      "2 1/4 cups all-purpose flour",
      "1 tsp baking soda",
      "1 tsp salt",
      "1 cup butter, softened",
      "3/4 cup sugar",
      "2 eggs",
      "2 cups chocolate chips"
    ]
  }
]
```

### Shopping List JSON Format

```json
[
  {
    "name": "Weekly Groceries",
    "items": [
      {
        "item_text": "Milk",
        "checked": false
      },
      {
        "item_text": "Eggs",
        "checked": true
      },
      {
        "item_text": "Bread",
        "checked": false
      }
    ]
  }
]
```

See the full [JSON Format Documentation](json-format-documentation.md) for details.

## Technical Details

### Architecture
- Two-tier architecture (Presentation Layer and Data Access Layer)
- Tkinter for the graphical user interface
- SQLite for data storage

### Database Schema
- recipes: Basic recipe information
- categories: Recipe categories
- recipe_categories: Many-to-many relationship between recipes and categories
- recipe_ingredients: Ingredients for each recipe
- shopping_lists: Shopping list metadata
- shopping_list_items: Items in shopping lists

### Class Structure
- RecipeDatabase: Handles all database operations
- RecipeApp: Manages the GUI and user interactions

## Future Enhancements

Planned future improvements include:
- Meal planning calendar
- Recipe import from websites
- Structured ingredient data (amount, unit, ingredient)
- Nutritional information calculation
- Mobile companion app

## Troubleshooting

### Common Issues
- **Database Errors**: If you encounter database errors, try deleting the `recipe_system.db` file and restarting the application
- **GUI Problems**: Ensure you have Tkinter installed correctly
- **Import Errors**: Verify your JSON format is correct and remove any `id` fields

### Performance Tips
- For large recipe collections, use categories and search to find recipes quickly
- Generate shopping lists from fewer recipes at a time for better performance

## Credits

Developed by Cody Hinz as part of a course project.

### Libraries Used
- Python: Programming language
- Tkinter: GUI framework
- SQLite: Database engine

---

For bug reports, feature requests, or contributions, please contact the developer or submit an issue on GitHub.