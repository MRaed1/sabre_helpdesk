import frappe

score_map = {"Satisfied": 5, "Somehow Satisfied": 3, "Not Satisfied": 1}


def get_context(context):
    ticket_name = frappe.form_dict.get("ticket")
    context.no_cache = 1

    if not ticket_name or not frappe.db.exists("HD Ticket", ticket_name):
        context.error = "The ticket reference provided is invalid or does not exist."
        return

    if frappe.request.method == "POST":
        try:
            q1 = frappe.form_dict.get("q1")
            q2 = frappe.form_dict.get("q2")
            q3 = frappe.form_dict.get("q3")
            comments = frappe.form_dict.get("comments") or "No additional comments"

            s1, s2, s3 = score_map.get(q1, 3), score_map.get(q2, 3), score_map.get(q3, 3)
            avg_rating_5 = round((s1 + s2 + s3) / 3)
            rating_0_1 = avg_rating_5 / 5

            # اختيار أقرب Feedback Option بناءً على أقرب rating
            options = frappe.get_all("HD Ticket Feedback Option", fields=["name", "rating"])

            if not options:
                frappe.log_error(
                    title="Ticket Survey Error",
                    message="No HD Ticket Feedback Option records found."
                )
                context.error = "Survey configuration is incomplete. Please contact the administrator."
                return

            closest = min(options, key=lambda o: abs((o["rating"] or 0) - rating_0_1))

            formatted_feedback = "\n".join([
                f"1. Sabre System/Product: {q1}",
                f"2. Sabre Support: {q2}",
                f"3. Speed to Reach Support: {q3}",
                "",
                "Additional Comments:",
                comments,
            ])

            doc = frappe.get_doc("HD Ticket", ticket_name)
            doc.feedback_rating = rating_0_1
            doc.feedback = closest["name"]
            doc.feedback_extra = formatted_feedback
            doc.save(ignore_permissions=True)
            frappe.db.commit()

            context.submitted = True
            context.ticket_name = ticket_name
            return

        except Exception:
            frappe.db.rollback()
            frappe.log_error(title="Ticket Survey Submission Error", message=frappe.get_traceback())
            context.error = "An error occurred while submitting your feedback. Please try again later."
            return

    context.ticket_name = ticket_name
