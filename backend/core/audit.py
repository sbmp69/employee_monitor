from core.database import supabase

def log_audit_action(admin_user, action: str, target_device_id: str = None, details: dict = None):
    try:
        admin_email = admin_user.user.email if hasattr(admin_user, "user") else "Unknown"
        supabase.table("audit_logs").insert({
            "action": action,
            "admin_email": admin_email,
            "target_device_id": target_device_id,
            "details": details or {}
        }).execute()
    except Exception as e:
        print(f"Failed to write audit log: {e}")
