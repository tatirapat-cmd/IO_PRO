import json
import os
import io
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Any, Set

ALLOWED_ROLES: Set[str] = {"admin", "staff", "customer"}

PRIMARY_FILE_PATH: str = os.path.join("data", "stock_data.json")
TMP_FILE_PATH: str = os.path.join("/tmp", "stock_data.json")

def get_writable_file_path() -> str:
    try:
        folder = os.path.dirname(PRIMARY_FILE_PATH)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        test_file = os.path.join(folder if folder else ".", ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return PRIMARY_FILE_PATH
    except Exception:
        return TMP_FILE_PATH

def load_data(file_path: str = None) -> Dict[str, Any]:
    target_path = file_path or get_writable_file_path()
    
    # กำหนดค่าเริ่มต้นให้เป็นห้องว่าง ไม่มีสินค้าตัวอย่างค้างอยู่
    default_structure = {
        "users": [
            {"username": "admin", "password": "123", "role": "admin", "name": "ผู้ดูแลระบบ"},
            {"username": "staff", "password": "123", "role": "staff", "name": "เจ้าหน้าที่คลัง"},
            {"username": "customer", "password": "123", "role": "customer", "name": "ลูกค้าทั่วไป"}
        ],
        "products": [],  # ตั้งให้เป็นค่าว่าง
        "stock_cards": [],
        "audit_logs": [],
        "purchase_orders": [],
        "supplier_pos": []
    }
    # ... (โค้ดที่เหลือคงเดิม)

def register_user(users: List[Dict[str, Any]], username: str, password: str, role: str, name: str) -> Tuple[bool, str]:
    try:
        if not username or not password or not name:
            return False, "กรุณากรอกข้อมูลให้ครบทุกช่อง"
            
        username = str(username).strip().lower()
        name = str(name).strip()
        role = str(role).strip().lower()

        if len(username) < 3:
            return False, "ชื่อผู้ใช้งานต้องมีความยาวอย่างน้อย 3 ตัวอักษร"
            
        if role not in ALLOWED_ROLES:
            return False, f"บทบาทผู้ใช้ต้องเป็นหนึ่งใน: {', '.join(ALLOWED_ROLES)}"
            
        for u in users:
            if u.get("username", "").lower() == username:
                return False, "ชื่อผู้ใช้งานนี้ถูกใช้งานแล้วในระบบ"
                
        users.append({
            "username": username,
            "password": str(password),
            "role": role,
            "name": name
        })
        return True, "สมัครสมาชิกสำเร็จ สามารถเข้าสู่ระบบได้ทันที"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการสมัครสมาชิก: {str(e)}"

def authenticate_user(users: List[Dict[str, Any]], username: str, password: str) -> Tuple[bool, str, Dict[str, Any]]:
    try:
        if not username or not password:
            return False, "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน", {}
            
        username = str(username).strip().lower()
        password = str(password)

        for u in users:
            if u.get("username", "").lower() == username and u.get("password") == password:
                user_info = {
                    "username": u.get("username"),
                    "role": u.get("role"),
                    "name": u.get("name")
                }
                return True, "เข้าสู่ระบบสำเร็จ", user_info
        return False, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", {}
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการเข้าสู่ระบบ: {str(e)}", {}

def validate_product_input(sku: str, name: str, cost_str: Any, price_str: Any, qty_str: Any, min_stock_str: Any = 5, company: str = "", category: str = "", unit: str = "", supplier: str = "", warehouse: str = "") -> Tuple[bool, str, Dict[str, Any]]:
    try:
        text_fields = {
            "SKU": sku,
            "ชื่อสินค้า": name,
            "บริษัท/ซัพพลายเออร์": company,
            "หมวดหมู่": category,
            "หน่วยนับ": unit,
            "ผู้จัดจำหน่าย": supplier,
            "คลังสินค้า": warehouse
        }

        for field_label, field_val in text_fields.items():
            if field_val and str(field_val).startswith(' '):
                return False, "โปรดใส่ชื่อให้ถูกต้อง", {}

        if not sku or not str(sku).strip():
            return False, "กรุณากรอกรหัส SKU สินค้า", {}
        if not name or not str(name).strip():
            return False, "กรุณากรอกชื่อสินค้า", {}

        sku_clean = str(sku).strip().upper()
        name_clean = str(name).strip()

        try:
            cost_price = float(cost_str)
            selling_price = float(price_str)
        except (ValueError, TypeError):
            return False, "ราคาทุนและราคาขายต้องเป็นตัวเลขที่ถูกต้องเท่านั้น", {}

        try:
            quantity = int(qty_str)
            min_stock = int(min_stock_str)
        except (ValueError, TypeError):
            return False, "จำนวนสินค้าและจุดสั่งซื้อต้องเป็นจำนวนเต็มเท่านั้น", {}

        if cost_price < 0.0 or selling_price < 0.0:
            return False, "ราคาทุนและราคาขายต้องไม่เป็นค่าติดลบ", {}

        if quantity < 0 or min_stock < 0:
            return False, "จำนวนสินค้าและจุดสั่งซื้อต้องไม่เป็นค่าติดลบ", {}

        validated_data = {
            "sku": sku_clean,
            "name": name_clean,
            "cost_price": round(cost_price, 2),
            "selling_price": round(selling_price, 2),
            "quantity": quantity,
            "min_stock": min_stock
        }
        return True, "ข้อมูลถูกต้อง", validated_data
    except Exception as e:
        return False, f"ตรวจสอบข้อมูลไม่ผ่าน: {str(e)}", {}

def generate_unique_id(items: List[Dict[str, Any]], prefix: str = "ORD") -> str:
    existing_ids = {i.get("id", i.get("order_id", i.get("po_id"))) for i in items if isinstance(i, dict)}
    counter = len(items) + 1
    new_id = f"{prefix}-{counter:03d}"

    while new_id in existing_ids:
        counter += 1
        new_id = f"{prefix}-{counter:03d}"

    return new_id

def process_stock_movement(products: List[Dict[str, Any]], stock_cards: List[Dict[str, Any]], sku: str, action_type: str, qty_change: int, reason: str, operator: str) -> Tuple[bool, str, Dict[str, Any]]:
    try:
        sku = str(sku).strip().upper()
        target_product = next((p for p in products if p.get("sku") == sku), None)

        if not target_product:
            return False, f"ไม่พบสินค้าที่มีรหัส SKU: {sku}", {}

        current_qty = int(target_product.get("quantity", 0))

        try:
            qty_change = int(qty_change)
        except (ValueError, TypeError):
            return False, "จำนวนการทำรายการต้องเป็นตัวเลขจำนวนเต็ม", {}

        if qty_change <= 0 and action_type in ["in", "out"]:
            return False, "จำนวนที่ทำรายการรับเข้า/เบิกออก ต้องมากกว่า 0", {}

        if action_type == "in":
            new_qty = current_qty + qty_change
            actual_change = qty_change
        elif action_type == "out":
            if qty_change > current_qty:
                return False, f"ไม่สามารถเบิกออกได้! ในคลังมีเพียง {current_qty} ชิ้น (ต้องการเบิก {qty_change} ชิ้น)", {}
            new_qty = current_qty - qty_change
            actual_change = -qty_change
        elif action_type == "adjust":
            if qty_change < 0:
                return False, "จำนวนสินค้าคงเหลือใหม่ต้องไม่ติดลบ", {}
            new_qty = qty_change
            actual_change = new_qty - current_qty
        else:
            return False, "ประเภทรายการปรับสต๊อกไม่ถูกต้อง", {}

        target_product["quantity"] = new_qty

        movement_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sku": sku,
            "product_name": target_product.get("name", ""),
            "action": action_type,
            "quantity_change": actual_change,
            "balance_after": new_qty,
            "reason": str(reason).strip() if reason else "ทำรายการปรับสต๊อก",
            "operator": str(operator).strip() if operator else "system"
        }

        stock_cards.insert(0, movement_entry)
        return True, f"ทำรายการ {action_type} สำเร็จ! ยอดคงเหลือใหม่คือ {new_qty} ชิ้น", movement_entry
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการปรับสต๊อก: {str(e)}", {}

