import frappe
from frappe.utils import random_string


def on_call_log_created(doc, method):
    if doc.get("type") != "Incoming":
        return
    if doc.get("medium") != "3CX":
        return

    original_user = frappe.session.user
    frappe.set_user("Administrator")

    try:
        # تم إلغاء إنشاء HD Ticket هنا لمنع التكرار والإكتفاء بالتذكرة المنشأة من cx3_call

        # حفظ سجل المكالمة في TP Call Log فقط
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
        frappe.db.commit()

    except Exception:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Sabre Helpdesk: Call Log Error")
    finally:
        frappe.set_user(original_user)
