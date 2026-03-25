import pandas as pd
import os
import pickle
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from deep_translator import GoogleTranslator
from sqlalchemy import func
import models
from datetime import date

# Arabic support
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register fonts that support Arabic and Chinese
ARIAL_FONT_PATH = "C:\\Windows\\Fonts\\arial.ttf"
MSYH_FONT_PATH = "C:\\Windows\\Fonts\\msyh.ttc" # Microsoft YaHei supports Chinese

try:
    pdfmetrics.registerFont(TTFont('ArialAr', ARIAL_FONT_PATH))
    # For TTC files, we might need to specify index, but standard registerFont often handles it or we use TTF
    pdfmetrics.registerFont(TTFont('MSYaHei', MSYH_FONT_PATH))
    ARABIC_FONT = 'ArialAr'
    CHINESE_FONT = 'MSYaHei'
    MAIN_FONT = 'MSYaHei' # Use YaHei as main since it supports many charsets
except:
    ARABIC_FONT = 'Helvetica'
    CHINESE_FONT = 'Helvetica'
    MAIN_FONT = 'Helvetica'

import re

def fix_pdf_text(text):
    if not text:
        return ""
    text_str = str(text)
    
    # Regex to find Arabic sequences (including spaces between Arabic words)
    # Range covers basic Arabic, supplement, reshaped forms, etc.
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+(?:[\s]+[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+)*)')
    
    parts = []
    last_end = 0
    
    for match in arabic_pattern.finditer(text_str):
        # Non-Arabic part before this match (could be Chinese, English, symbols)
        non_arb = text_str[last_end:match.start()]
        if non_arb:
            # Escape XML special characters for Paragraph
            escaped = non_arb.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            parts.append(f'<font name="MSYaHei">{escaped}</font>')
            
        # Arabic part
        arb = match.group(1)
        try:
            reshaped = arabic_reshaper.reshape(arb)
            visual = get_display(reshaped)
            # Escape XML special characters
            escaped_arb = visual.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            parts.append(f'<font name="ArialAr">{escaped_arb}</font>')
        except:
            parts.append(arb)
            
        last_end = match.end()
        
    # Remaining part
    remaining = text_str[last_end:]
    if remaining:
        escaped_rem = remaining.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        parts.append(f'<font name="MSYaHei">{escaped_rem}</font>')
        
    if not parts:
        return text_str
        
    return "".join(parts)

def fix_arabic(text):
    return fix_pdf_text(text)

# Model path for AI recommender
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expense_model.pkl")

def translate_to_chinese(text):
    if not text:
        return ""
    try:
        translated = GoogleTranslator(source='auto', target='zh-CN').translate(text)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def translate_to_english(text):
    if not text:
        return ""
    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text