def add_product(products: List[Dict[str, Any]], product_data: Dict[str, Any]) -> Tuple[bool, str]:
    try:
        sku = product_data.get("sku", "").strip().upper()
        if any(p.get("sku") == sku for p in products):
            return False, f"รหัส SKU '{sku}' มีในระบบแล้ว"

        new_prod = {
            "sku": sku,
            "name": str(product_data.get("name", "")).strip(),
            "company": str(product_data.get("company", "-")).strip() or "-",
            "category": str(product_data.get("category", "ทั่วไป")).strip() or "ทั่วไป",
            "unit": str(product_data.get("unit", "ชิ้น")).strip() or "ชิ้น",
            "cost_price": float(product_data.get("cost_price", 0.0)),
            "selling_price": float(product_data.get("selling_price", 0.0)),
            "quantity": int(product_data.get("quantity", 0)),
            "min_stock": int(product_data.get("min_stock", 5)),
            "supplier": str(product_data.get("supplier", product_data.get("company", "-"))).strip() or "-",
            "warehouse": str(product_data.get("warehouse", "คลังหลัก")).strip() or "คลังหลัก",
            "expiry_date": str(product_data.get("expiry_date", "")).strip()
        }
        products.append(new_prod)
        return True, f"เพิ่มสินค้า '{new_prod['name']}' (SKU: {sku}) เรียบร้อยแล้ว"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการเพิ่มสินค้า: {str(e)}"

