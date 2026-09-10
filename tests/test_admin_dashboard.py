def test_admin_dashboard_summary_and_activity(client, admin_auth_headers, auth_headers):
    # 1. Customer cannot access admin dashboard
    forbidden_res = client.get("/admin/dashboard/summary", headers=auth_headers)
    assert forbidden_res.status_code == 403

    # 2. Admin retrieves summary
    summary_res = client.get("/admin/dashboard/summary", headers=admin_auth_headers)
    assert summary_res.status_code == 200
    s_data = summary_res.json()["data"]
    assert "today_orders" in s_data
    assert "today_sales" in s_data
    assert "pending_payments" in s_data
    assert "pending_orders" in s_data
    assert "total_users" in s_data
    assert "pending_topups" in s_data
    assert s_data["total_users"] >= 1

    # 3. Admin retrieves recent activity
    act_res = client.get("/admin/dashboard/recent-activity", headers=admin_auth_headers)
    assert act_res.status_code == 200
    a_data = act_res.json()["data"]
    assert "recent_orders" in a_data
    assert "recent_payments" in a_data