def generate_excel(expenses):
    rows = []
    for idx, e in enumerate(expenses, 1):
        if not e.items:
            rows.append({
                "Seq ID": idx,
                "Date": e.date,
                "Invoice No": e.invoice_number or f"EXP-{e.id}",
                "Type (AR)": "N/A",
                "Type (CH)": "N/A",
                "Description (AR)": "N/A",
                "Description (CH)": "N/A",
                "Quantity": 0,
                "Unit Price": 0,
                "Item Total": 0,
                "Invoice Subtotal": e.amount_egp,
                "Taxes": e.taxes,
                "Discount (%)": e.discount_pct,
                "Grand Total": e.total,
                "Cost Center": e.cost_center.name if e.cost_center else "N/A",
                "Notes": e.notes
            })
        else:
            for item in e.items:
                rows.append({
                    "Seq ID": idx,
                    "Date": e.date,
                    "Invoice No": e.invoice_number or f"EXP-{e.id}",
                    "Type (AR)": item.type_rel.name if item.type_rel else "N/A",
                    "Type (CH)": item.type_rel.name_chinese if item.type_rel else "N/A",
                    "Description (AR)": item.description or "N/A",
                    "Description (CH)": item.description_chinese or "N/A",
                    "Quantity": item.quantity,
                    "Unit Price": item.unit_price,
                    "Item Total": item.amount,
                    "Invoice Subtotal": e.amount_egp,
                    "Taxes": e.taxes,
                    "Discount (%)": e.discount_pct,
                    "Grand Total": e.total,
                    "Cost Center": e.cost_center.name if e.cost_center else "N/A",
                    "Notes": e.notes
                })
    
    df = pd.DataFrame(rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Expenses')
    return output.getvalue()

def generate_pdf(expenses):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    styles = getSampleStyleSheet()
    # Update style to use Chinese font
    styles['Title'].fontName = MAIN_FONT
    styles['Heading2'].fontName = MAIN_FONT
    elements = []
    
    # Title - fix Arabic/Chinese if any
    title_text = fix_pdf_text("تقرير المصروفات التفصيلي (Detailed Expenses Report / 详细费用报告)")
    elements.append(Paragraph(title_text, styles['Title']))
    
    # Custom style for table cells to handle Paragraphs
    cell_style = styles['Normal'].clone('cell_style')
    cell_style.alignment = 1 # Center
    cell_style.fontName = MAIN_FONT # Microsoft YaHei handles Latin, Chinese, and many others
    
    # Table Header - fix Arabic/Chinese
    headers = ["Seq ID", "التاريخ (Date)", "الرقم (No)", "النوع (AR)", "النوع (CH)", "الوصف (AR)", "الوصف (CH)", "الكمية (Qty)", "السعر (Price)", "المبلغ (Amount)"]
    fixed_headers = [Paragraph(fix_pdf_text(h), cell_style) for h in headers]
    data = [fixed_headers]

    for idx, e in enumerate(expenses, 1):
        invoice_no = e.invoice_number or f"EXP-{e.id}"
        if not e.items:
            data.append([
                Paragraph(str(idx), cell_style),
                Paragraph(str(e.date), cell_style),
                Paragraph(str(invoice_no), cell_style),
                Paragraph("N/A", cell_style),
                Paragraph("N/A", cell_style),
                Paragraph("N/A", cell_style),
                Paragraph("N/A", cell_style),
                Paragraph("0", cell_style),
                Paragraph("0", cell_style),
                Paragraph("0", cell_style)
            ])
        else:
            for item in e.items:
                # Use separate columns for Arabic and Chinese descriptions
                data.append([
                    Paragraph(str(idx), cell_style),
                    Paragraph(str(e.date), cell_style),
                Paragraph(str(invoice_no), cell_style),
                Paragraph(fix_pdf_text(item.type_rel.name if item.type_rel else "N/A"), cell_style),
                Paragraph(fix_pdf_text(item.type_rel.name_chinese if item.type_rel else "N/A"), cell_style),
                Paragraph(fix_pdf_text(item.description or ""), cell_style),
                Paragraph(fix_pdf_text(item.description_chinese or ""), cell_style),
                Paragraph(f"{item.quantity}", cell_style),
                Paragraph(f"{item.unit_price:.2f}", cell_style),
                Paragraph(f"{item.amount:.2f}", cell_style)
                ])
    
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
    ]))
    elements.append(t)
    
    # Add Space
    from reportlab.platypus import Spacer
    elements.append(Spacer(1, 20))
    
    # Summary Totals (only if exporting a single invoice, or as a general summary)
    if len(expenses) == 1:
        e = expenses[0]
        # Use Paragraphs for labels to ensure font rendering
        summary_data = [
            [Paragraph(fix_pdf_text("المجموع الفرعي (Subtotal / 小计):"), cell_style), Paragraph(f"{e.amount_egp:.2f}", cell_style)],
            [Paragraph(fix_pdf_text("الضرائب (Taxes / 税费):"), cell_style), Paragraph(f"{e.taxes:.2f}", cell_style)],
            [Paragraph(fix_pdf_text("الخصم (Discount / 折扣 %):"), cell_style), Paragraph(f"{e.discount_pct:.1f}%", cell_style)],
            [Paragraph(fix_pdf_text("الإجمالي النهائي (Grand Total / 总计):"), cell_style), Paragraph(f"{e.total:.2f}", cell_style)]
        ]
        
        st = Table(summary_data, colWidths=[250, 100])
        st.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0, colors.white), # Invisible grid
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ]))
        elements.append(st)
    else:
        # General total for all expenses if multiple
        total_sum = sum(exp.total for exp in expenses)
        total_text = fix_pdf_text(f"إجمالي كافة الفواتير (Grand Total / 所有发票总计): {total_sum:.2f}")
        elements.append(Paragraph(total_text, styles['Heading2']))

    doc.build(elements)
    return output.getvalue()