def update_product(products: List[Dict[str, Any]], sku: str, update_data: Dict[str, Any]) -> Tuple[bool, str]:
    try:
        sku = str(sku).strip().upper()
        target_p = next((p for p in products if p.get("sku") == sku), None)

        if not target_p:
            return False, f"ไม่พบสินค้าที่มีรหัส SKU: {sku}"

        text_keys = ["name", "company", "category", "unit", "supplier", "warehouse"]
        for k in text_keys:
            if k in update_data and str(update_data[k]).startswith(' '):
                return False, "โปรดใส่ชื่อให้ถูกต้อง"

        if "name" in update_data:
            name_val = str(update_data["name"]).strip()
            if not name_val:
                return False, "กรุณากรอกชื่อสินค้า"
            target_p["name"] = name_val

        if "company" in update_data:
            target_p["company"] = str(update_data["company"]).strip() or "-"
        if "category" in update_data:
            target_p["category"] = str(update_data["category"]).strip() or "ทั่วไป"
        if "unit" in update_data:
            target_p["unit"] = str(update_data["unit"]).strip() or "ชิ้น"
        if "cost_price" in update_data:
            target_p["cost_price"] = float(update_data["cost_price"])
        if "selling_price" in update_data:
            target_p["selling_price"] = float(update_data["selling_price"])
        if "min_stock" in update_data:
            target_p["min_stock"] = int(update_data["min_stock"])
        if "supplier" in update_data:
            target_p["supplier"] = str(update_data["supplier"]).strip() or "-"
        if "warehouse" in update_data:
            target_p["warehouse"] = str(update_data["warehouse"]).strip() or "คลังหลัก"

        return True, f"อัปเดตข้อมูลสินค้า SKU {sku} สำเร็จ"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการอัปเดตสินค้า: {str(e)}"

def delete_product(products: List[Dict[str, Any]], sku: str) -> Tuple[bool, str]:
    try:
        sku = str(sku).strip().upper()
        for i, p in enumerate(products):
            if p.get("sku") == sku:
                del products[i]
                return True, f"ลบสินค้า SKU '{sku}' สำเร็จ"
        return False, f"ไม่พบสินค้าที่มีรหัส SKU: {sku}"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการลบสินค้า: {str(e)}"

