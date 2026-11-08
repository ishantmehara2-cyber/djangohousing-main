from django.urls import path
from apps.engagements.views import (
    toggle_favorite_view,
    send_enquiry_view,
    verify_property_interest_otp_view,
    resend_property_interest_otp_view,
    api_express_property_interest_view,
    api_verify_property_interest_otp_view,
    schedule_visit_view,
    notifications_list_view,
    mark_notification_read_view,
    mark_all_notifications_read_view,
    buyer_enquiries_view,
    owner_enquiries_view,
    user_preferences_view,
    recently_viewed_view,
    clear_recently_viewed_view,
    saved_searches_view,
    save_current_search_view,
    delete_saved_search_view,
    smart_discover_dashboard_view
)
from apps.accounts.views import update_lead_status_view

app_name = 'engagements'

urlpatterns = [
    path('property/<slug:slug>/favorite/', toggle_favorite_view, name='toggle-favorite'),
    path('property/<slug:slug>/inquiry/', send_enquiry_view, name='send-inquiry'),
    path('property/<int:pk>/verify-interest-otp/', verify_property_interest_otp_view, name='verify-property-interest-otp'),
    path('property/<int:pk>/resend-interest-otp/', resend_property_interest_otp_view, name='resend-property-interest-otp'),

    # REST APIs for Property Interest
    path('api/properties/<int:pk>/express-interest/', api_express_property_interest_view, name='api-express-property-interest'),
    path('api/properties/<int:pk>/verify-interest-otp/', api_verify_property_interest_otp_view, name='api-verify-property-interest-otp'),

    path('property/<slug:slug>/visit/', schedule_visit_view, name='schedule-visit'),
    path('notifications/', notifications_list_view, name='notifications'),
    path('notifications/<int:pk>/read/', mark_notification_read_view, name='mark-notification-read'),
    path('notifications/read-all/', mark_all_notifications_read_view, name='mark-all-notifications-read'),
    path('dashboard/my-enquiries/', buyer_enquiries_view, name='buyer-enquiries'),
    path('dashboard/enquiries/', owner_enquiries_view, name='owner-enquiries'),
    path('dashboard/lead/<int:lead_id>/update/', update_lead_status_view, name='update-lead-status'),
    path('dashboard/preferences/', user_preferences_view, name='preferences'),
    path('dashboard/recently-viewed/', recently_viewed_view, name='recently-viewed'),
    path('dashboard/recently-viewed/clear/', clear_recently_viewed_view, name='clear-recently-viewed'),
    path('dashboard/saved-searches/', saved_searches_view, name='saved-searches'),
    path('dashboard/saved-searches/save/', save_current_search_view, name='save-search'),
    path('dashboard/saved-searches/<int:pk>/delete/', delete_saved_search_view, name='delete-saved-search'),
    path('dashboard/discover/', smart_discover_dashboard_view, name='smart-discover'),
]