def train_recommender(expenses):
    if len(expenses) < 5:  # Not enough data to train
        return None
    
    X = []
    y = []
    for e in expenses:
        if e.items:
            # Use expense notes and first item's type for training
            X.append(e.notes or "")
            y.append(e.items[0].expense_type)
    
    if not X:
        return None
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer()),
        ('clf', MultinomialNB())
    ])
    pipeline.fit(X, y)
    
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    return pipeline

def predict_type(notes):
    if not os.path.exists(MODEL_PATH):
        return None
    
    with open(MODEL_PATH, "rb") as f:
        pipeline = pickle.load(f)
    
    prediction = pipeline.predict([notes])
    return prediction[0] if prediction else None

from typing import Optional

def generate_doc_number(db, movement_date: Optional[date] = None) -> str:
    """Generates a unique sequential document number: WH-YYYYMMDD-XXXX"""
    today = movement_date or date.today()
    prefix = f"WH-{today.strftime('%Y%m%d')}"
    
    # Find the highest sequence number for today
    last = db.query(models.WarehouseMovement).filter(
        models.WarehouseMovement.doc_number.like(f"{prefix}-%")
    ).order_by(models.WarehouseMovement.doc_number.desc()).first()
    
    if last and last.doc_number:
        try:
            seq = int(last.doc_number.split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}-{seq:04d}"

def generate_invoice_number(db, expense_date: Optional[date] = None) -> str:
    """Generates a unique sequential invoice number: EXP-YYYYMMDD-XXXX"""
    today = expense_date or date.today()
    prefix = f"EXP-{today.strftime('%Y%m%d')}"
    
    # Find the highest sequence number for today
    last = db.query(models.Expense).filter(
        models.Expense.invoice_number.like(f"{prefix}-%")
    ).order_by(models.Expense.invoice_number.desc()).first()
    
    if last and last.invoice_number:
        try:
            seq = int(last.invoice_number.split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}-{seq:04d}"

def generate_warehouse_excel(products):
    rows = []
    for p in products:
        rows.append({
            "Code": p.code or f"#{p.id}",
            "Name (AR)": p.name,
            "Name (CH)": p.name_chinese or "N/A",
            "Unit": p.unit or "N/A",
            "Stock": p.current_stock,
            "Avg Cost": p.average_cost,
            "Last Purchase Price": p.purchase_price,
            "Reorder Level": p.reorder_level,
            "Total Value": p.current_stock * p.average_cost
        })
    df = pd.DataFrame(rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventory')
    return output.getvalue()

def generate_warehouse_pdf(products):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    styles = getSampleStyleSheet()
    styles['Title'].fontName = MAIN_FONT
    elements = []
    
    title_text = fix_pdf_text("تقرير حالة المخزون (Inventory Status Report / 库存状态报告)")
    elements.append(Paragraph(title_text, styles['Title']))
    
    cell_style = styles['Normal'].clone('cell_style')
    cell_style.alignment = 1
    cell_style.fontName = MAIN_FONT
    cell_style.fontSize = 8
    
    headers = ["Code", "Name (AR)", "Name (CH)", "Unit", "Stock", "Avg Cost", "Value"]
    fixed_headers = [Paragraph(fix_pdf_text(h), cell_style) for h in headers]
    data = [fixed_headers]

    for p in products:
        data.append([
            Paragraph(p.code or f"#{p.id}", cell_style),
            Paragraph(fix_pdf_text(p.name), cell_style),
            Paragraph(fix_pdf_text(p.name_chinese or ""), cell_style),
            Paragraph(fix_pdf_text(p.unit or ""), cell_style),
            Paragraph(f"{p.current_stock}", cell_style),
            Paragraph(f"{p.average_cost:.2f}", cell_style),
            Paragraph(f"{p.current_stock * p.average_cost:.2f}", cell_style)
        ])
    
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.indigo),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(t)
    
    total_val = sum(p.current_stock * p.average_cost for p in products)
    elements.append(Paragraph(fix_pdf_text(f"إجمالي قيمة المخزون (Total Inventory Value): {total_val:.2f}"), styles['Heading2']))
    
    doc.build(elements)
    return output.getvalue()

