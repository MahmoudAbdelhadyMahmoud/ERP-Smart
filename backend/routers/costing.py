from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import datetime

import models, schemas
from database import get_db

router = APIRouter(
    prefix="/costing",
    tags=["costing"]
)

@router.get("/recipes", response_model=List[schemas.Recipe])
def read_recipes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    recipes = db.query(models.Recipe).offset(skip).limit(limit).all()
    return recipes

@router.post("/recipes", response_model=schemas.Recipe)
def create_recipe(recipe: schemas.RecipeCreate, db: Session = Depends(get_db)):
    db_recipe = models.Recipe(
        product_id=recipe.product_id,
        name=recipe.name,
        name_chinese=recipe.name_chinese,
        base_quantity=recipe.base_quantity,
        labor_cost=recipe.labor_cost,
        overhead_cost=recipe.overhead_cost,
        gas_cost=recipe.gas_cost,
        electricity_cost=recipe.electricity_cost,
        water_cost=recipe.water_cost,
        rent_cost=recipe.rent_cost,
        marketing_cost=recipe.marketing_cost,
        ad_cost=recipe.ad_cost,
        admin_cost=recipe.admin_cost,
        taxes=recipe.taxes,
        import_costs=recipe.import_costs,
        other_costs=recipe.other_costs,
        is_active=recipe.is_active,
        notes=recipe.notes
    )
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    
    for item in recipe.items:
        db_item = models.RecipeItem(
            recipe_id=db_recipe.id,
            material_product_id=item.material_product_id,
            quantity=item.quantity,
            waste_pct=item.waste_pct
        )
        db.add(db_item)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe

@router.get("/recipes/{recipe_id}", response_model=schemas.Recipe)
def read_recipe(recipe_id: int, db: Session = Depends(get_db)):
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if db_recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return db_recipe

@router.post("/recipes/{recipe_id}/produce")
def produce_recipe(recipe_id: int, quantity: float, db: Session = Depends(get_db)):
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if db_recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
        
    final_product = db.query(models.Product).filter(models.Product.id == db_recipe.product_id).first()
    if not final_product:
        raise HTTPException(status_code=404, detail="Final product not found")

    ratio = quantity / db_recipe.base_quantity
    
    total_material_cost = 0.0
    
    for item in db_recipe.items:
        material = db.query(models.Product).filter(models.Product.id == item.material_product_id).first()
        qty_needed = item.quantity * ratio
        qty_with_waste = qty_needed * (1 + item.waste_pct)
        
        mat_cost = qty_with_waste * material.average_cost
        total_material_cost += mat_cost
        
        material.current_stock -= qty_with_waste
        
        tx = models.CostTransaction(
            product_id=material.id,
            transaction_type="Production Out",
            quantity=-qty_with_waste,
            unit_cost=material.average_cost,
            total_cost=-mat_cost,
            reference_id=f"RECIPE-{recipe_id}"
        )
        db.add(tx)
        
    total_labor = db_recipe.labor_cost * ratio
    total_overhead = db_recipe.overhead_cost * ratio
    total_gas = (db_recipe.gas_cost or 0.0) * ratio
    total_elec = (db_recipe.electricity_cost or 0.0) * ratio
    total_water = (db_recipe.water_cost or 0.0) * ratio
    total_rent = (db_recipe.rent_cost or 0.0) * ratio
    total_marketing = (db_recipe.marketing_cost or 0.0) * ratio
    total_ad = (db_recipe.ad_cost or 0.0) * ratio
    total_admin = (db_recipe.admin_cost or 0.0) * ratio
    total_taxes = (db_recipe.taxes or 0.0) * ratio
    total_import = (db_recipe.import_costs or 0.0) * ratio
    total_other = (db_recipe.other_costs or 0.0) * ratio
    
    total_cost = (total_material_cost + total_labor + total_overhead + 
                  total_gas + total_elec + total_water + total_rent + 
                  total_marketing + total_ad + total_admin + 
                  total_taxes + total_import + total_other)
    
    unit_cost = total_cost / quantity if quantity > 0 else 0
    
    old_qty = final_product.current_stock
    old_avg = final_product.average_cost
    
    new_qty = old_qty + quantity
    if new_qty > 0:
        new_avg = ((old_qty * old_avg) + (quantity * unit_cost)) / new_qty
        final_product.average_cost = new_avg
        
    final_product.current_stock += quantity
    final_product.purchase_price = unit_cost
    
    tx_in = models.CostTransaction(
        product_id=final_product.id,
        transaction_type="Production In",
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=total_cost,
        reference_id=f"RECIPE-{recipe_id}"
    )
    db.add(tx_in)
    
    layer = models.CostLayer(
        product_id=final_product.id,
        original_qty=quantity,
        remaining_qty=quantity,
        unit_cost=unit_cost,
        source_doc=f"RECIPE-{recipe_id}"
    )
    db.add(layer)
    
    db.commit()
    
    return {"status": "success", "produced_quantity": quantity, "total_cost": total_cost, "unit_cost": unit_cost}

@router.put("/recipes/{recipe_id}", response_model=schemas.Recipe)
def update_recipe(recipe_id: int, recipe: schemas.RecipeCreate, db: Session = Depends(get_db)):
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Update main fields
    db_recipe.product_id = recipe.product_id
    db_recipe.name = recipe.name
    db_recipe.name_chinese = recipe.name_chinese
    db_recipe.base_quantity = recipe.base_quantity
    db_recipe.labor_cost = recipe.labor_cost
    db_recipe.overhead_cost = recipe.overhead_cost
    db_recipe.gas_cost = recipe.gas_cost
    db_recipe.electricity_cost = recipe.electricity_cost
    db_recipe.water_cost = recipe.water_cost
    db_recipe.rent_cost = recipe.rent_cost
    db_recipe.marketing_cost = recipe.marketing_cost
    db_recipe.ad_cost = recipe.ad_cost
    db_recipe.admin_cost = recipe.admin_cost
    db_recipe.taxes = recipe.taxes
    db_recipe.import_costs = recipe.import_costs
    db_recipe.other_costs = recipe.other_costs
    db_recipe.is_active = recipe.is_active
    db_recipe.notes = recipe.notes

    # Replace items
    db.query(models.RecipeItem).filter(models.RecipeItem.recipe_id == recipe_id).delete()
    
    for item in recipe.items:
        db_item = models.RecipeItem(
            recipe_id=db_recipe.id,
            material_product_id=item.material_product_id,
            quantity=item.quantity,
            waste_pct=item.waste_pct
        )
        db.add(db_item)
        
    db.commit()
    db.refresh(db_recipe)
    return db_recipe

@router.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Delete related items first
    db.query(models.RecipeItem).filter(models.RecipeItem.recipe_id == recipe_id).delete()
    db.delete(db_recipe)
    db.commit()
    return {"message": "Recipe deleted successfully"}
