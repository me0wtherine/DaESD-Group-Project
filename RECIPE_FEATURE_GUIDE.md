# Recipe Feature Implementation Guide

## Overview
This document outlines the recipe feature implementation for producers to share recipes using their products with customers.

## Features Implemented

### 1. Recipe Model (`products/models.py`)
- **Recipe** model with the following fields:
  - `title`: Recipe name
  - `description`: Story and overview
  - `ingredients`: List of ingredients
  - `instructions`: Step-by-step cooking instructions
  - `image`: Recipe photo
  - `products`: ManyToMany link to producer's products
  - `season`: Seasonal tag (Spring, Summer, Autumn, Winter)
  - `prep_time_minutes`: Preparation time
  - `cook_time_minutes`: Cooking time
  - `serves`: Serving size
  - `is_published`: Visibility to customers
  - `created_at` / `updated_at`: Timestamps

### 2. Producer Dashboard Features (`producers/`)
- **Recipe Management Page** (`/producers/recipes/`)
  - List all recipes with creation date and product links
  - View publication status
  - Edit/Delete actions for each recipe

- **Add Recipe Form** (`/producers/recipes/add/`)
  - Fill in recipe details
  - Link to producer's own products
  - Upload recipe image
  - Set seasonal tags
  - Publish immediately or save as draft

- **Edit Recipe Page** (`/producers/recipes/<id>/edit/`)
  - Update all recipe details
  - Modify product links
  - Update image
  - Change publication status

### 3. Customer-Facing Features (`home/`)
- **Product Detail Page** (`/home/product/<id>/`)
  - New "Recipes Using [Product]" section
  - Recipe cards showing:
    - Recipe image
    - Title
    - Producer name
    - Seasonal tag
    - Prep/cook times and serving size
    - Brief description
    - "View Full Recipe" link
  - Full recipe details with:
    - Complete ingredients list
    - Step-by-step instructions
    - Related products (clickable links)
    - Producer information

## URL Routes

### Producer Routes (under `/producers/`)
```
/recipes/                          - List all recipes
/recipes/add/                      - Add new recipe
/recipes/<int:recipe_id>/edit/     - Edit recipe
/recipes/<int:recipe_id>/delete/   - Delete recipe
```

## Database Migration
Run these commands to apply the database changes:

```bash
python manage.py migrate
```

The migration file `0010_recipe.py` creates the Recipe table with all required fields and relationships.

## Forms

### RecipeForm (`producers/forms.py`)
- Handles recipe creation and editing
- Filters products to show only the logged-in producer's items
- Validates all required fields
- Supports image upload

## Views

### Producer Views (`producers/views.py`)
- `recipes_list()` - Display all recipes for the producer
- `add_recipe()` - Create new recipe
- `edit_recipe()` - Update existing recipe
- `delete_recipe()` - Remove recipe

### Home Views (`home/views.py`)
- `product_detail()` - Updated to include linked recipes

## Templates

### Producer Templates
1. **recipes_list.html** - Recipe management page with table
2. **add_recipe.html** - Form for creating recipes
3. **edit_recipe.html** - Form for editing recipes

### Customer Templates
- Product detail page updated with recipe section

## Styling
- Responsive grid layout for recipe cards
- Hover effects and transitions
- Color-coded status badges
- Ingredient list with checkmark icons
- Seasonal color indicators

## Usage Instructions

### For Producers
1. Navigate to "Recipes" in the producer dashboard
2. Click "Add New Recipe"
3. Fill in recipe details (title, description, ingredients, instructions)
4. Upload a recipe image (optional)
5. Link to products used in the recipe
6. Set cooking times and serving size
7. Optionally tag with season
8. Click "Create Recipe" to publish

### For Customers
1. Browse products in the shop
2. View product details
3. Scroll to "Recipes Using [Product]" section
4. View recipe cards with key information
5. Click "View Full Recipe" for complete details
6. See cooking instructions and linked products
7. Click product links to purchase

## Features & Benefits

✅ **Producers can share**
- Recipes featuring their products
- Storage and preparation guidance
- Farm stories through recipe context

✅ **Customers can**
- Discover recipe ideas using purchased products
- Learn how to prepare products
- Access complete cooking instructions
- Purchase linked ingredients

✅ **Educational Value**
- Strengthens producer-customer connection
- Supports local food education
- Seasonal recipe organization
- Combines product marketing with education

## Future Enhancements
- Recipe ratings/reviews from customers
- Favorite recipes bookmark feature
- Recipe search and filter
- Nutritional information
- Difficulty level ratings
- User-submitted recipes
- Recipe printing functionality
- Social media sharing buttons