def get_product_template():
    df = pd.DataFrame(columns=["Code", "Name", "Name (CH)", "Unit", "Reorder Level", "Initial Stock", "Initial Price", "Notes"])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    return output.getvalue()

def get_expense_template():
    columns = ["Date", "Invoice No", "Cost Center", "Type (AR)", "Product Code (optional)", "Description (AR)", "Quantity", "Unit Price", "Tax", "Discount", "Notes"]
    df = pd.DataFrame(columns=columns)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    return output.getvalue()

def import_products_from_excel(file_content, db):
    df = pd.read_excel(BytesIO(file_content))
    imported_count = 0
    # Get a default location for initial movements
    loc = db.query(models.Location).first()
    loc_id = loc.id if loc else 1

    for _, row in df.iterrows():
        name = str(row.get("Name", "")).strip()
        if not name or name == "nan": continue
        
        code = str(row.get("Code", "")) if row.get("Code") and str(row.get("Code")) != "nan" else None
        
        existing = None
        if code:
            existing = db.query(models.Product).filter(models.Product.code == code).first()
        if not existing:
            existing = db.query(models.Product).filter(models.Product.name == name).first()
            
        # Correctly check for presence of columns
        initial_stock = float(row["Initial Stock"]) if "Initial Stock" in row and pd.notnull(row["Initial Stock"]) else 0
        initial_price = float(row["Initial Price"]) if "Initial Price" in row and pd.notnull(row["Initial Price"]) else 0

        if existing:
            if "Name (CH)" in row and pd.notnull(row["Name (CH)"]): existing.name_chinese = row["Name (CH)"]
            if "Unit" in row and pd.notnull(row["Unit"]): existing.unit = row["Unit"]
            if "Reorder Level" in row and pd.notnull(row["Reorder Level"]): existing.reorder_level = float(row["Reorder Level"])
            if "Notes" in row and pd.notnull(row["Notes"]): existing.notes = str(row["Notes"])
            if code: existing.code = code
            
            # --- FORCE UPDATE PRICE ---
            if initial_price > 0:
                existing.purchase_price = initial_price
                existing.average_cost = initial_price # Always adopt latest update as requested

            # --- UPDATE STOCK VIA ADJUSTMENT ---
            # If initial stock is provided, we treat it as an adjustment to the specified value
            # This ensures recalculate_stock picks it up
            if "Initial Stock" in row and pd.notnull(row["Initial Stock"]):
                movement = models.WarehouseMovement(
                    product_id=existing.id,
                    location_id=loc_id,
                    type="Adjustment",
                    quantity=initial_stock,
                    unit_price=initial_price if initial_price > 0 else existing.average_cost,
                    date=date.today(),
                    notes="تحديث رصيد عبر استيراد الإكسل"
                )
                db.add(movement)
                existing.current_stock = initial_stock
        else:
            new_p = models.Product(
                name=name,
                name_chinese=row["Name (CH)"] if "Name (CH)" in row and pd.notnull(row["Name (CH)"]) else None,
                unit=str(row["Unit"]) if "Unit" in row and pd.notnull(row["Unit"]) else "واحد",
                reorder_level=float(row["Reorder Level"]) if "Reorder Level" in row and pd.notnull(row["Reorder Level"]) else 0,
                notes=str(row["Notes"]) if "Notes" in row and pd.notnull(row["Notes"]) else "",
                code=code,
                current_stock=initial_stock,
                average_cost=initial_price,
                purchase_price=initial_price
            )
            db.add(new_p)
            db.flush()

            if initial_stock > 0:
                movement = models.WarehouseMovement(
                    product_id=new_p.id,
                    location_id=loc_id,
                    type="رصيد افتتاحي",
                    quantity=initial_stock,
                    unit_price=initial_price,
                    date=date.today(),
                    notes="مستورد من شيت الإكسل"
                )
                db.add(movement)

        imported_count += 1
    db.commit()
    return imported_count

