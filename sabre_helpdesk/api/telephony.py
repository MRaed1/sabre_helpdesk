import frappe
from frappe.utils import random_string


def on_call_log_created(doc, method):
    if doc.get("type") != "Incoming":
        return
    if doc.get("medium") != "3CX":
        return

    # الـ "customer" الجاي من الـ Call Log ممكن يكون اسم Contact/موظف
    # اتطابق برقم الهاتف مش سجل Customer حقيقي - نتأكد الأول عشان
    # ماتفشلش عملية إنشاء التذكرة بالكامل بسبب LinkValidationError
    customer = doc.get("customer")
    if customer and not frappe.db.exists("Customer", customer):
        customer = None

    try:
        ticket = frappe.get_doc({
            "doctype": "HD Ticket",
            "subject": f"Incoming call from {doc.get('from') or 'Unknown'}",
            "ticket_type": "Phone Call",
            "agent_group": "Sabre Frontline Helpdesk",
            "customer": customer,
        })
        ticket.insert(ignore_permissions=True)

        doc.append("links", {"link_doctype": "HD Ticket", "link_name": ticket.name})
        doc.save(ignore_permissions=True)

        tp_call = frappe.get_doc({
            "doctype": "TP Call Log",
            "id": doc.name or random_string(10),
            "from": doc.get("from"),
            "to": doc.get("to"),
            "type": doc.get("type"),
            "status": "Completed",
            "duration": doc.get("duration"),
            "medium": "3CX",
            "start_time": doc.get("start_time"),
            "end_time": doc.get("end_time"),
            "recording_url": doc.get("recording_url"),
        })
        tp_call.insert(ignore_permissions=True)

        tp_call.append("links", {"link_doctype": "HD Ticket", "link_name": ticket.name})
        tp_call.save(ignore_permissions=True)

        frappe.db.commit()

    except Exception:
        # لو أي خطوة فشلت (زي إنشاء TP Call Log بعد نجاح HD Ticket)،
        # نرجع الخطوات كلها عشان مانسيبش تذكرة بدون سجل مكالمة مرتبط بيها
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Sabre Helpdesk: Call to Ticket Error")