def create_customer_order(orders: List[Dict[str, Any]], products: List[Dict[str, Any]], sku: str, qty: Any, cust_name: str) -> Tuple[bool, str, Dict[str, Any]]:
    try:
        sku = str(sku).strip().upper()
        target_p = next((p for p in products if p.get("sku") == sku), None)

        if not target_p:
            return False, f"ไม่พบสินค้า SKU '{sku}' ในระบบ", {}

        try:
            qty = int(qty)
        except (ValueError, TypeError):
            return False, "จำนวนที่สั่งซื้อต้องเป็นตัวเลขจำนวนเต็ม", {}

        if qty <= 0:
            return False, "จำนวนที่สั่งซื้อต้องมากกว่า 0", {}

        current_qty = int(target_p.get("quantity", 0))
        if qty > current_qty:
            return False, f"สินค้าในสต็อกไม่เพียงพอ! คงเหลือเพียง {current_qty} ชิ้น", {}

        order_id = generate_unique_id(orders, prefix="ORD")
        unit_price = float(target_p.get("selling_price", 0.0))

        new_order = {
            "order_id": order_id,
            "customer": str(cust_name).strip() or "Guest",
            "sku": sku,
            "product_name": target_p.get("name", ""),
            "quantity": qty,
            "total_price": round(unit_price * qty, 2),
            "status": "Pending",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        orders.insert(0, new_order)
        return True, f"สร้างคำสั่งซื้อ {order_id} เรียบร้อยแล้ว", new_order
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการสร้างคำสั่งซื้อ: {str(e)}", {}

def create_supplier_po(supplier_pos: List[Dict[str, Any]], products: List[Dict[str, Any]], supplier: str, sku: str, qty: Any) -> Tuple[bool, str, Dict[str, Any]]:
    try:
        sku = str(sku).strip().upper()
        target_p = next((p for p in products if p.get("sku") == sku), None)

        if not target_p:
            return False, f"ไม่พบสินค้า SKU '{sku}' ในระบบ", {}

        try:
            qty = int(qty)
        except (ValueError, TypeError):
            return False, "จำนวนสั่งซื้อต้องเป็นตัวเลขจำนวนเต็ม", {}

        if qty <= 0:
            return False, "จำนวนสั่งซื้อต้องมากกว่า 0", {}

        po_id = generate_unique_id(supplier_pos, prefix="PO")
        unit_cost = float(target_p.get("cost_price", 0.0))

        new_po = {
            "po_id": po_id,
            "supplier": str(supplier).strip() or target_p.get("supplier", "-"),
            "sku": sku,
            "product_name": target_p.get("name", ""),
            "quantity": qty,
            "total_cost": round(unit_cost * qty, 2),
            "status": "Ordered",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        supplier_pos.insert(0, new_po)
        return True, f"ออกใบสั่งซื้อ {po_id} ถึงผู้ขาย '{new_po['supplier']}' สำเร็จ", new_po
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการออกใบสั่งซื้อ PO: {str(e)}", {}

def receive_supplier_po(supplier_pos: List[Dict[str, Any]], products: List[Dict[str, Any]], stock_cards: List[Dict[str, Any]], po_id: str, operator: str) -> Tuple[bool, str]:
    try:
        po = next((p for p in supplier_pos if p.get("po_id") == po_id), None)
        if not po:
            return False, f"ไม่พบใบสั่งซื้อ {po_id}"

        if po.get("status") == "Received":
            return False, "ใบสั่งซื้อนี้รับสินค้าเข้าคลังไปแล้ว"

        sku = po.get("sku")
        qty = int(po.get("quantity", 0))

        success, msg, movement = process_stock_movement(
            products, stock_cards, sku=sku, action_type="in", qty_change=qty,
            reason=f"รับสินค้าเข้าคลังตามใบสั่งซื้อ {po_id}", operator=operator
        )

        if success:
            po["status"] = "Received"
            return True, f"รับสินค้าเข้าคลังตาม PO {po_id} จำนวน {qty} ชิ้น เรียบร้อยแล้ว"
        return False, msg
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการรับสินค้า PO: {str(e)}"

def approve_customer_order(products: List[Dict[str, Any]], stock_cards: List[Dict[str, Any]], order: Dict[str, Any], operator: str) -> Tuple[bool, str, Dict[str, Any]]:
    try:
        if order.get("status") != "Pending":
            return False, f"คำสั่งซื้อนี้อยู่ในสถานะ '{order.get('status')}' ไม่สามารถอนุมัติซ้ำได้", {}

        sku = order.get("sku")
        qty = int(order.get("quantity", 0))

        success, msg, movement = process_stock_movement(
            products, stock_cards, sku=sku, action_type="out", qty_change=qty,
            reason=f"อนุมัติคำสั่งซื้อ {order.get('order_id')}", operator=operator
        )

        if success:
            order["status"] = "Approved"
            return True, f"อนุมัติคำสั่งซื้อ {order.get('order_id')} สำเร็จและตัดสต็อกเรียบร้อยแล้ว", movement
        else:
            return False, msg, {}
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการอนุมัติคำสั่งซื้อ: {str(e)}", {}

def calculate_inventory_summary(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_sku = len(products)
    total_quantity = 0
    total_cost_value = 0.0
    total_sell_value = 0.0
    low_stock_count = 0
    
    category_summary: Dict[str, int] = {}
    company_summary: Dict[str, int] = {}
    product_summary: Dict[str, int] = {}

    for item in products:
        q = int(item.get("quantity", 0))
        c = float(item.get("cost_price", 0.0))
        s = float(item.get("selling_price", 0.0))
        min_s = int(item.get("min_stock", 5))
        cat = item.get("category", "ทั่วไป") or "ทั่วไป"
        comp = item.get("company", "ไม่ระบุ") or "ไม่ระบุ"
        name = item.get("name", item.get("sku", ""))

        total_quantity += q
        total_cost_value += (q * c)
        total_sell_value += (q * s)

        if q <= min_s:
            low_stock_count += 1

        category_summary[cat] = category_summary.get(cat, 0) + q
        company_summary[comp] = company_summary.get(comp, 0) + q
        product_summary[name] = product_summary.get(name, 0) + q

    return {
        "total_sku": total_sku,
        "total_quantity": total_quantity,
        "total_cost_value": round(total_cost_value, 2),
        "total_sell_value": round(total_sell_value, 2),
        "potential_profit": round(total_sell_value - total_cost_value, 2),
        "low_stock_count": low_stock_count,
        "category_summary": category_summary,
        "company_summary": company_summary,
        "product_summary": product_summary
    }

def filter_and_paginate(items: List[Dict[str, Any]], search_term: str = "", category: str = "", sort_by: str = "sku", page: int = 1, per_page: int = 5) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    try:
        filtered = []
        search_term = str(search_term).lower().strip()

        for item in items:
            sku_match = search_term in str(item.get("sku", "")).lower()
            name_match = search_term in str(item.get("name", "")).lower()
            company_match = search_term in str(item.get("company", "")).lower()
            supp_match = search_term in str(item.get("supplier", "")).lower()

            matches_search = not search_term or (sku_match or name_match or company_match or supp_match)
            matches_cat = not category or item.get("category") == category

            if matches_search and matches_cat:
                filtered.append(item)

        if sort_by == "price_asc":
            filtered.sort(key=lambda x: float(x.get("selling_price", 0)))
        elif sort_by == "price_desc":
            filtered.sort(key=lambda x: float(x.get("selling_price", 0)), reverse=True)
        elif sort_by == "qty_asc":
            filtered.sort(key=lambda x: int(x.get("quantity", 0)))
        elif sort_by == "qty_desc":
            filtered.sort(key=lambda x: int(x.get("quantity", 0)), reverse=True)
        else:
            filtered.sort(key=lambda x: str(x.get("sku", "")))

        try:
            page = max(1, int(page))
            per_page = max(1, min(int(per_page), 50))
        except (ValueError, TypeError):
            page = 1
            per_page = 5

        total_items = len(filtered)
        total_pages = max(1, (total_items + per_page - 1) // per_page)
        page = min(page, total_pages)

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        return filtered[start_idx:end_idx], {
            "current_page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages
        }
    except Exception:
        return [], {"current_page": 1, "per_page": 5, "total_items": 0, "total_pages": 1}

def add_audit_log(logs: List[Dict[str, Any]], username: str, role: str, action: str, details: str) -> List[Dict[str, Any]]:
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "username": str(username),
        "role": str(role),
        "action": str(action),
        "details": str(details)
    }
    logs.insert(0, log_entry)
    return logs

def export_products_to_excel(products: List[Dict[str, Any]]) -> io.BytesIO:
    df = pd.DataFrame(products)
    cols_order = ["sku", "name", "company", "category", "unit", "cost_price", "selling_price", "quantity", "min_stock", "supplier", "warehouse", "expiry_date"]
    present_cols = [c for c in cols_order if c in df.columns]
    df = df[present_cols]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Products")
    output.seek(0)
    return output

def clean_number(val, default=0.0):
    if pd.isna(val) or val is None or str(val).strip() == '':
        return default
    try:
        val_str = str(val).replace(',', '').replace('฿', '').replace('$', '').strip()
        return float(val_str)
    except Exception:
        return default

def import_products_from_excel(file_stream, existing_products: List[Dict[str, Any]]) -> Tuple[bool, str, int]:
    try:
        df = pd.read_excel(file_stream)
        clean_cols = [str(c).strip().lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_") for c in df.columns]
        df.columns = clean_cols

        column_mapping = {
            'sku': ['sku', 'รหัส', 'รหัสสินค้า', 'code', 'item_code', 'product_sku'],
            'name': ['name', 'ชื่อ', 'ชื่อสินค้า', 'รายการ', 'รายการสินค้า', 'product_name', 'item_name', 'title'],
            'company': ['company', 'บริษัท', 'ซัพพลายเออร์', 'ผู้ผลิต', 'แบรนด์', 'brand', 'supplier'],
            'category': ['category', 'หมวดหมู่', 'หมวด', 'กลุ่มสินค้า', 'cat'],
            'unit': ['unit', 'หน่วย', 'หน่วยนับ'],
            'cost_price': ['cost_price', 'cost', 'ต้นทุน', 'ราคาทุน', 'ราคาทุน_บาท', 'ราคาต้นทุน', 'costprice'],
            'selling_price': ['selling_price', 'price', 'unit_price', 'sell_price', 'ราคาขาย', 'ราคา', 'ราคาขาย_บาท', 'ราคา_หน่วย', 'sellingprice'],
            'quantity': ['quantity', 'stock_qty', 'stock_quantity', 'qty_stock', 'in_stock', 'qty', 'stock', 'จำนวน', 'สต็อก', 'จำนวนสินค้า', 'ปริมาณ', 'สต็อกคงเหลือ', 'คงเหลือ', 'จำนวนคงเหลือ'],
            'min_stock': ['min_stock', 'min', 'จุดสั่งซื้อ', 'ขั้นต่ำ', 'สต็อกขั้นต่ำ', 'min_qty'],
            'supplier': ['supplier', 'ผู้ขาย', 'ผู้จัดจำหน่าย'],
            'warehouse': ['warehouse', 'คลัง', 'คลังสินค้า'],
            'expiry_date': ['expiry_date', 'expiry', 'วันหมดอายุ']
        }

        actual_cols = {}
        for target_key, aliases in column_mapping.items():
            for alias in aliases:
                alias_clean = alias.lower().replace(" ", "_")
                if alias_clean in df.columns:
                    actual_cols[target_key] = alias_clean
                    break

        if 'quantity' not in actual_cols:
            for col in df.columns:
                if 'qty' in col or 'stock' in col or 'จำนวน' in col:
                    actual_cols['quantity'] = col
                    break

        if 'selling_price' not in actual_cols:
            for col in df.columns:
                if 'price' in col or 'ราคา' in col:
                    actual_cols['selling_price'] = col
                    break

        # ตรวจสอบความพร้อมของคอลัมน์ SKU และ Name อย่างปลอดภัย
        sku_key = actual_cols.get('sku')
        name_key = actual_cols.get('name')

        if not sku_key or not name_key or sku_key not in df.columns or name_key not in df.columns:
            return False, "ไฟล์ Excel ต้องมีคอลัมน์ 'sku' และ 'name' (หรือ รหัสสินค้า / ชื่อสินค้า)", 0

        imported_count = 0
        existing_skus = {p["sku"]: p for p in existing_products if isinstance(p, dict)}

        for _, row in df.iterrows():
            sku_val = row.get(sku_key, "")
            sku = str(sku_val).strip().upper() if pd.notna(sku_val) else ""
            if not sku or sku == "NAN" or sku == "NONE":
                continue

            name_val = row.get(name_key, "")
            name = str(name_val).strip() if pd.notna(name_val) else ""

            comp_col = actual_cols.get('company')
            company = str(row[comp_col]).strip() if comp_col and comp_col in df.columns and pd.notna(row[comp_col]) else "-"

            cat_col = actual_cols.get('category')
            category = str(row[cat_col]).strip() if cat_col and cat_col in df.columns and pd.notna(row[cat_col]) else "ทั่วไป"

            unit_col = actual_cols.get('unit')
            unit = str(row[unit_col]).strip() if unit_col and unit_col in df.columns and pd.notna(row[unit_col]) else "ชิ้น"

            price_col = actual_cols.get('selling_price')
            selling_price = clean_number(row[price_col], 0.0) if price_col and price_col in df.columns else 0.0

            cost_col = actual_cols.get('cost_price')
            cost_price = clean_number(row[cost_col], selling_price) if cost_col and cost_col in df.columns else selling_price

            qty_col = actual_cols.get('quantity')
            quantity = int(clean_number(row[qty_col], 0)) if qty_col and qty_col in df.columns else 0

            min_col = actual_cols.get('min_stock')
            min_stock = int(clean_number(row[min_col], 5)) if min_col and min_col in df.columns else 5

            supp_col = actual_cols.get('supplier')
            supplier = str(row[supp_col]).strip() if supp_col and supp_col in df.columns and pd.notna(row[supp_col]) else company

            wh_col = actual_cols.get('warehouse')
            warehouse = str(row[wh_col]).strip() if wh_col and wh_col in df.columns and pd.notna(row[wh_col]) else "คลังหลัก"

            exp_col = actual_cols.get('expiry_date')
            expiry_date = str(row[exp_col]).strip() if exp_col and exp_col in df.columns and pd.notna(row[exp_col]) else ""

            prod_data = {
                "sku": sku,
                "name": name,
                "company": company,
                "category": category,
                "unit": unit,
                "cost_price": float(cost_price),
                "selling_price": float(selling_price),
                "quantity": int(quantity),
                "min_stock": int(min_stock),
                "supplier": supplier,
                "warehouse": warehouse,
                "expiry_date": expiry_date
            }

            if sku in existing_skus:
                existing_skus[sku].update(prod_data)
            else:
                existing_products.append(prod_data)
                existing_skus[sku] = prod_data

            imported_count += 1

        return True, f"นำเข้าข้อมูลสินค้าสำเร็จจำนวน {imported_count} รายการ", imported_count
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการนำเข้าไฟล์ Excel: {str(e)}", 0