def import_expenses_from_excel(file_content, db):
    df = pd.read_excel(BytesIO(file_content))
    # Pre-fetch caches for speed
    cost_centers = {cc.name: cc.id for cc in db.query(models.CostCenter).all()}
    expense_types = {et.name: et.id for et in db.query(models.ExpenseType).all()}
    products = {p.code: p.id for p in db.query(models.Product).filter(models.Product.code != None).all()}
    
    # Fill nan in Invoice No to avoid groups issues
    df['Invoice No'] = df['Invoice No'].fillna('TEMP-' + pd.Timestamp.now().strftime('%Y%m%d%H%M%S'))
    # Ensure Date is valid
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    imported_count = 0
    for (exp_date, inv_no), group in df.groupby(['Date', 'Invoice No']):
        # Find or create cost center
        cc_name = str(group.iloc[0].get("Cost Center", "Default")).strip()
        if cc_name not in cost_centers:
            new_cc = models.CostCenter(name=cc_name)
            db.add(new_cc)
            db.flush()
            cost_centers[cc_name] = new_cc.id
        
        cc_id = cost_centers[cc_name]
        
        # Create Expense
        db_expense = models.Expense(
            date=exp_date,
            invoice_number=inv_no if not str(inv_no).startswith('TEMP-') else None,
            cost_center_id=cc_id,
            amount_egp=0, 
            taxes=0,
            discount_pct=0,
            total=0,
            notes=str(group.iloc[0].get("Notes", "")) if str(group.iloc[0].get("Notes", "")) != "nan" else ""
        )
        db.add(db_expense)
        db.flush()
        
        total_amount = 0
        for _, row in group.iterrows():
            et_name = str(row.get("Type (AR)", "General")).strip()
            if et_name not in expense_types:
                new_et = models.ExpenseType(name=et_name)
                new_et.name_chinese = translate_to_chinese(et_name)
                db.add(new_et)
                db.flush()
                expense_types[et_name] = new_et.id
            
            et_id = expense_types[et_name]
            
            prod_code = str(row.get("Product Code (optional)", "")).strip()
            prod_id = products.get(prod_code) if prod_code and prod_code != "nan" else None
            
            qty = float(row.get("Quantity", 1))
            price = float(row.get("Unit Price", 0))
            tax = float(row.get("Tax", 0))
            discount = float(row.get("Discount", 0))
            amount = (qty * price) + tax - discount
            
            desc = str(row.get("Description (AR)", ""))
            if desc == "nan": desc = ""
            
            item = models.ExpenseItem(
                expense_id=db_expense.id,
                expense_type_id=et_id,
                product_id=prod_id,
                description=desc,
                description_chinese=translate_to_chinese(desc) if desc else None,
                quantity=qty,
                unit_price=price,
                tax=tax,
                discount=discount,
                amount=amount
            )
            db.add(item)
            total_amount += amount
            
            if prod_id:
                # Assuming first location as target for simplicity or add a Location column?
                # For now let's assume Addition to main warehouse (id=1 or first found)
                loc = db.query(models.Location).first()
                loc_id = loc.id if loc else 1
                movement = models.WarehouseMovement(
                    product_id=prod_id,
                    location_id=loc_id,
                    type="Addition",
                    quantity=qty,
                    unit_price=price,
                    date=exp_date,
                    notes=f"Imported EXP: {inv_no}",
                    expense_id=db_expense.id,
                    doc_number=inv_no if not str(inv_no).startswith('TEMP-') else f"IMP-{db_expense.id}"
                )
                db.add(movement)
        
        db_expense.amount_egp = total_amount
        db_expense.total = total_amount
        imported_count += 1
        
    db.commit()
    return imported_count
